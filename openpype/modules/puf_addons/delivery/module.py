"""Launch scripts module."""
import os
import time
import pyblish
import click
from pathlib import Path
import fileseq
import platform

from openpype.modules import OpenPypeModule
from openpype.pipeline.create import CreateContext
# from abstract_publish import publish_version
from openpype.client import get_project, get_asset_by_name
import openpype.client as client
from openpype.pipeline.context_tools import change_current_context

from . import easy_publish

from openpype.hosts.traypublisher.api import TrayPublisherHost
from openpype.pipeline import Anatomy, get_current_project_name, install_host
from openpype.pipeline.anatomy import AnatomyTemplates
from openpype.pipeline.template_data import get_template_data_with_names

from openpype.lib import Logger, StringTemplate
from openpype.modules.deadline.lib import submit as deadline_submit
from openpype.modules.deadline import constants as dl_constants

from openpype.modules.kitsu.utils import credentials

log = Logger.get_logger("Delivery")


OP_ROOT = "X:/sombrero/jobs/_openpype" if platform.system() == 'Windows' else "/sombrero/jobs/_openpype"

class DeliveryModule(OpenPypeModule):
    label = "Delivery module to submit Kitsu Playlists using a template"
    name = "delivery"

    def initialize(self, modules_settings):
        self.enabled = True

    def cli(self, click_group):
        click_group.add_command(cli_main)

    def get_global_environments(self):
        """Get addon global environments.

        Use standalone publisher for asset publishing
        """
        return {}

@click.group(DeliveryModule.name,
             help="Ingest mess from client.")
def cli_main():
    pass

@cli_main.command()
@click.option("-p", "--playlist_url",
              required=True,
              help="Playlist URL")
def submit(playlist_url):
    '''Submits a playlist through the delivey.nk template'''
    log.info(f"Will generate a client package from {playlist_url}")

    _submit(playlist_url)


from openpype.pipeline import (
    LegacyCreator,
    LoaderPlugin,
)
class Loader(LoaderPlugin):
    """Base class for Loader plug-ins."""

    hosts = []


