"""Addon definition is located here.

Import of python packages that may not be available should not be imported
in global space here until are required or used.
- Qt related imports
- imports of Python 3 packages
    - we still support Python 2 hosts where addon definition should available
"""

import os
import click
# import pathlib
import pyblish
from pathlib import Path
import gazu
from fuzzywuzzy import fuzz, process
from openpype.hosts.batchpublisher import BatchPublisherHost
from openpype.pipeline import install_host

from openpype.modules.batch_publish_addon.abstract_publish import publish_version


from openpype.modules import (
    JsonFilesSettingsDef,
    OpenPypeAddOn,
    ModulesManager,
    IPluginPaths,
    ITrayAction
)


# Settings definition of this addon using `JsonFilesSettingsDef`
# - JsonFilesSettingsDef is prepared settings definition using json files
#   to define settings and store default values
class AddonSettingsDef(JsonFilesSettingsDef):
    # This will add prefixes to every schema and template from `schemas`
    #   subfolder.
    # - it is not required to fill the prefix but it is highly
    #   recommended as schemas and templates may have name clashes across
    #   multiple addons
    # - it is also recommended that prefix has addon name in it
    schema_prefix = "batch_publish_addon"

    def get_settings_root_path(self):
        """Implemented abstract class of JsonFilesSettingsDef.

        Return directory path where json files defying addon settings are
        located.
        """
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "settings"
        )


class BatchPublishAddon(OpenPypeAddOn, IPluginPaths, ITrayAction):
    """This Addon has defined its settings and interface.

    This example has system settings with an enabled option. And use
    few other interfaces:
    - `IPluginPaths` to define custom plugin paths
    - `ITrayAction` to be shown in tray tool
    """
    label = "Batch publish"
    name = "batch_publish_addon"

    def initialize(self, settings):
        """Initialization of addon."""
        module_settings = settings[self.name]
        # Enabled by settings
        self.enabled = module_settings.get("enabled", False)

        # Prepare variables that can be used or set afterwards
        self._connected_modules = None
        # UI which must not be created at this time
        self._dialog = None

    def tray_init(self):
        """Implementation of abstract method for `ITrayAction`.

        We're definitely  in tray tool so we can pre create dialog.
        """
        self._create_dialog()

    def _create_dialog(self):
        # Don't recreate dialog if already exists
        if self._dialog is not None:
            return

        from .widgets import MyExampleDialog

        self._dialog = MyExampleDialog()

    def show_dialog(self):
        """Show dialog with connected modules.

        This can be called from anywhere but can also crash in headless mode.
        There is no way to prevent addon to do invalid operations if he's
        not handling them.
        """
        # Make sure dialog is created
        self._create_dialog()
        # Show dialog
        self._dialog.open()

    def get_connected_modules(self):
        """Custom implementation of addon."""
        names = set()
        if self._connected_modules is not None:
            for module in self._connected_modules:
                names.add(module.name)
                print(module.name)
        return names

    def on_action_trigger(self):
        """Implementation of abstract method for `ITrayAction`."""
        self.show_dialog()

    def get_plugin_paths(self):
        """Implementation of abstract method for `IPluginPaths`."""
        current_dir = os.path.dirname(os.path.abspath(__file__))

        return {
            "publish": [os.path.join(current_dir, "plugins", "publish")]
        }

    def cli(self, click_group):
        click_group.add_command(cli_main)

    # def get_global_environments(self):
    #     """Get addon global environments.

    #     Use standalone publisher for asset publishing
    #     """
    #     return {
    #         "AVALON_APP_NAME": "batch_publish_addon",
    #         "AVALON_APP": "batch_publish_addon",
    #     }


@click.group(BatchPublishAddon.name, help="Example addon dynamic cli commands.")
def cli_main():
    pass

@cli_main.command()
def test2():

    host = BatchPublisherHost()
    install_host(host)
    print(1)
    # print(host.get_context_data())
    # print(type(host.get_context_data()))
    # print(Path(host.get_context_data()).read_text())
    host.set_project_name('cse_test_056')
    # print(host
        #   from pathlib import Path
    print(2)
    print(host.get_context_data())

@cli_main.command()
def test2():

    host = BatchPublisherHost()
    install_host(host)

    host.set_project_name('cse_test_056')
    # print(host.get_context_title())
    # print(host.get_context_data())
    filepath = Path("/sombrero/jobs/cse/in/20231002/09_Deliveries/2023.07.19/02_AE_Comp/02_Assets/SHOTS/CSE101_A001/ART/CSE101_BG_INT_Frances_Apartment_S10_V01.png")
    # representations = {"png": str(filepath)}

    ext = filepath.suffix.strip(".")
    representation = {
        "name": ext,
        "ext": ext,
        "preview": True,
        "tags": ["review"],
        "files": filepath.name,
        "stagingDir": filepath.parent,
    }
    representations = {'png': str(filepath)}

    publish_version('cse_test_056', 'CSE101_01_001 ', 'Compositing', 'render', 'subset_name', representations, {})
    # host.get_current_asset_name


