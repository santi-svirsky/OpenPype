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
    label = "Batch publish Addon"
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

    def get_global_environments(self):
        """Get addon global environments.

        Use standalone publisher for asset publishing
        """
        return {
            "AVALON_APP_NAME": "standalonepublisher",
            "AVALON_APP": "standalonepublisher",
        }


@click.group(BatchPublishAddon.name, help="Example addon dynamic cli commands.")
def cli_main():
    pass


@cli_main.command()
def process_directory():
    """Does nothing but print a message."""
    print("You've triggered \"process_directory\" command.")
    DIRECTORY = '/sombrero/jobs/cse/in/ingest_test/'
    PROJECT = 'cse_test_056'
    project = PROJECT




# def board_publish(login, password, project, board_dir, upload_to_kitsu=False):
#     """Synchronize openpype database from Zou sever database.

#     Args:
#         login (str): Kitsu user login
#         password (str): Kitsu user password
#         project (str): Project name
#         board_dir (str): Path to storyboard shot movies directory
#         upload_to_kitsu (bool): Upload directly to Kitsu
#     """
    # validate_credentials(login, password)

    gazu.set_host("http://10.68.150.36/api")  # PROD
    gazu.log_in("admin@example.com", "mysecretpassword")


    # Fetch zou data
    zou_project = gazu.project.get_project_by_name(project)
    # board = gazu.task.get_task_type_by_name("Board")
    # real = gazu.task.get_task_status_by_name("Real")
    # shots = {
    #     shot["name"]: shot
    #     for shot in gazu.shot.all_shots_for_project(zou_project)
    # }
    # print(shots)
    assets = {
        asset["name"]: asset
        for asset in gazu.asset.all_assets_for_project(zou_project)
    }
    task_type = gazu.task.get_task_type_by_name("Concept")
    task_status = gazu.task.get_task_status_by_short_name("wfa")

    # print(assets)
    # Register pyblish plugins
    pyblish.api.register_host("shell")
    openpype_path = Path(os.environ["OPENPYPE_REPOS_ROOT"])
    pyblish.api.register_plugin_path(
        openpype_path.joinpath("openpype/plugins/publish").as_posix()
    )
    pyblish.api.register_plugin_path(
        openpype_path.joinpath(
            "openpype/hosts/standalonepublisher/plugins/publish"
        ).as_posix()
    )

    # Set missing context keys
    os.environ["AVALON_PROJECT"] = project
    os.environ["AVALON_PROJECT_LOWER"] = project.lower()
    os.environ["AVALON_TASK"] = "Board"


    # files = pathlib.Path(DIRECTORY).glob('*')

    # for file in files:
    #     print(file)

    # print(assets.keys())

    for filepath in Path(DIRECTORY).iterdir():

        # match_ratios = process.extract(filepath.stem, assets.keys, scorer=fuzz.token_sort_ratio)

        # FUZZY MATCH filepath.stem vs assets.keys
        best_match, _ = process.extractOne(filepath.stem, assets.keys(), scorer=fuzz.token_sort_ratio)
        # print(best_match)

        asset = assets.get(best_match)
        # for key in assets.keys():
            # print(best_match, key)
            # if best_match == key:
                # print("Yes")
        # print(asset)
        # Get related zou asset
        # asset = shots.get(filepath.stem)
        # print(filepath.stem)
        # if not shot:
        #     continue

        # Get related zou task
        print(task_type)
        print(asset['id'])
        task = gazu.task.get_task_by_name(asset, task_type)
        print(task)
        if not task:
            continue

        # # Upload to Kitsu
        # # if upload_to_kitsu and task["task_status_id"] != real["id"]:
        if True:
            comment = gazu.task.add_comment(task, task_status, f"Original: {filepath}")
            preview = gazu.task.add_preview(
                task,
                comment,
                preview_file_path=filepath,
            )
            gazu.task.set_main_preview(preview)

        # Build shot appropriate name
        # seq = gazu.shot.get_sequence_from_shot(shot)
        # shot_name = "_".join([seq["episode_name"], seq["name"], filepath.stem])

        # Build required pyblish data
        # asset['name']
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