def _submit(playlist_url):
    import gazu
    import re
    import pprint
    import json
    from openpype.client import get_representations
    user, password = credentials.load_credentials()

    version_regex = re.compile(r"^.+_v([0-9]+).*$")

    if credentials.validate_credentials(user, password):
        # URL has the playlist id that we need to locate the playlist
        pattern = r"playlists\/([^\/]+)"
        results = re.search(pattern, playlist_url)

        playlist_id = None
        if len(results.groups()) > 0:
            playlist_id = results.group(1)
            # log.info(f"Playlist ID: {playlist_id}")

            gazu.log_in(user, password)

            playlist = gazu.playlist.get_playlist(playlist_id)
            playlist_name = playlist.get("name")

            # log.info(f"Processing {playlist_name}")
            for entity in playlist.get("shots"):
                entity_id = entity.get("entity_id")
                preview_file_id = entity.get("preview_file_id")

                # log.info("Entity:")
                # log.info(pprint.pformat(entity))

                shot = gazu.shot.get_shot(entity_id)
                preview_file = gazu.files.get_preview_file(preview_file_id)

                # log.info("Shot:")
                # log.info(pprint.pformat(shot))

                # log.info("Preview File:")
                # log.info(pprint.pformat(preview_file))

                task_id = preview_file["task_id"]
                task = gazu.task.get_task(task_id)

                # TODO: This is pretty hacky we are retrieving the
                # Avalon Version number from the original name of
                # the file uploaded to Kitsu. I couldn't find
                # any way to relate Kitsu Preview Files to OP Representations.
                # log.info(preview_file["original_name"])
                regex_result = version_regex.findall(preview_file["original_name"])
                representation_version_number = int(regex_result[0])
                # log.info(f"Representation version # {representation_version_number}")

                context = {
                    "project_name": shot["project_name"],
                    "asset_name": shot["name"],
                    "task_name": task["task_type"]["name"]
                }
                context_filters = {
                    "asset": context["asset_name"],
                    "task": {"name": context["task_name"]},
                    "version": representation_version_number
                    # "version": preview_file["revision"],
                    # "task": [context["task_name"]],
                    # "subset": [re.compile(placeholder.data["subset"])],
                    # "hierarchy": [re.compile(placeholder.data["hierarchy"])],
                    # "representation": [placeholder.data["representation"]],
                    # "family": [placeholder.data["family"]]
                }
                print('*' * 40)
                log.info(context["asset_name"])
                log.info(preview_file["original_name"])
                representations = get_representations(context["project_name"],
                                                      context_filters=context_filters)

                path_to_frames = []
                represented = False
                for repr in representations:
                    represented = True
                    if len(repr['files']) > 2 and not repr['context']['representation'] == 'thumbnail' and not 'h264' in repr['context']['representation']:
                        path_to_frames = [f['path'] for f in repr['files']]
                        break
                if not represented:
                    log.info("representation not found")

                if path_to_frames:
                    project_name = context["project_name"]
                    asset_name = context["asset_name"]
                    task_name = task["task_type"]["name"]
                    host_name = None
                    data = get_template_data_with_names(project_name, asset_name, task_name, host_name)

                    anatomy = Anatomy(project_name)
                    data["root"] = anatomy.roots
                    data["package_name"] = playlist_name
                    data["ext"] = 'mov'
                    data["version"] = representation_version_number
                    solved_anatomy = AnatomyTemplates.solve_template_inner_links(anatomy["templates"])
                    delivery_path_template = solved_anatomy['delivery']["path"]

                    seq = fileseq.findSequencesInList(path_to_frames)[0]
                    OP_DELIVERY_TEMPLATE_IN = seq.format(template='{dirname}{basename}####{extension}')
                    OP_DELIVERY_TEMPLATE_IN = StringTemplate.format_strict_template(OP_DELIVERY_TEMPLATE_IN, data)
                    OP_DELIVERY_TEMPLATE_IN = os.path.normpath(OP_DELIVERY_TEMPLATE_IN)

                    OP_DELIVERY_TEMPLATE_OUT = StringTemplate.format_strict_template(delivery_path_template, data)
                    OP_DELIVERY_TEMPLATE_OUT = os.path.normpath(OP_DELIVERY_TEMPLATE_OUT)

                    OP_DELIVERY_TEMPLATE_FRAME_IN = seq.start()
                    OP_DELIVERY_TEMPLATE_FRAME_OUT = seq.end()

                    template = StringTemplate.format_strict_template(r"{root[work]}/templates/delivery.nk", data)
                    template = os.path.normpath(template)
                    plugin_data = {
                        "AWSAssetFile0": OP_DELIVERY_TEMPLATE_OUT,
                        "OutputFilePath": os.path.dirname(OP_DELIVERY_TEMPLATE_OUT),
                        "ProjectPath": template,
                        "SceneFile": template,
                        "UseGpu": True,
                        "Version": 13.2,
                        "WriteNode": "Write1",
                    }

                    extra_env = {
                        "OP_DELIVERY_TEMPLATE_IN": OP_DELIVERY_TEMPLATE_IN,
                        "OP_DELIVERY_TEMPLATE_OUT": OP_DELIVERY_TEMPLATE_OUT,
                        "OP_DELIVERY_TEMPLATE_FRAME_IN": OP_DELIVERY_TEMPLATE_FRAME_IN,
                        "OP_DELIVERY_TEMPLATE_FRAME_OUT": OP_DELIVERY_TEMPLATE_FRAME_OUT,
                    }

                    # log.info("#"*50)
                    log.info("IN: {}".format(OP_DELIVERY_TEMPLATE_IN))
                    log.info("OUT: {}".format(OP_DELIVERY_TEMPLATE_OUT))
                    log.info("Template: {}".format(template))
                    response = deadline_submit.payload_submit(
                        plugin="Nuke",
                        plugin_data=plugin_data,
                        batch_name=seq.format(template='{basename}').replace('.',''),
                        # batch_name=publish_data.get("jobBatchName") or deadline_task_name,
                        task_name=seq.format(template='{basename}').replace('.',''),
                        group=dl_constants.OP_GROUP,
                        pool=dl_constants.OP_POOL,
                        extra_env=extra_env,
                        frame_range=(OP_DELIVERY_TEMPLATE_FRAME_IN, OP_DELIVERY_TEMPLATE_FRAME_OUT)
                        # response_data=response_data
                    )
                    log.info("Job id: {}".format(response.get("_id")))
