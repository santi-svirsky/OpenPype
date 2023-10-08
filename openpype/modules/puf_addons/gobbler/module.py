"""Launch scripts module."""
import os
import time
import pyblish
import click

from openpype.modules import OpenPypeModule
from openpype.pipeline.create import CreateContext
# from abstract_publish import publish_version
from openpype.client import get_project, get_asset_by_name
from openpype.pipeline.context_tools import change_current_context

from openpype.modules.puf_addons.gobbler.easy_publish import publish_version
# from openpype.hosts.batchpublisher import BatchPublisherHost

from openpype.modules.kitsu.utils.credentials import (
    clear_credentials,
    load_credentials,
    save_credentials,
    set_credentials_envs,
    validate_credentials,
)

# from .lib import find_app_variant
# from .run_script import (
#     run_script as _run_script
# )


class GobblerModule(OpenPypeModule):
    label = "Gobble mess from client"
    name = "gobbler"

    def initialize(self, modules_settings):
        self.enabled = True

    def cli(self, click_group):
        click_group.add_command(cli_main)


@click.group(GobblerModule.name,
             help="Publish Workfile cli commands.")
def cli_main():
    pass


@cli_main.command()
@click.option("-project", "--project_name",
              required=True,
              envvar="AVALON_PROJECT",
              help="Project name")
@click.option("-asset", "--asset_name",
              required=True,
              envvar="AVALON_ASSET",
              help="Asset name")
@click.option("-task", "--task_name",
              required=True,
              envvar="AVALON_TASK",
              help="Task name")
@click.option("-path", "--filepath",
              required=True,
              help="Absolute filepath to workfile to publish")
@click.option("-app", "--app_name",
              envvar="AVALON_APP",
              required=True,
              help="App name, specific variant 'maya/2023' or just 'maya' to "
                   "take latest found variant for which current machine has "
                   "an existing executable.")
def run_script(project_name,
               asset_name,
               task_name,
               filepath,
               app_name,
               timeout=None):
    app_name = find_app_variant(app_name)
    launched_app = _run_script(
        project_name=project_name,
        asset_name=asset_name,
        task_name=task_name,
        app_name=app_name,
        script_path=filepath
    )
    _print_stdout_until_timeout(launched_app, timeout, app_name)

    print("Application shut down.")


@cli_main.command()
@click.option("-project", "--project_name",
              required=True,
              envvar="AVALON_PROJECT",
              help="Project name")
@click.option("-asset", "--asset_name",
              required=True,
              envvar="AVALON_ASSET",
              help="Asset name")
@click.option("-task", "--task_name",
              required=True,
              envvar="AVALON_TASK",
              help="Task name")
@click.option("-path", "--filepath",
              required=True,
              help="Absolute filepath to workfile to publish")
@click.option("-app", "--app_name",
              envvar="AVALON_APP_NAME",
              required=True,
              help="App name, specific variant 'maya/2023' or just 'maya' to "
                   "take latest found variant for which current machine has "
                   "an existing executable.")
@click.option("-pre", "--pre_publish_script",
              multiple=True,
              help="Pre process script path")
@click.option("-post", "--post_publish_script",
              multiple=True,
              help="Post process script path")
@click.option("-c", "--comment",
              help="Publish comment")
def publish(project_name,
            asset_name,
            task_name,
            filepath,
            app_name=None,
            pre_publish_script=None,
            post_publish_script=None,
            comment=None,
            timeout=None):
    """Publish a workfile standalone for a host."""

    # The entry point should be a script that opens the workfile since the
    # `run_script` interface doesn't have an "open with file" argument due to
    # some hosts triggering scripts before opening the file or not allowing
    # both scripts to run and a file to open. As such, the best entry point
    # is to just open in the host instead and allow the script itself to open
    # a file.

    print(f"Using context {project_name} > {asset_name} > {task_name}")
    print(f"Publishing workfile: {filepath}")

    if not os.path.exists(filepath):
        raise RuntimeError(f"Filepath does not exist: {filepath}")

    # Pass specific arguments to the publish script using environment variables
    env = os.environ.copy()
    env["PUBLISH_WORKFILE"] = filepath

    if pre_publish_script:
        print(f"Pre scripts: {', '.join(pre_publish_script)}")
        env["PUBLISH_PRE_SCRIPTS"] = os.pathsep.join(pre_publish_script)
    if post_publish_script:
        print(f"Post scripts: {', '.join(post_publish_script)}")
        env["PUBLISH_PRE_SCRIPTS"] = os.pathsep.join(post_publish_script)
    if comment:
        env["PUBLISH_COMMENT"] = comment

    script_path = os.path.join(os.path.dirname(__file__),
                               "scripts",
                               "publish_script.py")

    app_name = find_app_variant(app_name)
    launched_app = _run_script(
        project_name=project_name,
        asset_name=asset_name,
        task_name=task_name,
        app_name=app_name,
        script_path=script_path,
        env=env
    )
    _print_stdout_until_timeout(launched_app, timeout, app_name)

    print("Application shut down.")

