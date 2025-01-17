#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/


import os
from copy import deepcopy
from unittest import TestCase, mock, SkipTest

from langchain.llms import Cohere
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough

from ads.llm.serialize import load, dump
from ads.llm import (
    GenerativeAI,
    GenerativeAIEmbeddings,
    ModelDeploymentTGI,
    ModelDeploymentVLLM,
)


class ChainSerializationTest(TestCase):
    """Contains tests for chain serialization."""

    # LangChain is updating frequently on the module organization,
    # mainly affecting the id field of the serialization.
    # In the test, we will not check the id field of some components.
    # We expect users to use the same LangChain version for serialize and de-serialize

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()

    PROMPT_TEMPLATE = "Tell me a joke about {subject}"
    COMPARTMENT_ID = "<ocid>"
    GEN_AI_KWARGS = {"service_endpoint": "https://endpoint.oraclecloud.com"}
    ENDPOINT = "https://modeldeployment.customer-oci.com/ocid/predict"

    EXPECTED_LLM_CHAIN_WITH_COHERE = {
        "memory": None,
        "verbose": True,
        "tags": None,
        "metadata": None,
        "prompt": {
            "input_variables": ["subject"],
            "input_types": {},
            "output_parser": None,
            "partial_variables": {},
            "template": "Tell me a joke about {subject}",
            "template_format": "f-string",
            "validate_template": False,
            "_type": "prompt",
        },
        "llm": {
            "model": None,
            "max_tokens": 256,
            "temperature": 0.75,
            "k": 0,
            "p": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "truncate": None,
            "_type": "cohere",
        },
        "output_key": "text",
        "output_parser": {"_type": "default"},
        "return_final_only": True,
        "llm_kwargs": {},
        "_type": "llm_chain",
    }

    EXPECTED_LLM_CHAIN_WITH_OCI_MD = {
        "lc": 1,
        "type": "constructor",
        "id": ["langchain", "chains", "llm", "LLMChain"],
        "kwargs": {
            "prompt": {
                "lc": 1,
                "type": "constructor",
                "kwargs": {
                    "input_variables": ["subject"],
                    "template": "Tell me a joke about {subject}",
                    "template_format": "f-string",
                    "partial_variables": {},
                },
            },
            "llm": {
                "lc": 1,
                "type": "constructor",
                "id": ["ads", "llm", "ModelDeploymentVLLM"],
                "kwargs": {
                    "endpoint": "https://modeldeployment.customer-oci.com/ocid/predict",
                    "model": "my_model",
                },
            },
        },
    }

    EXPECTED_GEN_AI_LLM = {
        "lc": 1,
        "type": "constructor",
        "id": ["ads", "llm", "GenerativeAI"],
        "kwargs": {
            "compartment_id": "<ocid>",
            "client_kwargs": {"service_endpoint": "https://endpoint.oraclecloud.com"},
        },
    }

    EXPECTED_GEN_AI_EMBEDDINGS = {
        "lc": 1,
        "type": "constructor",
        "id": ["ads", "llm", "GenerativeAIEmbeddings"],
        "kwargs": {
            "compartment_id": "<ocid>",
            "client_kwargs": {"service_endpoint": "https://endpoint.oraclecloud.com"},
        },
    }

    EXPECTED_RUNNABLE_SEQUENCE = {
        "lc": 1,
        "type": "constructor",
        "kwargs": {
            "first": {
                "lc": 1,
                "type": "constructor",
                "kwargs": {
                    "steps": {
                        "text": {
                            "lc": 1,
                            "type": "constructor",
                            "id": [
                                "langchain_core",
                                "runnables",
                                "RunnablePassthrough",
                            ],
                            "kwargs": {"func": None, "afunc": None, "input_type": None},
                        }
                    }
                },
                "_type": "RunnableParallel",
            },
            "middle": [
                {
                    "lc": 1,
                    "type": "constructor",
                    "kwargs": {
                        "input_variables": ["subject"],
                        "template": "Tell me a joke about {subject}",
                        "template_format": "f-string",
                        "partial_variables": {},
                    },
                }
            ],
            "last": {
                "lc": 1,
                "type": "constructor",
                "id": ["ads", "llm", "ModelDeploymentTGI"],
                "kwargs": {
                    "endpoint": "https://modeldeployment.customer-oci.com/ocid/predict"
                },
            },
        },
    }

    @mock.patch.dict(os.environ, {"COHERE_API_KEY": "api_key"})
    def test_llm_chain_serialization_with_cohere(self):
        """Tests serialization of LLMChain with Cohere."""
        llm = Cohere()
        template = PromptTemplate.from_template(self.PROMPT_TEMPLATE)
        llm_chain = LLMChain(prompt=template, llm=llm, verbose=True)
        serialized = dump(llm_chain)
        self.assertEqual(serialized, self.EXPECTED_LLM_CHAIN_WITH_COHERE)
        llm_chain = load(serialized)
        self.assertIsInstance(llm_chain, LLMChain)
        self.assertIsInstance(llm_chain.prompt, PromptTemplate)
        self.assertEqual(llm_chain.prompt.template, self.PROMPT_TEMPLATE)
        self.assertIsInstance(llm_chain.llm, Cohere)
        self.assertEqual(llm_chain.input_keys, ["subject"])

    def test_llm_chain_serialization_with_oci(self):
        """Tests serialization of LLMChain with OCI Gen AI."""
        llm = ModelDeploymentVLLM(endpoint=self.ENDPOINT, model="my_model")
        template = PromptTemplate.from_template(self.PROMPT_TEMPLATE)
        llm_chain = LLMChain(prompt=template, llm=llm)
        serialized = dump(llm_chain)
        # Do not check the ID field.
        expected = deepcopy(self.EXPECTED_LLM_CHAIN_WITH_OCI_MD)
        expected["kwargs"]["prompt"]["id"] = serialized["kwargs"]["prompt"]["id"]
        self.assertEqual(serialized, expected)
        llm_chain = load(serialized)
        self.assertIsInstance(llm_chain, LLMChain)
        self.assertIsInstance(llm_chain.prompt, PromptTemplate)
        self.assertEqual(llm_chain.prompt.template, self.PROMPT_TEMPLATE)
        self.assertIsInstance(llm_chain.llm, ModelDeploymentVLLM)
        self.assertEqual(llm_chain.llm.endpoint, self.ENDPOINT)
        self.assertEqual(llm_chain.llm.model, "my_model")
        self.assertEqual(llm_chain.input_keys, ["subject"])

    def test_oci_gen_ai_serialization(self):
        """Tests serialization of OCI Gen AI LLM."""
        try:
            llm = GenerativeAI(
                compartment_id=self.COMPARTMENT_ID,
                client_kwargs=self.GEN_AI_KWARGS,
            )
        except ImportError as ex:
            raise SkipTest("OCI SDK does not support Generative AI.") from ex
        serialized = dump(llm)
        self.assertEqual(serialized, self.EXPECTED_GEN_AI_LLM)
        llm = load(serialized)
        self.assertIsInstance(llm, GenerativeAI)
        self.assertEqual(llm.compartment_id, self.COMPARTMENT_ID)

    def test_gen_ai_embeddings_serialization(self):
        """Tests serialization of OCI Gen AI embeddings."""
        try:
            embeddings = GenerativeAIEmbeddings(
                compartment_id=self.COMPARTMENT_ID, client_kwargs=self.GEN_AI_KWARGS
            )
        except ImportError as ex:
            raise SkipTest("OCI SDK does not support Generative AI.") from ex
        serialized = dump(embeddings)
        self.assertEqual(serialized, self.EXPECTED_GEN_AI_EMBEDDINGS)
        embeddings = load(serialized)
        self.assertIsInstance(embeddings, GenerativeAIEmbeddings)
        self.assertEqual(embeddings.compartment_id, self.COMPARTMENT_ID)

    def test_runnable_sequence_serialization(self):
        """Tests serialization of runnable sequence."""
        map_input = RunnableParallel(text=RunnablePassthrough())
        template = PromptTemplate.from_template(self.PROMPT_TEMPLATE)
        llm = ModelDeploymentTGI(endpoint=self.ENDPOINT)

        chain = map_input | template | llm
        serialized = dump(chain)
        # Do not check the ID fields.
        expected = deepcopy(self.EXPECTED_RUNNABLE_SEQUENCE)
        expected["id"] = serialized["id"]
        expected["kwargs"]["first"]["id"] = serialized["kwargs"]["first"]["id"]
        expected["kwargs"]["first"]["kwargs"]["steps"]["text"]["id"] = serialized[
            "kwargs"
        ]["first"]["kwargs"]["steps"]["text"]["id"]
        expected["kwargs"]["middle"][0]["id"] = serialized["kwargs"]["middle"][0]["id"]
        self.assertEqual(serialized, expected)
        chain = load(serialized)
        self.assertEqual(len(chain.steps), 3)
        self.assertIsInstance(chain.steps[0], RunnableParallel)
        self.assertEqual(
            chain.steps[0].dict(),
            {"steps": {"text": {"input_type": None, "func": None, "afunc": None}}},
        )
        self.assertIsInstance(chain.steps[1], PromptTemplate)
        self.assertIsInstance(chain.steps[2], ModelDeploymentTGI)
        self.assertEqual(chain.steps[2].endpoint, self.ENDPOINT)
