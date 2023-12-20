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

log = Logger.get_logger("kitsutools")


class KitsuToolsModule(OpenPypeModule):
    label = "Tools for Kitsu"
    name = "kitsutools"

    def initialize(self, modules_settings):
        self.enabled = True

    def cli(self, click_group):
        click_group.add_command(cli_main)

    def get_global_environments(self):
        """Get addon global environments.

        Use standalone publisher for asset publishing
        """
        return {}


@click.group(KitsuToolsModule.name, help="Ingest mess from client.")
def cli_main():
    pass


@cli_main.command()
@click.option("-p", "--playlist_url", required=True, help="Playlist URL")
def run(playlist_url):
    """runs a playlist through the delivey.nk template"""
    # log.info(f"Will generate a client package from {playlist_url}")

    _run(playlist_url)


from openpype.pipeline import (
    LegacyCreator,
    LoaderPlugin,
)


class Loader(LoaderPlugin):
    """Base class for Loader plug-ins."""

    hosts = []


def _run(playlist_url):
    import gazu
    import re
    import pprint

    # import json
    # from openpype.client import get_representations

    user, password = credentials.load_credentials()

    # version_regex = re.compile(r"^.+_v([0-9]+).*$")
    if not credentials.validate_credentials(user, password):
        return

    gazu.log_in(user, password)

    # URL has the playlist id that we need to locate the playlist
    pattern = r"playlists\/([^\/]+)"
    results = re.search(pattern, playlist_url)

    playlist_id = None
    if len(results.groups()) > 0:
        playlist_id = results.group(1)
        log.info(f"Playlist ID: {playlist_id}")

        # playlist = gazu.playlist.get_playlist(playlist_id)
        # pprint.pprint(playlist)

        playlist_new = {
            # "build_jobs": [],
            # "created_at": "2023-12-14T22:05:06",
            "episode_id": "84954cf9-6091-4baf-bce0-28c64d008640",
            # "for_client": False,
            # "for_entity": "shot",
            "id": "885720e5-7c9b-49b1-82b3-31c4de584508",
            # "is_for_all": False,
            # "name": "2023-12-14 19:04:58",
            # "project_id": "be776537-51b0-433a-ae81-0b0890f85b7e",
            "shots": [
                {
                    "entity_id": "8826b3f6-64d1-42ba-afe9-f84ae60aade2",
                    "preview_file_id": "5b9ca1f7-c3c6-404a-bbad-41fb90e8ff27",
                },
                {
                    "entity_id": "79b41a73-9a6f-425c-a0df-f082c6d7d0de",
                    "preview_file_id": "0245ac01-242a-473a-95c5-abd679f5f2bf",
                },
            ],
            # "task_type_id": "b4cfc2d3-6a34-4a46-9a08-093854581cf2",
            "type": "Playlist",
            # "updated_at": "2023-12-14T22:06:04",
        }
        gazu.playlist.update_playlist(playlist_new)

#         playlist_name = playlist.get("name")

#         log.info(f"Processing {playlist_name}")

#         for entity in playlist.get("shots"):
#             entity_id = entity.get("entity_id")
#             preview_file_id = entity.get("preview_file_id")

#             # log.info("Entity:")
#             # log.info(pprint.pformat(entity))

#             shot = gazu.shot.get_shot(entity_id)
#             preview_file = gazu.files.get_preview_file(preview_file_id)

#             # log.info("Shot:")
#             # log.info(pprint.pformat(shot))

#             # log.info("Preview File:")
#             # log.info(pprint.pformat(preview_file))

#             task_id = preview_file["task_id"]
#             task = gazu.task.get_task(task_id)

#             # TODO: This is pretty hacky we are retrieving the
#             # Avalon Version number from the original name of
#             # the file uploaded to Kitsu. I couldn't find
#             # any way to relate Kitsu Preview Files to OP Representations.
#             log.info(preview_file["original_name"])
#             regex_result = version_regex.findall(preview_file["original_name"])
#             representation_version_number = int(regex_result[0])
#             log.info(f"Representation version # {representation_version_number}")

#             context = {
#                 "project_name": shot["project_name"],
#                 "asset_name": shot["name"],
#                 "task_name": task["task_type"]["name"]
#             }
#             context_filters = {
#                 "asset": context["asset_name"],
#                 "task": {"name": context["task_name"]},
#                 "version": representation_version_number
#                 # "version": preview_file["revision"],
#                 # "task": [context["task_name"]],
#                 # "subset": [re.compile(placeholder.data["subset"])],
#                 # "hierarchy": [re.compile(placeholder.data["hierarchy"])],
#                 # "representation": [placeholder.data["representation"]],
#                 # "family": [placeholder.data["family"]]
#             }
#             representations = get_representations(context["project_name"],
#                                                   context_filters=context_filters)

#             for repr in representations:
#                 log.info(pprint.pformat(repr))
