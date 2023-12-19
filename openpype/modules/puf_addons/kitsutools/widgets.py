import os
import pprint
from qtpy import QtWidgets, uic, QtCore, QtGui

from openpype.style import load_stylesheet
import gazu
import re

from openpype.modules.kitsu.utils import credentials
from openpype.lib import Logger

import tempfile

from copy import deepcopy

log = Logger.get_logger("kitsutools")


class MyKitsuToolsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyKitsuToolsDialog, self).__init__(parent)

        self.auth()

        self.ui = uic.loadUi(
            r"X:\vfxboat\OpenPype\openpype\modules\puf_addons\kitsutools\addon.ui"
        )

        self.setWindowTitle("Connected modules")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.ui)

        self.setLayout(layout)

        self.ui.playlistFetchButton.clicked.connect(self.onClickPlaylistFetch)
        # self.ui.playlistUrlLineEdit
        self.ui.updatePlaylistButton.clicked.connect(self.onClickPlaylistUpdate)

        self.ui.tableWidget.setSortingEnabled(True)
        self.ui.tableWidget.sortItems(0, QtCore.Qt.AscendingOrder)

        # Get the horizontal header
        header = self.ui.tableWidget.horizontalHeader()

        # Set different stretch factors for each column header
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Fixed)

        # You can also set the width for the Fixed and Interactive modes
        # header.resizeSection(3, 100)

        self.playlist = None

        self.temp_dir = os.path.join(tempfile.gettempdir(), "kitsutools_addons")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.setStyleSheet(load_stylesheet())

    def onClickPlaylistFetch(self):
        self.playlist = self.fetchPlaylist()
        self.updateTable()

    def onClickPlaylistUpdate(self):
        shots = []
        for row_index in range(self.ui.tableWidget.rowCount()):
            shot = {
                "order": self.ui.tableWidget.item(row_index, 0).text(),
                "entity_id": self.ui.tableWidget.item(row_index, 5).text(),
                "preview_file_id": self.ui.tableWidget.item(row_index, 6).text(),
            }
            shots.append(shot)

        shots = sorted(shots, key=lambda obj: int(obj["order"]))

        payload = {
            "id": self.playlist["id"],
            "shots": [
                {
                    "entity_id": shot["entity_id"],
                    "preview_file_id": shot["preview_file_id"],
                }
                for shot in shots
            ],
        }

        status = gazu.playlist.update_playlist(payload)

        messageBox = QtWidgets.QMessageBox()
        messageBox.information(self, "Playlist updated", "Updated playlist {}".format(status["name"]))

    def auth(self):
        user, password = credentials.load_credentials()

        # version_regex = re.compile(r"^.+_v([0-9]+).*$")
        if not credentials.validate_credentials(user, password):
            raise RuntimeError("Credentials not valid.")

        gazu.log_in(user, password)
        log.info("Logged to kitsu.")

    def fetchPlaylist(self):
        playlist_url = self.ui.playlistUrlLineEdit.text()
        playlist_url = "http://10.68.150.36/productions/be776537-51b0-433a-ae81-0b0890f85b7e/episodes/84954cf9-6091-4baf-bce0-28c64d008640/playlists/885720e5-7c9b-49b1-82b3-31c4de584508"
        if not playlist_url:
            return

        # URL has the playlist id that we need to locate the playlist
        pattern = r"playlists\/([^\/]+)"
        results = re.search(pattern, playlist_url)

        playlist_id = None
        if len(results.groups()) > 0:
            playlist_id = results.group(1)
            log.info(f"Playlist ID: {playlist_id}")

            playlist = gazu.playlist.get_playlist(playlist_id)

        return playlist

    def updateTable(self):
        """ """

        entity_type = self.playlist["for_entity"]

        if entity_type == "shot":
            shots = self.playlist["shots"]

            for index, shot in enumerate(shots):
                entity = gazu.entity.get_entity(shot["entity_id"])
                preview_file = gazu.files.get_preview_file(shot["preview_file_id"])
                task = gazu.task.get_task(preview_file["task_id"])

                # pprint.pprint(entity)
                # pprint.pprint(preview_file)
                # pprint.pprint(task)

                row_index = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(row_index)

                # Column 0: Order
                # We need this column to be ordered by index
                # instead of an alphanumeric sorting.
                #
                widget = QtWidgets.QTableWidgetItem()
                widget.setData(QtCore.Qt.DisplayRole, index * 10)
                self.ui.tableWidget.setItem(row_index, 0, widget)

                # Column 1: Display a bitmap image using QLabel
                preview_file_temp = os.path.join(
                    self.temp_dir, "{}.png".format(preview_file["id"])
                )
                if not os.path.exists(preview_file_temp):
                    gazu.files.download_preview_file_thumbnail(
                        preview_file, preview_file_temp
                    )
                image = QtGui.QPixmap(preview_file_temp)
                label_bitmap = QtWidgets.QLabel()
                label_bitmap.setPixmap(image)
                cell_widget_bitmap = QtWidgets.QWidget()
                layout_bitmap = QtWidgets.QHBoxLayout(cell_widget_bitmap)
                layout_bitmap.addWidget(label_bitmap)
                layout_bitmap.setAlignment(QtCore.Qt.AlignCenter)
                layout_bitmap.setContentsMargins(0, 0, 0, 0)
                self.ui.tableWidget.setCellWidget(row_index, 1, cell_widget_bitmap)

                # Column 2 and 3: Add text items
                name = "{} / {}".format(task["sequence"]["name"], entity["name"])
                self.ui.tableWidget.setItem(
                    row_index, 2, QtWidgets.QTableWidgetItem(name)
                )

                task_name = task["task_type"]["name"]
                self.ui.tableWidget.setItem(
                    row_index, 3, QtWidgets.QTableWidgetItem(task_name)
                )

                revision = preview_file["revision"]
                self.ui.tableWidget.setItem(
                    row_index, 4, QtWidgets.QTableWidgetItem(str(revision))
                )

                revision = preview_file["revision"]
                self.ui.tableWidget.setItem(
                    row_index, 5, QtWidgets.QTableWidgetItem(str(entity["id"]))
                )

                revision = preview_file["revision"]
                self.ui.tableWidget.setItem(
                    row_index, 6, QtWidgets.QTableWidgetItem(str(preview_file["id"]))
                )

                self.ui.tableWidget.resizeRowToContents(row_index)

        else:
            log.info("Only processing playlist of shots")
