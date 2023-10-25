#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import oci
import requests
import logging

from typing import Any, Mapping, Dict, List, Optional
from ads.common.auth import default_signer

# TODO: Switch to runtime_dependency
# from ads.common.decorator.runtime_dependency import (
#     runtime_dependency,
#     OptionalDependency,
# )
# @runtime_dependency(module="langchain", install_from=OptionalDependency.LANGCHAIN)

try:
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from langchain.pydantic_v1 import root_validator, Field, Extra
except ImportError as e:
    print("Pip install `langchain`")
    pass

try:
    from oci.generative_ai import GenerativeAiClient, models
except ImportError as e:
    print("Pip install `oci` with correct version")

logger = logging.getLogger(__name__)


class NotAuthorizedError(oci.exceptions.ServiceError):
    pass


# Move to constant.py
class TASK:
    TEXT_GENERATION = "text_generation"
    SUMMARY_TEXT = "summary_text"


class LengthParamOptions:
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"
    AUTO = "AUTO"


class FormatParamOptions:
    PARAGRAPH = "PARAGRAPH"
    BULLETS = "BULLETS"
    AUTO = "AUTO"


class ExtractivenessParamOptions:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    AUTO = "AUTO"


class OCIGenerativeAIModelOptions:
    COHERE_COMMAND = "cohere.command"
    COHERE_COMMAND_LIGHT = "cohere.command-light"


DEFAULT_SERVICE_ENDPOINT = (
    "https://generativeai.aiservice.us-chicago-1.oci.oraclecloud.com"
)
DEFAULT_TIME_OUT = 300
DEFAULT_CONTENT_TYPE_JSON = "application/json"


class OCILLM(LLM):
    """Base OCI LLM class. Contains common attributes."""

    auth: Any
    """ADS auth dictionary for OCI authentication.
    This can be generated by calling `ads.common.auth.api_keys()` or `ads.common.auth.resource_principal()`.
    If this is not provided then the `ads.common.default_signer()` will be used."""

    max_tokens: int = 256
    """Denotes the number of tokens to predict per generation."""

    temperature: float = 0.1
    """A non-negative float that tunes the degree of randomness in generation."""

    k: int = 0
    """Number of most likely tokens to consider at each step."""

    p: int = 0.9
    """Total probability mass of tokens to consider at each step."""

    stop: Optional[List[str]] = None
    """Stop words to use when generating. Model output is cut off at the first occurrence of any of these substrings."""

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid


