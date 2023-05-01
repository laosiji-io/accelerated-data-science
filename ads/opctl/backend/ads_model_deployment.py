#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2022, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from typing import Dict
from ads.common.auth import create_signer, AuthContext
from ads.common.oci_client import OCIClientFactory
from ads.opctl.backend.base import Backend
from ads.model.deployment import ModelDeployment


class ModelDeploymentBackend(Backend):
    def __init__(self, config: Dict) -> None:
        """
        Initialize a ModelDeployment object given config dictionary.

        Parameters
        ----------
        config: dict
            dictionary of configurations
        """
        self.config = config
        self.oci_auth = create_signer(
            config["execution"].get("auth"),
            config["execution"].get("oci_config", None),
            config["execution"].get("oci_profile", None),
        )
        self.auth_type = config["execution"].get("auth")
        self.profile = config["execution"].get("oci_profile", None)
        self.client = OCIClientFactory(**self.oci_auth).data_science

    def apply(self) -> None:
        """
        Deploy model deployment from YAML.
        """
        wait_for_completion = self.config["execution"].get("wait_for_completion")
        max_wait_time = self.config["execution"].get("max_wait_time")
        poll_interval = self.config["execution"].get("poll_interval")
        with AuthContext(auth=self.auth_type, profile=self.profile):
            model_deployment = ModelDeployment.from_dict(self.config)
            model_deployment.deploy(
                wait_for_completion=wait_for_completion,
                max_wait_time=max_wait_time,
                poll_interval=poll_interval,
            )
            print("Model Deployment id: ", model_deployment.model_deployment_id)

    def delete(self) -> None:
        """
        Delete model deployment from OCID.
        """
        model_deployment_id = self.config["execution"].get("run_id")
        wait_for_completion = self.config["execution"].get("wait_for_completion")
        max_wait_time = self.config["execution"].get("max_wait_time")
        poll_interval = self.config["execution"].get("poll_interval")
        with AuthContext(auth=self.auth_type, profile=self.profile):
            model_deployment = ModelDeployment.from_id(model_deployment_id)
            model_deployment.delete(
                wait_for_completion=wait_for_completion,
                max_wait_time=max_wait_time,
                poll_interval=poll_interval,
            )
            print(
                f"Model Deployment {model_deployment.model_deployment_id} has been deleted."
            )

    def activate(self) -> None:
        """
        Activate model deployment from OCID.
        """
        model_deployment_id = self.config["execution"].get("run_id")
        wait_for_completion = self.config["execution"].get("wait_for_completion")
        max_wait_time = self.config["execution"].get("max_wait_time")
        poll_interval = self.config["execution"].get("poll_interval")
        with AuthContext(auth=self.auth_type, profile=self.profile):
            model_deployment = ModelDeployment.from_id(model_deployment_id)
            model_deployment.activate(
                wait_for_completion=wait_for_completion,
                max_wait_time=max_wait_time,
                poll_interval=poll_interval,
            )
            print(
                f"Model Deployment {model_deployment.model_deployment_id} has been activated."
            )

    def deactivate(self) -> None:
        """
        Deactivate model deployment from OCID.
        """
        model_deployment_id = self.config["execution"].get("run_id")
        wait_for_completion = self.config["execution"].get("wait_for_completion")
        max_wait_time = self.config["execution"].get("max_wait_time")
        poll_interval = self.config["execution"].get("poll_interval")
        with AuthContext(auth=self.auth_type, profile=self.profile):
            model_deployment = ModelDeployment.from_id(model_deployment_id)
            model_deployment.deactivate(
                wait_for_completion=wait_for_completion,
                max_wait_time=max_wait_time,
                poll_interval=poll_interval,
            )
            print(
                f"Model Deployment {model_deployment.model_deployment_id} has been deactivated."
            )

    def watch(self) -> None:
        """
        Watch Model Deployment from OCID.
        """
        model_deployment_id = self.config["execution"].get("run_id")
        log_type = self.config["execution"].get("log_type")
        interval = self.config["execution"].get("interval")
        log_filter = self.config["execution"].get("log_filter")
        with AuthContext(auth=self.auth_type, profile=self.profile):
            model_deployment = ModelDeployment.from_id(model_deployment_id)
            model_deployment.watch(
                log_type=log_type, interval=interval, log_filter=log_filter
            )
