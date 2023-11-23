"""Launch scripts module."""
import os
import time
import pyblish
import click
from pathlib import Path

from openpype.modules import OpenPypeModule
from openpype.pipeline.create import CreateContext
# from abstract_publish import publish_version
from openpype.client import get_project, get_asset_by_name
import openpype.client as client
from openpype.pipeline.context_tools import change_current_context

from . import easy_publish

from openpype.hosts.traypublisher.api import TrayPublisherHost
from openpype.pipeline import install_host
from openpype.lib import Logger

from openpype.modules.kitsu.utils import credentials

log = Logger.get_logger("Delivery")

class RebaseAEWorkfile(OpenPypeModule):
    label = "rebase ae "
    name = "rebase"

    def initialize(self, modules_settings):
        self.enabled = True

    def cli(self, click_group):
        click_group.add_command(cli_main)

    def get_global_environments(self):
        """Get addon global environments.

        Use standalone publisher for asset publishing
        """
        return {}

@click.group(RebaseAEWorkfile.name,
             help="Rebase.")
def cli_main():
    pass

@cli_main.command()
@click.option("-p", "--project",
              required=True,
              help="Project Name")
@click.option("-a", "--asset",
              required=True,
              help="Asset Name")
@click.option("-t", "--task",
              required=True,
              help="Task Name")
def submit(project, asset, task):
    '''Submits a playlist through the delivey.nk template'''
    log.info(f"{project}, {asset}, {task}")

    context = {
        "project_name": project,
        "asset_name": asset,
        "task_name": task,
    }