class GenerativeAI(OCILLM):
    """GenerativeAI Service.

    To use, you should have the ``oci`` python package installed.

    Example
    -------

    .. code-block:: python

        from ads.llm import GenerativeAI

        gen_ai = GenerativeAI(compartment_id="ocid1.compartment.oc1..<ocid>")

    """

    client: Any  #: :meta private:
    """OCI GenerativeAiClient."""

    model: Optional[str] = OCIGenerativeAIModelOptions.COHERE_COMMAND
    """Model name to use."""

    frequency_penalty: float = None
    """Penalizes repeated tokens according to frequency. Between 0 and 1."""

    presence_penalty: float = None
    """Penalizes repeated tokens. Between 0 and 1."""

    truncate: Optional[str] = None
    """Specify how the client handles inputs longer than the maximum token."""

    length: str = LengthParamOptions.AUTO
    """Indicates the approximate length of the summary. """

    format: str = FormatParamOptions.PARAGRAPH
    """Indicates the style in which the summary will be delivered - in a free form paragraph or in bullet points."""

    extractiveness: str = ExtractivenessParamOptions.AUTO
    """Controls how close to the original text the summary is. High extractiveness summaries will lean towards reusing sentences verbatim, while low extractiveness summaries will tend to paraphrase more."""

    additional_command: str = ""
    """A free-form instruction for modifying how the summaries get generated. """

    endpoint_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Optional attributes passed to the generate_text/summarize_text function."""

    client_kwargs: Dict[str, Any] = {}
    """Holds any client parametes for creating GenerativeAiClient"""

    service_endpoint: str = DEFAULT_SERVICE_ENDPOINT
    """The name of the service endpoint from the OCI GenertiveAI Service."""

    compartment_id: str = None
    """Compartment ID of the caller."""

    task: str = TASK.TEXT_GENERATION
    """Indicates the task."""

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that python package exists in environment."""
        if values.get("client") is not None:
            return values

        _auth = values.get("auth", default_signer())
        _client_kwargs = values["client_kwargs"] or {}
        _service_endpoint = _client_kwargs.get(
            "service_endpoint",
            values.get("service_endpoint", None) or cls.service_endpoint,
        )
        _client_kwargs["service_endpoint"] = _service_endpoint
        try:
            import oci

            values["client"] = GenerativeAiClient(**_auth, **_client_kwargs)
        except ImportError:
            raise ImportError(
                "Could not import oci python package. "
                "Please install it with `pip install oci`."
            )
        return values

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            **{
                "model": self.model,
                "task": self.task,
                "client_kwargs": self.client_kwargs,
                "endpoint_kwargs": self.endpoint_kwargs,
            },
            **self._default_params,
        }

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "GenerativeAI"

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling OCIGenerativeAI API."""
        return (
            {
                "compartment_id": self.compartment_id,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_k": self.k,
                "top_p": self.p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty,
                "truncate": self.truncate,
                "serving_mode": models.OnDemandServingMode(model_id=self.model),
            }
            if self.task == "text_generation"
            else {
                "serving_mode": models.OnDemandServingMode(model_id=self.model),
                "compartment_id": self.compartment_id,
                "temperature": self.temperature,
                "length": self.length,
                "format": self.format,
                "extractiveness": self.extractiveness,
                "additional_command": self.additional_command,
            }
        )

    def _invocation_params(self, stop: Optional[List[str]], **kwargs: Any) -> dict:
        params = self._default_params
        if self.task == TASK.SUMMARY_TEXT:
            return {**params}

        if self.stop is not None and stop is not None:
            raise ValueError("`stop` found in both the input and default params.")
        elif self.stop is not None:
            params["stop_sequences"] = self.stop
        else:
            params["stop_sequences"] = stop
        return {**params, **kwargs}

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Call out to GenerativeAI's generate endpoint.

        Parameters
        ----------
        prompt: The prompt to pass into the model.
        stop: Optional list of stop words to use when generating.

        Returns
        -------
        The string generated by the model.

        Example
        -------

            .. code-block:: python

                response = gen_ai("Tell me a joke.")
        """

        params = self._invocation_params(stop, **kwargs)

        try:
            response = (
                self.completion_with_retry(prompts=[prompt], **params)
                if self.task == TASK.TEXT_GENERATION
                else self.completion_with_retry(input=prompt, **params)
            )
        except Exception as ex:
            logger.error(
                "Error occur when invoking oci service api."
                f"DEBUG INTO: task={self.task}, params={params}, prompt={prompt}"
            )
            raise

        return self._process_response(response, params.get("num_generations", 1))

    def _process_response(self, response: Any, num_generations: int = 1) -> str:
        if self.task == TASK.SUMMARY_TEXT:
            return response.data.summary

        return (
            response.data.generated_texts[0][0].text
            if num_generations == 1
            else [gen.text for gen in response.data.generated_texts[0]]
        )

    def completion_with_retry(self, **kwargs: Any) -> Any:
        _model_kwargs = {**kwargs}
        _endpoint_kwargs = self.endpoint_kwargs or {}

        if self.task == TASK.TEXT_GENERATION:
            return self.client.generate_text(
                models.GenerateTextDetails(**_model_kwargs), **_endpoint_kwargs
            )
        elif self.task == TASK.SUMMARY_TEXT:
            return self.client.summarize_text(
                models.SummarizeTextDetails(**_model_kwargs), **_endpoint_kwargs
            )
        else:
            raise ValueError("Unsupported tasks.")

    def batch_completion(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        num_generations: int = 1,
        **kwargs: Any,
    ) -> List[str]:
        """Generates multiple completion for the given prompt.

        Parameters
        ----------
        prompt (str):
            The prompt to pass into the model.
        stop: (List[str], optional):
            Optional list of stop words to use when generating. Defaults to None.
        num_generations (int, optional):
            Number of completions aims to get. Defaults to 1.

        Raises
        ------
        NotImplementedError
            Raise when invoking batch_completion under summarization task.

        Returns
        -------
        List[str]
            List of multiple completions.

        Example
        -------

            .. code-block:: python

                responses = gen_ai.batch_completion("Tell me a joke.", num_generations=5)

        """
        if self.task == TASK.SUMMARY_TEXT:
            raise NotImplementedError(
                f"task={TASK.SUMMARY_TEXT} does not support batch_completion. "
            )

        return self._call(
            prompt=prompt,
            stop=stop,
            run_manager=run_manager,
            num_generations=num_generations,
            **kwargs,
        )


