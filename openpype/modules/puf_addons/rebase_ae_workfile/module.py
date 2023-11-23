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

# from . import easy_publish

from openpype.hosts.traypublisher.api import TrayPublisherHost
from openpype.pipeline import install_host
from openpype.lib import Logger

from openpype.modules.kitsu.utils import credentials

from openpype.modules.puf_addons.launch_scripts.lib import find_app_variant
from openpype.modules.puf_addons.launch_scripts.module import _print_stdout_until_timeout

log = Logger.get_logger("RebaseAEWorkfile")

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
    from openpype.lib import (
        ApplicationManager,
        ApplicationNotFound,
        ApplictionExecutableNotFound,
        get_app_environments_for_context
    )

    from openpype.lib.applications import (
        ApplicationLaunchContext,
        ApplicationExecutable
    )


    import subprocess

    log.info(f"{project}, {asset}, {task}")

    context = {
        "project_name": project,
        "asset_name": asset,
        "task_name": task,
    }

    app_name = "aftereffects/2023"

    application_manager = ApplicationManager()
    app = application_manager.applications.get(app_name)
    if not app:
        raise ApplicationNotFound(app_name)

    # Must-have for proper launch of app
    app_env = get_app_environments_for_context(
        context["project_name"],
        context["asset_name"],
        context["task_name"],
        app_name
    )

    executable = app.find_executable()

    env = dict(os.environ.copy())
    env.update(app_env)
    env.update({
        # "OPENPYPE_WEBSERVER_URL": "http://localhost:8079"
        "HS_FORCE_REPLACE_PLACEHOLDERS": "1",
        "AVALON_AFTEREFFECTS_WORKFILES_ON_LAUNCH": "0",
        "AVALON_PHOTOSHOP_WORKFILES_ON_LAUNCH": "0"
    })

    # Application specific arguments to launch script
    host_name = app_name.split("/", 1)[0]
    app_args = []
    data = {}
    data.update(dict(
        app_args=app_args,
        project_name=context["project_name"],
        asset_name=context["asset_name"],
        task_name=context["task_name"],
        env=env,
        # start_last_workfile=start_last_workfile,
    ))

    context = ApplicationLaunchContext(
        app, executable, **data
    )

    # TODO: Do not hardcode this - we might not always want to capture output
    #  and especially not stderr -> stdout. For now this is used to capture
    #  the output from the subprocess and log the output accordingly
    context.kwargs["stdout"] = subprocess.PIPE
    context.kwargs["stderr"] = subprocess.STDOUT

    proc = context.launch()
    _print_stdout_until_timeout(proc)

    # start_script = os.path.join(
    #     os.getenv("OPENPYPE_ROOT"),
    #     "start.py",
    # )

    # non_python_host_launch = os.path.join(
    #     os.getenv("OPENPYPE_ROOT"),
    #     "openpype",
    #     "scripts",
    #     "non_python_host_launch.py",
    # )

    # cmds = [
    #     "python",
    #     start_script,
    #     "run",
    #     non_python_host_launch,
    #     app_executable,
    #     'X:\\sombrero\\jobs\\DevAE\\Shots\\E01\\SQ01\\SH01\\work\\Animation\\devae_SH01_Animation_v002.aep',
    #     # 'X:\\sombrero\\jobs\\DevAE\\Shots\\E01\\SQ01\\SH01\\work\\Animation\\devae_SH01_Animation_v002.aep'
    # ]

    # # log.info(cmds)
    # # subprocess.Popen(cmds, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)


    # # data.update(dict(
    # #     app_args=app_args,
    # #     project_name=project_name,
    # #     asset_name=asset_name,
    # #     task_name=task_name,
    # #     env=env,
    # #     start_last_workfile=start_last_workfile,
    # # ))
    # # context = ApplicationLaunchContext(
    # #     app, executable, **data
    # # )

    # # # TODO: Do not hardcode this - we might not always want to capture output
    # # #  and especially not stderr -> stdout. For now this is used to capture
    # # #  the output from the subprocess and log the output accordingly
    # # context.kwargs["stdout"] = subprocess.PIPE
    # # context.kwargs["stderr"] = subprocess.STDOUT

    # # return context.launch()
