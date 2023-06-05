#!/usr/bin/env python

# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import os
import sys
import json
from functools import lru_cache

# Importing pyspark libraries
from pyspark.ml.pipeline import PipelineModel
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

"""
   Inference script. This script is used for prediction by scoring server when schema is known.
"""

model_name = "model"
spark_input_schema = model_name + "_input_data_schema.json"

spark = SparkSession.builder.appName("Spark Model Inference").getOrCreate()


@lru_cache(maxsize=10)
def load_model(model_file_name=model_name):
    """
    Loads model from the serialized format

    Returns
    -------
    model:  a model instance on which predict API can be invoked
    """
    model_dir = os.path.dirname(os.path.realpath(__file__))
    if model_dir not in sys.path:
        sys.path.insert(0, model_dir)
    contents = os.listdir(model_dir)
    try:
        print(f"Start loading {model_file_name} from model directory {model_dir} ...")
        loaded_model = PipelineModel.load(os.path.join(model_dir, model_file_name))
        print("Model is successfully loaded.")
        return loaded_model
    except Exception as e:
        error_msg = f"Failed to load the model and gave the exception: {e}."
        raise Exception(error_msg)


@lru_cache(maxsize=1)
def fetch_data_type_from_schema(
    input_schema_path=os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "input_schema.json"
    )
):
    """
    Returns data type information fetch from input_schema.json.

    Parameters
    ----------
    input_schema_path: path of input schema.

    Returns
    -------
    data_type: data type fetch from input_schema.json.

    """
    data_type = {}
    if os.path.exists(input_schema_path):
        schema = json.load(open(input_schema_path))
        for col in schema["schema"]:
            data_type[col["name"]] = col["dtype"]
    else:
        print(
            "input_schema has to be passed in in order to recover the same data type. pass `X_sample` in `ads.model.framework.spark_model.SparkPipelineModel.prepare` function to generate the input_schema. Otherwise, the data type might be changed after serialization/deserialization."
        )
    return data_type


def deserialize(data, input_schema_path):
    """
    Deserialize json serialization data to data in original type when sent to predict.

    Parameters
    ----------
    data: serialized input data.
    input_schema_path: path of input schema.

    Returns
    -------
    data: deserialized input data.

    """
    data_type = data.get("data_type", "") if isinstance(data, dict) else ""
    json_data = data.get("data", data) if isinstance(data, dict) else data

    spark_schema_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), spark_input_schema
    )
    with open(spark_schema_path) as f:
        spark_schema = StructType.fromJson(json.loads(f.read()))

    try:
        rdd_data = spark.sparkContext.parallelize(json_data)
        return spark.read.json(rdd_data, schema=spark_schema)
    except:
        raise TypeError(
            f"unsupported data_type: {data_type}. Only supported data types are: pyspark.sql.dataframe.DataFrame, pyspark.pandas.dataframe.DataFrame, pandas.DataFrame, json"
        )


def pre_inference(data, input_schema_path):
    """
    Preprocess data

    Parameters
    ----------
    data: Data format as expected by the predict API of the core estimator.
    input_schema_path: path of input schema.

    Returns
    -------
    data: Data format after any processing.

    """
    data = deserialize(data, input_schema_path)
    return data


def post_inference(yhat, input_cols):
    """
    Post-process the model results

    Parameters
    ----------
    yhat: Data format after calling model.predict.

    Returns
    -------
    yhat: Data format after any processing.

    """
    return yhat.toPandas()["prediction"].to_list()


def predict(
    data,
    model=load_model(),
    input_schema_path=os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "input_schema.json"
    ),
):
    """
    Returns prediction given the model and data to predict

    Parameters
    ----------
    model: Model instance returned by load_model API
    data: Data format as expected by the predict API of the core estimator. For eg. in case of sckit models it could be numpy array/List of list/Pandas DataFrame
    input_schema_path: path of input schema.

    Returns
    -------
    predictions: Output from scoring server
        Format: {'prediction': output from model.predict method}

    """

    input = pre_inference(data, input_schema_path)
    input_cols = input.columns
    print("Dataset Count: " + str(input.count()))

    yhat = post_inference(model.transform(input), input_cols)
    return {"prediction": yhat}