@cli_main.command()
@click.option("-p", "--project_name",
              required=True,
              envvar="AVALON_PROJECT",
              help="Project name")
@click.option("-d", "--directory",
              required=False,
              help="Directory to gobble")
def go(project_name, directory=None):
    print("GO!")
    os.environ["AVALON_PROJECT"] = project_name
    from openpype.lib import Logger
    from openpype.lib.applications import (
        get_app_environments_for_context,
        LaunchTypes,
    )
    from openpype.modules import ModulesManager
    from openpype.pipeline import (
        install_openpype_plugins,
        get_global_context,
    )
    from openpype.tools.utils.host_tools import show_publish
    from openpype.tools.utils.lib import qt_app_context

    from openpype.modules.kitsu import KitsuModule
    # Register target and host
    import pyblish.api
    import pyblish.util

    log = Logger.get_logger("CLI-publish")

    # env
    # env = os.environ.copy()
    # kitsu
    # env["KITSU_SERVER"] = 'http://10.68.150.36/'
    # env["KITSU_LOGIN"], = 'admin@example.com'
    # env["KITSU_PWD"] = 'mysecretpassword'


    # clear_credentials,
    (l, p) = load_credentials()
    # print(load_credentials)
    # save_credentials,
    set_credentials_envs(l, p)

    # kitsu = KitsuModule()
    # kitsu.initialize()

    # validate_credentials,
    # ???
    x = pyblish.api.register_host("batchpublisher")
    print(x)

    # import pyblish.util
    # context = pyblish.util.collect()
    # print(context)
    # host = BatchPublisherHost()
    # host.set_project_name(project_name)
    # print(host.get_current_asset_name())
    # print(host.get_current_context())
    # print(host.get_context_data())

    # print(dir(host))
    # install_openpype_plugins()

    manager = ModulesManager()

    # for item in manager.get_enabled_modules():
        # print(item)
    publish_plugin_paths = manager.collect_plugin_paths()["publish"]

    for path in publish_plugin_paths:
        pyblish.api.register_plugin_path(path)
        print(path)

    # if not any(paths):
    #     raise RuntimeError("No publish paths specified")

    # self.data["asset_doc"] = asset_doc
    # asset_doc = get_asset_by_id(project_name, folder["id"])

    asset_name = "CSE101_BG_EXT_BoaBranch"
    family_name = "render"
    task_name = "Concept"
    subset_name = "BoaBranch"
    expected_representations = {"png": "/home/santi/Screenshots/snip_20231007-185838.png"}
    publish_data = {}


    # project_doc = get_project(project_name)
    # project_doc = project_doc

    asset_doc = get_asset_by_name(project_name, asset_name)

    # change_current_context(
    #     asset_doc,
    #     task_name,
    #     # template_key=template_key
    # )






    from openpype.hosts.traypublisher.api import TrayPublisherHost
    from openpype.pipeline import install_host

    class FakeHost(TrayPublisherHost):
        name = "fake"

    host = FakeHost()
    install_host(host)

    print(f"<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>> {os.environ.get('AVALON_PROJECT')}")
    # host = registered_host()
    context = CreateContext(host)



    publish_version(project_name,
                    asset_name,
                    task_name,
                    family_name,
                    subset_name,
                    expected_representations,
                    publish_data)














def _print_stdout_until_timeout(popen,
                                timeout=None,
                                app_name=None):
    """Print stdout until app close.

    If app remains open for longer than `timeout` then app is terminated.

    """
    time_start = time.time()
    prefix = f"{app_name}: " if app_name else " "
    for line in popen.stdout:
        # Print stdout
        line_str = line.decode("utf-8")
        print(f"{prefix}{line_str}", end='')

        if timeout and time.time() - time_start > timeout:
            popen.terminate()
            raise RuntimeError("Timeout reached")
