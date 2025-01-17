#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/


from .runtime import ContainerRuntime, PythonRuntime

RUNTIME_TYPE_MAP = {
    ContainerRuntime.type: ContainerRuntime,
    PythonRuntime.type: PythonRuntime,
}
