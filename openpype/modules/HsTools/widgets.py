import os
import pprint
from qtpy import QtWidgets, uic, QtCore, QtGui

from openpype.style import load_stylesheet
import gazu
import re

from openpype.modules.kitsu.utils import credentials
from openpype.lib import Logger

from openpype.client import get_projects

import tempfile

from copy import deepcopy

log = Logger.get_logger("MyHsToolsDialog")

from openpype.pipeline import AvalonMongoDB, Anatomy
from openpype.tools.utils.models import ProjectModel, ProjectSortFilterProxy
from openpype.lib import StringTemplate

from openpype.modules.puf_addons.gobbler.module import gobble


class MyHsToolsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyHsToolsDialog, self).__init__(parent)
        self.setMinimumSize(300, 200)
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(self)
        label.setText("Hs Tools")
        layout.addWidget(label)

        button = QtWidgets.QPushButton("Open Kitsu Playlist Sort Tool", parent=self)
        button.clicked.connect(self.onClickOpenKitsuPlaylistSortTool)
        layout.addWidget(button)

        button = QtWidgets.QPushButton("Open Gobble Tool", parent=self)
        button.clicked.connect(self.onClickOpenGobble)
        layout.addWidget(button)

        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(load_stylesheet())

        self.setAttribute(QtGui.Qt.WA_DeleteOnClose)

    def onClickOpenKitsuPlaylistSortTool(self):
        dialog = HsToolsPlaylistSortDialog(parent=self)
        dialog.show()

    def onClickOpenGobble(self):
        dialog = HsToolsGobbleDialog(parent=self)
        dialog.show()


class HsToolsGobbleDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(HsToolsGobbleDialog, self).__init__(parent)

        log.info("HsToolsGobbleDialog")

        # self.auth()

        base_path = os.path.dirname(__file__)
        ui = os.path.join(base_path, "ui", "HsToolsGobbleDialog.ui")
        self.ui = uic.loadUi(ui)

        self.setWindowTitle("Gobble")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.ui)

        self.setLayout(layout)

        dbcon = AvalonMongoDB()

        project_combobox = self.ui.comboBox
        # Styled delegate to propagate stylessheet
        project_delegate = QtWidgets.QStyledItemDelegate(project_combobox)
        project_combobox.setItemDelegate(project_delegate)
        # Project model with only active projects without default item
        project_model = ProjectModel(dbcon, only_active=True, add_default_project=False)
        project_model.refresh()
        # Sorting proxy model
        project_proxy = ProjectSortFilterProxy()
        project_proxy.setSourceModel(project_model)
        project_proxy.sort(0)
        project_combobox.setModel(project_proxy)

        self._project_model = project_model
        self._project_proxy = project_proxy

        self.ui.browsePushButton.clicked.connect(self.openFileDialog)
        self.ui.ingestPushButton.clicked.connect(self.onClickIngestPushButton)

    def get_project_name(self):
        index = self.ui.comboBox.currentIndex()
        proxy_index = self._project_proxy.index(index, 0)
        source_index = self._project_proxy.mapToSource(proxy_index)
        project = self._project_model.data(source_index)

        return project

    def openFileDialog(self):
        project = self.get_project_name()
        anatomy = Anatomy(project)
        data = {}
        data["root"] = anatomy.roots
        data["project"] = {"name": project}
        template = r"{root[work]}/{project[name]}"

        work_root = StringTemplate.format_strict_template(template, data)
        work_root = os.path.abspath(work_root)

        fileDialog = QtWidgets.QFileDialog(parent=self, directory=work_root)
        fileDialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if fileDialog.exec_():
            files = fileDialog.selectedFiles()
            self.ui.lineEdit.setText(files[0])

    def onClickIngestPushButton(self):
        project_name = self.get_project_name()
        input_dir = self.ui.lineEdit.text()
        matching_mode_widget = self.ui.matchingModeButtonGroup.checkedButton()
        matching_mode = matching_mode_widget.text()

        try:
            log.info(f"Will glob {project_name}, {input_dir}, {matching_mode}")
            gobble.callback(project_name, input_dir, matching_mode)
            msgBox = QtWidgets.QMessageBox()
            msgBox.information(self, "Gobbling finished", "Gobbling finished")

        except:
            import traceback

            error_msg = traceback.format_exc()
            log.error("Error while gobbling")
            log.error(error_msg)

            msgBox = QtWidgets.QMessageBox()
            msgBox.critical(self, "Error", "Error occurred while gobbling directory.")


class HsToolsPlaylistSortDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(HsToolsPlaylistSortDialog, self).__init__(parent)

        log.info("HsToolsPlaylistSortDialog sort playlist")

        self.auth()

        base_path = os.path.dirname(__file__)
        ui = os.path.join(base_path, "ui", "HsToolsPlaylistSortDialog.ui")
        self.ui = uic.loadUi(ui)

        self.setWindowTitle("Kitsu Playlist sort")

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

        self.temp_dir = os.path.join(
            tempfile.gettempdir(), "HsToolsPlaylistSort_addons"
        )
        os.makedirs(self.temp_dir, exist_ok=True)

        self.setStyleSheet(load_stylesheet())

        self.setAttribute(QtGui.Qt.WA_DeleteOnClose)

    def onClickPlaylistFetch(self):
        self.playlist = self.fetchPlaylist()
        self.clearTable()
        self.updateTable()

    def onClickPlaylistUpdate(self):
        if not self.playlist:
            msgBox = QtWidgets.QMessageBox()
            msgBox.critical(self, "Add a URL", "Missing URL")
            return

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
        messageBox.information(
            self, "Playlist updated", "Updated playlist {}".format(status["name"])
        )

    def auth(self):
        user, password = credentials.load_credentials()

        # version_regex = re.compile(r"^.+_v([0-9]+).*$")
        if not credentials.validate_credentials(user, password):
            raise RuntimeError("Credentials not valid.")

        gazu.log_in(user, password)
        log.info("Logged to kitsu.")

    def fetchPlaylist(self):
        playlist_url = self.ui.playlistUrlLineEdit.text()
        # playlist_url = "http://10.68.150.36/productions/be776537-51b0-433a-ae81-0b0890f85b7e/episodes/84954cf9-6091-4baf-bce0-28c64d008640/playlists/885720e5-7c9b-49b1-82b3-31c4de584508"

        if not playlist_url:
            msgBox = QtWidgets.QMessageBox()
            msgBox.critical(self, "Add a URL", "Missing URL")
            return

        # URL has the playlist id that we need to locate the playlist
        pattern = r"playlists\/([^\/]+)"
        results = re.search(pattern, playlist_url)

        playlist_id = None
        if len(results.groups()) > 0:
            playlist_id = results.group(1)
            log.info(f"Fetching Playlist ID: {playlist_id}")

            playlist = gazu.playlist.get_playlist(playlist_id)

        return playlist

    def updateTable(self):
        """ """
        if not self.playlist:
            return

        entity_type = self.playlist["for_entity"]

        if entity_type == "shot":
            shots = self.playlist["shots"]
            log.info("Found {} shots".format(len(shots)))

            for index, shot in enumerate(shots):
                entity = gazu.entity.get_entity(shot["entity_id"])
                log.info("Loading shot {} information...".format(shot["entity_id"]))
                preview_file = gazu.files.get_preview_file(shot["preview_file_id"])
                log.info(
                    "Loading preview_file {} information...".format(
                        shot["preview_file_id"]
                    )
                )
                task = gazu.task.get_task(preview_file["task_id"])
                log.info(
                    "Loading task {} information...".format(preview_file["task_id"])
                )

                row_index = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(row_index)

                # Column 0: Order
                # We need this column to be ordered by index
                # instead of an alphanumeric sorting.
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

                self.ui.tableWidget.setItem(
                    row_index,
                    4,
                    QtWidgets.QTableWidgetItem(str(preview_file["revision"])),
                )

                self.ui.tableWidget.setItem(
                    row_index, 5, QtWidgets.QTableWidgetItem(str(entity["id"]))
                )

                self.ui.tableWidget.setItem(
                    row_index, 6, QtWidgets.QTableWidgetItem(str(preview_file["id"]))
                )

                self.ui.tableWidget.resizeRowToContents(row_index)

        else:
            log.info("Only processing playlist of shots")

    def clearTable(self):
        self.ui.tableWidget.setRowCount(0)
