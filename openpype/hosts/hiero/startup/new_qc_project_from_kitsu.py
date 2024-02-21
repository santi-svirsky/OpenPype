""" OpenPype custom script for resetting read nodes start frame values """
import os
import re
import pprint
import distutils.dir_util

import hiero.core
import hiero.ui
from hiero.core import (newProject, BinItem, Bin, Sequence, VideoTrack)
import foundry.ui

from bson import json_util
from datetime import date, datetime
import gazu

from openpype.modules.kitsu.utils import credentials
from openpype.client import get_representations
from openpype.pipeline import Anatomy

from qtpy import QtWidgets
from qtpy.QtWidgets import QInputDialog, QLineEdit

from openpype.lib import Logger, StringTemplate

log = Logger.get_logger(__name__)

def main():
    print("Loaded script 'new_qc_project_from_kitsu.py'")

    playlist_url, ok = QInputDialog().getText(None, "New QC Project Playlist",
                                        "Playlist URL:", QLineEdit.Normal)

    create_qc_timeline(playlist_url)


def list_files(path):
    files_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            files_list.append(os.path.join(root, file))
        for dir in dirs:
            list_files(os.path.join(root, dir))
    return files_list


def create_qc_timeline(playlist_url):
    user, password = credentials.load_credentials()

    if credentials.validate_credentials(user, password):
        # URL has the playlist id that we need to locate the playlist
        pattern = r"playlists\/([^\/]+)"
        results = re.search(pattern, playlist_url)
        playlist_id = None

        if len(results.groups()) > 0:
            playlist_id = results.group(1)
            log.info("Playlist ID: {}".format(playlist_id))

            gazu.log_in(user, password)

            playlist = gazu.playlist.get_playlist(playlist_id)
            playlist_name = playlist.get("name")

            # Get current project and clipbin:
            myProject = hiero.core.projects()[-1]
            clipsBin = myProject.clipsBin()

            # Create bin, name it and add it to clip bin.
            qc_bin = hiero.core.Bin("QC_{}".format(playlist_name))
            clipsBin.addItem(qc_bin)

            # Add sequence to bin and create tracks
            sequence = hiero.core.Sequence(playlist_name)
            clipsBin.addItem(hiero.core.BinItem(sequence))
            videotrack = hiero.core.VideoTrack("latest compo")
            audiotrack = hiero.core.AudioTrack("animatic")

            # Set initial position in timeline
            timeline_in = 0

            log.info(f"Processing {playlist_name}")

            for entity in playlist.get("shots"):
                # Get id's
                entity_id = entity.get("entity_id")
                preview_file_id = entity.get("preview_file_id")

                # Get shot, preview and task
                shot = gazu.shot.get_shot(entity_id)
                preview_file = gazu.files.get_preview_file(preview_file_id)
                task_id = preview_file["task_id"]
                task = gazu.task.get_task(task_id)

                #####################
                # Compositing plates:
                # Get representations and place them in video track

                compo_representations = get_plate_representations("compo", shot, task, preview_file)

                frame_in = None
                # Of all representations, we keep the 'png', just first and last frame
                for repr in compo_representations:
                    if repr["name"] == "png":
                        frame_in = repr["files"][0]
                        frame_out = repr["files"][-1]
                        log.info(repr["files"][0])
                        break

                if frame_in:
                    path_to_representation = frame_in["path"]
                    path_to_representation = map_representation_path(path_to_representation, shot["project_name"])
                    add_track_item(path_to_representation, qc_bin, videotrack, timeline_in)

                #####################
                # Animatic plates:
                # Get representations and place them in audio track

                animatic_representations = get_plate_representations("animatic", shot)

                # Get the latest version of animatic
                max_index = 0
                newest_version = None
                for repr in animatic_representations:
                    if int(repr["context"]["version"]) >= max_index:
                        max_index = int(repr["context"]["version"])
                        newest_version = repr

                print(newest_version)
                animatic_path = newest_version["data"]["path"]
                animatic_path = map_representation_path(animatic_path, shot["project_name"])

                source_duration = add_track_item(animatic_path, qc_bin, audiotrack, timeline_in)

                # Move the position in timeline
                timeline_in += source_duration

            # Add tracks to sequence and display it
            sequence.addTrack(audiotrack)
            sequence.addTrack(videotrack)
            editor = hiero.ui.getTimelineEditor(sequence)
            editor.window()


def add_track_item(path_to_representation, bin, track, timeline_in):
    # Add a track item to the timeline, at the frame indicated in "timeline_in"

    log.info("Adding new item to timeline: {}".format(path_to_representation))
    repr_clip = bin.createClip(path_to_representation)
    repr_clip.rescan()
    trackItem = track.createTrackItem(path_to_representation)
    trackItem.setSource(repr_clip)

    # Keep track duration as variable
    track_duration = trackItem.sourceDuration()

    # Set track with in, out and speed
    log.info("Track item will be placed at time: {}".format(timeline_in))
    trackItem.setTimelineIn(timeline_in)
    trackItem.setTimelineOut(timeline_in + track_duration - 1)
    trackItem.setPlaybackSpeed(1)
    track.addItem(trackItem)

    # Return the duration of clip
    return track_duration


def get_plate_representations(plate_type, shot, task=None, preview_file=None):
    context = {
        "project_name": shot["project_name"],
        "asset_name": shot["name"]
    }
    context_filters = {
        "asset": context["asset_name"]
    }

    if plate_type == "compo" and task and preview_file:
        # TODO: This is pretty hacky we are retrieving the
        # Avalon Version number from the original name of
        # the file uploaded to Kitsu. I couldn't find
        # any way to relate Kitsu Preview Files to OP Representations.
        log.info("Getting representations of compos")
        log.info(preview_file["original_name"])

        version_regex = re.compile(r"^.+_v([0-9]+).*$")
        regex_result = version_regex.findall(preview_file["original_name"])
        representation_version_number = int(regex_result[0])

        context["task_name"] = task["task_type"]["name"]
        context_filters["version"] = representation_version_number
        context_filters["task"] = {"name": context["task_name"]}

        representations = get_representations(context["project_name"],
                                                      context_filters=context_filters)

    elif plate_type == "animatic":
        log.info("Getting representations of animatics")

        context["task_name"] = "Edit"
        context_filters["subset"] = ["plateAnimatic"]
        context_filters["representation"] = ["mp4"]

        representations = get_representations(context["project_name"],
                                                      context_filters=context_filters)

    else:
        raise RuntimeError("No valid plate type")

    return representations

def map_representation_path(path_to_representation, project_name):
    anatomy = Anatomy(project_name)
    data = {"root": anatomy.roots}
    path_mapped = StringTemplate.format_strict_template(path_to_representation, data)
    path_mapped = path_mapped.replace("\\", "/")
    return path_mapped