class OCIModelDeployment(OCILLM):
    """Base class for OCI Model Deployment Endpoint model."""

    endpoint: str = None
    """The uri of the endpoint from the deployed Model Deployment model."""

    best_of: int = 1
    """Generates best_of completions server-side and returns the "best" (the one with the highest log probability per token). """

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            **{"endpoint": self.endpoint},
            **self._default_params,
        }

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Dont do anything if client provided externally."""

        _signer = values.get("auth", default_signer()["signer"])
        try:
            import requests

            values["signer"] = _signer
        except ImportError:
            raise ImportError(
                "Could not import requests python package. "
                "Please install it with `pip install requests`."
            )
        return values

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to OCI Data Science Model Deployment TGI endpoint.

        Parameters
        ----------
        prompt (str):
            The prompt to pass into the model.
        stop (List[str], Optional):
            List of stop words to use when generating.

        Returns
        -------
            The string generated by the model.

        Example
        -------

            .. code-block:: python

                response = oci_md("Tell me a joke.")

        """
        params = self._invocation_params(stop, **kwargs)
        body = self._construct_json_body(prompt, params)
        response = self.send_request(
            data=body, endpoint=self.endpoint, timeout=DEFAULT_TIME_OUT
        )

        return str(response.get("generated_text", response))

    def send_request(
        self,
        data,
        endpoint: str,
        header: dict = {},
        **kwargs,
    ) -> Dict:
        """Sends request to the model deployment endpoint.

        Parameters
        ----------
        data (Json serializablype):
            data need to be sent to the endpoint.
        endpoint (str):
            The model HTTP endpoint.
        header (dict, optional):
            A dictionary of HTTP headers to send to the specified url. Defaults to {}.

        Raises
        ------
        NotAuthorizedError:
            Raise when the provided ``auth`` is not valid.
        ValueError:
            Raise when invoking fails.

        Returns
        -------
            A JSON representive of a requests.Response object.
        """
        header["Content-Type"] = (
            header.pop("content_type", DEFAULT_CONTENT_TYPE_JSON)
            or DEFAULT_CONTENT_TYPE_JSON
        )
        request_kwargs = {"json": data}
        request_kwargs["headers"] = header
        request_kwargs["auth"] = self.signer
        print(request_kwargs)

        try:
            response = requests.post(endpoint, **request_kwargs, **kwargs)
            response_json = response.json()

        except Exception:
            response = requests.post(endpoint, **request_kwargs, **kwargs)
            logger.error(
                f"DEBUG INFO: request_kwargs={request_kwargs},"
                f"status_code={response.status_code}, "
                f"content={response._content}"
            )
            raise

        return response_json

    def _construct_json_body(self, prompt, params):
        """Needs to be implemented in different framework."""
        raise NotImplementedError


class OCIModelDeploymentTGI(OCIModelDeployment):
    """OCI Data Science Model Deployment TGI Endpoint.

    Example
    -------

        .. code-block:: python

            oci_md = OCIModelDeploymentTGI(*args, **kwargs)
            oci_md("Tell me a joke.")

    """

    do_sample: bool = True
    """if set to True, this parameter enables decoding strategies such as multinomial sampling, beam-search multinomial sampling, Top-K sampling and Top-p sampling. """

    watermark = True

    return_full_text = True

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "oci_model_deployment_tgi_endpoint"

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for invoking OCI model deployment TGI endpoint."""
        return {
            "best_of": self.best_of,
            "max_new_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_k": self.k
            if self.k > 0
            else None,  # `top_k` must be strictly positive'
            "top_p": self.p,
            "do_sample": self.do_sample,
            "return_full_text": self.return_full_text,
            "watermark": self.watermark,
        }

    def _invocation_params(self, stop: Optional[List[str]], **kwargs: Any) -> dict:
        params = self._default_params
        if self.stop is not None and stop is not None:
            raise ValueError("`stop` found in both the input and default params.")
        elif self.stop is not None:
            params["stop"] = self.stop
        elif stop is not None:
            params["stop"] = stop
        else:  # don't set stop in param as None. TGI not accept stop=null.
            pass
        return {**params, **kwargs}

    def _construct_json_body(self, prompt, params):
        return {
            "inputs": prompt,
            "parameters": params,
        }


class OCIModelDeploymentvLLM(OCIModelDeployment):
    """Not support yet."""

    pass


#     n: int = 1
#     """Number of output sequences to return for the given prompt."""

#     presence_penalty: float = 0.0
#     """Float that penalizes new tokens based on whether they appear in the
#     generated text so far"""

#     frequency_penalty: float = 0.0
#     """Float that penalizes new tokens based on their frequency in the
#     generated text so far"""

#     use_beam_search: bool = False
#     """Whether to use beam search instead of sampling."""

#     ignore_eos: bool = False
#     """Whether to ignore the EOS token and continue generating tokens after
#     the EOS token is generated."""

#     logprobs: Optional[int] = None
#     """Number of log probabilities to return per output token."""

#     @property
#     def _llm_type(self) -> str:
#         """Return type of llm."""
#         return "oci_model_deployment_vllm_endpoint"

#     @property
#     def _default_params(self) -> Dict[str, Any]:
#         """Get the default parameters for invoking OCI model deployment vllm endpoint."""
#         return {
#             "n": self.n,
#             "best_of": self.best_of,
#             "max_tokens": self.max_tokens,
#             "top_k": self.k,
#             "top_p": self.p,
#             "temperature": self.temperature,
#             "presence_penalty": self.presence_penalty,
#             "frequency_penalty": self.frequency_penalty,
#             "ignore_eos": self.ignore_eos,
#             "use_beam_search": self.use_beam_search,
#             "logprobs": self.logprobs,
#         }

#     def _invocation_params(self, stop: Optional[List[str]], **kwargs: Any) -> dict:
#         params = self._default_params
#         if self.stop is not None and stop is not None:
#             raise ValueError("`stop` found in both the input and default params.")
#         elif self.stop is not None:
#             params["stop"] = self.stop
#         else:
#             params["stop"] = stop
#         return {**params, **kwargs}