@cli_main.command()
def test3():
    # """Processes input directory. Walks through source, fuzzy-matches to OP assets and publishes."""
    # print("You've triggered \"process_directory\" command.")
    # DIRECTORY = '/sombrero/jobs/cse/in/ingest_test/'
    # PROJECT = 'cse_test_056'
    # project = PROJECT
    # # pyblish.api.register_host("batch_publisher")


    # # def board_publish(login, password, project, board_dir, upload_to_kitsu=False):
    # #     """Synchronize openpype database from Zou sever database.

    # #     Args:
    # #         login (str): Kitsu user login
    # #         password (str): Kitsu user password
    # #         project (str): Project name
    # #         board_dir (str): Path to storyboard shot movies directory
    # #         upload_to_kitsu (bool): Upload directly to Kitsu
    # #     """
    # # validate_credentials(login, password)

    # gazu.set_host("http://10.68.150.36/api")  # PROD
    # gazu.log_in("admin@example.com", "mysecretpassword")


    # # Fetch zou data0
    # zou_project = gazu.project.get_project_by_name(project)

    # # shots = {
    # #     shot["name"]: shot
    # #     for shot in gazu.shot.all_shots_for_project(zou_project)
    # # }
    # # print(shots)
    # assets = {
    #     asset["name"]: asset
    #     for asset in gazu.asset.all_assets_for_project(zou_project)
    # }
    # task_type = gazu.task.get_task_type_by_name("Concept")
    # task_status = gazu.task.get_task_status_by_short_name("wfa")


    # # Register pyblish plugins
    # pyblish.api.register_host("shell")
    # openpype_path = Path(os.environ["OPENPYPE_REPOS_ROOT"])
    # pyblish.api.register_plugin_path(
    #     openpype_path.joinpath("openpype/plugins/publish").as_posix()
    # )
    # pyblish.api.register_plugin_path(
    #     openpype_path.joinpath(
    #         "openpype/hosts/standalonepublisher/plugins/publish"
    #     ).as_posix()
    # )

    # # Set missing context keys
    # os.environ["AVALON_APP"] = 'Photoshop'
    # os.environ["AVALON_PROJECT"] = project
    # os.environ["AVALON_PROJECT_LOWER"] = project.lower()
    # os.environ["AVALON_TASK"] = "Concept"

    for filepath in Path(DIRECTORY).iterdir():

        # match_ratios = process.extract(filepath.stem, assets.keys, scorer=fuzz.token_sort_ratio)

        # FUZZY MATCH filepath.stem vs assets.keys
        best_match, _ = process.extractOne(filepath.stem, assets.keys(), scorer=fuzz.token_sort_ratio)
        # print(best_match)

        asset = assets.get(best_match)

        # Get related zou task
        print(task_type)
        print(asset['id'])
        task = gazu.task.get_task_by_name(asset, task_type)
        print(task)
        if not task:
            continue



        # Build required pyblish data
        os.environ["AVALON_ASSET"] = asset['name']
        context = pyblish.api.Context()
        instance = context.create_instance(name=asset['name'])
        instance.data.update(
            {
                "family": "review",
                "asset": asset['name'],
                "task": "Concept",
                "subset": "background",
                "publish": True,
                "active": True,
                "source": filepath.as_posix(),
            }
        )
        # Add representation
        ext = filepath.suffix.strip(".")
        representation = {
            "name": ext,
            "ext": ext,
            "preview": True,
            "tags": ["review"],
            "files": filepath.name,
            "stagingDir": filepath.parent,
        }
        instance.data.setdefault("representations", [])
        instance.data["representations"].append(representation)

        # Publish to OP
        context = pyblish.util.publish(context)

        # Check published passed
        for result in context.data["results"]:
            if not result["success"]:
                raise result.get("error")


        # # Upload to Kitsu
        # # if upload_to_kitsu and task["task_status_id"] != real["id"]:
        # if ext in ["jpg", "png"]:
        #     preview_file_path = filepath
        # else:
        #     print(f">>>>>>>>>>>>>>>>>>>>>>>>> need to find a jpeg for {filepath}")
        #     print(instance.data)
        #     preview_file_path = None  #
        # comment = gazu.task.add_comment(task, task_status, f"Ingested from: {filepath}")
        # preview = gazu.task.add_preview(
        #     task,
        #     comment,
        #     preview_file_path=preview_file_path,
        # )
        # gazu.task.set_main_preview(preview)


@cli_main.command()
def show_dialog():
    """Show BatchPublishAddon dialog.

    We don't have access to addon directly through cli so we have to create
    it again.
    """
    from openpype.tools.utils.lib import qt_app_context

    manager = ModulesManager()
    batch_publish_addon = manager.modules_by_name[BatchPublishAddon.name]
    with qt_app_context():
        batch_publish_addon.show_dialog()
