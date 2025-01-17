===============
Getting Started
===============

Configure
---------

After having set up ``ads opctl`` on your desired machine using ``ads opctl configure``, you are ready to begin forecasting. At a bare minimum, you will need to provide the following details about your forecasting problem:

- Path to the historical data (historical_data)
- Name of the Datetime column (datetime_column)
- Forecast horizon (horizon)
- Name of the Target column (target_column)


These details exactly match the initial forecast.yaml file generated by running ``ads operator init --type forecast``:

.. code-block:: yaml

    kind: operator
    type: forecast
    version: v1
    spec:
        datetime_column:
            name: Date
        historical_data:
            url: data.csv
        horizon: 3
        model: auto
        target_column: target


Optionally, you are able to specify much more. The most common additions are:

- Path to the additional data, which has values for each period of the forecast horizon (additional_data)
- Path to test data, in the event you want to evaluate the forecast on a test set (test_data)
- List of column names that index different timeseries within the data, such as a product_ID or some other such series (target_category_columns)
- Path to the output directory, where the operator will place the forecast.csv, metrics.csv, and other artifacts produced from the run (output_directory)

An extensive list of parameters can be found in the ``YAML Schema`` section.


Run
---

After you have your forecast.yaml written, you simply run the forecast using:

.. code-block:: bash

    ads operator run -f forecast.yaml


Interpret Results
-----------------

The forecasting operator produces many output files: ``forecast.csv``, ``metrics.csv``, ``local_explanations.csv``, ``global_explanations.csv``, ``report.html``.

We will go through each of these output files in turn.

**Forecast.csv**

This file contains the entire historical dataset with the following columns:

- Series: Categorical or numerical index
- Date: Time series data
- Real values: Target values from historical data
- Fitted values: Model's predictions on historical data
- Forecasted values: Only available over the forecast horizon, representing the true forecasts
- Upper and lower bounds: Confidence intervals for the predictions (based on the specified confidence interval width in the YAML file)

**report.html**

The report.html file is designed differently for each model type. Generally, it contains a summary of the historical and additional data, a plot of the target from historical data overlaid with fitted and forecasted values, analysis of the models used, and details about the model components. It also includes a receipt YAML file, providing a fully detailed version of the original forecast.yaml file.

**Metrics.csv**

The metrics file includes relevant metrics calculated on the training set.


**Global and Local Explanations in Forecasting Models**

In the realm of forecasting models, understanding not only the predictions themselves but also the factors and features driving those predictions is of paramount importance. Global and local explanations are two distinct approaches to achieving this understanding, providing insights into the inner workings of forecasting models at different levels of granularity.

**Global Explanations:**

Global explanations aim to provide a high-level overview of how a forecasting model works across the entire dataset or a specific feature space. They offer insights into the model's general behavior, helping users grasp the overarching patterns and relationships it has learned. Here are key aspects of global explanations:

1. **Feature Importance:** Global explanations often involve the identification of feature importance, which ranks variables based on their contribution to the model's predictions. This helps users understand which features have the most significant influence on the forecasts.

2. **Model Structure:** Global explanations can also reveal the architecture and structure of the forecasting model, shedding light on the algorithms, parameters, and hyperparameters used. This information aids in understanding the model's overall approach to forecasting.

3. **Trends and Patterns:** By analyzing global explanations, users can identify broad trends and patterns in the data that the model has captured. This can include seasonality, long-term trends, and cyclical behavior.

4. **Assumptions and Constraints:** Global explanations may uncover any underlying assumptions or constraints the model operates under, highlighting potential limitations or biases.

While global explanations provide valuable insights into the model's behavior at a holistic level, they may not capture the nuances and variations that exist within the dataset.

**Local Explanations:**

Local explanations, on the other hand, delve deeper into the model's predictions for specific data points or subsets of the dataset. They offer insights into why the model made a particular prediction for a given instance. Key aspects of local explanations include:

1. **Instance-specific Insights:** Local explanations provide information about the individual features and their contribution to a specific prediction. This helps users understand why the model arrived at a particular forecast for a particular data point.

2. **Contextual Understanding:** They consider the context of the prediction, taking into account the unique characteristics of the data point in question. This is particularly valuable when dealing with outliers or anomalous data.

3. **Model Variability:** Local explanations may reveal the model's sensitivity to changes in input variables. Users can assess how small modifications to the data impact the predictions.

4. **Decision Boundaries:** In classification problems, local explanations can elucidate the decision boundaries and the factors that led to a specific classification outcome.

While local explanations offer granular insights, they may not provide a comprehensive understanding of the model's behavior across the entire dataset.
