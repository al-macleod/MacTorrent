#!/usr/bin/env python3
"""MacTorrent, a PyQt6 desktop BitTorrent client."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import libtorrent as lt
from PyQt6.QtCore import QSettings, QStandardPaths, Qt, QTimer
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QMenu,
    QProgressBar,
    QPushButton,
    QSplashScreen,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

__version__ = "2.0.0"


def default_download_directory() -> str:
    """Return a writable, platform-native download folder for MacTorrent."""
    downloads = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DownloadLocation
    )
    return str(Path(downloads or Path.home()) / "MacTorrent")


def make_splash_pixmap() -> QPixmap:
    pixmap = QPixmap(620, 340)
    pixmap.fill(QColor("#101a2b"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#173958"))
    painter.drawEllipse(438, -105, 310, 310)
    painter.setBrush(QColor("#1b6b78"))
    painter.drawEllipse(490, 175, 230, 230)
    painter.setBrush(QColor("#27c4ad"))
    painter.drawRoundedRect(52, 54, 54, 54, 15, 15)
    painter.setPen(QColor("#101a2b"))
    painter.setFont(QFont("Segoe UI", 23, QFont.Weight.Bold))
    painter.drawText(52, 53, 54, 54, Qt.AlignmentFlag.AlignCenter, "M")
    painter.setPen(QColor("#91a9c3"))
    painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
    painter.drawText(52, 143, "MACLEOD SOFTWARE GROUP")
    painter.setPen(QColor("#f2f7fc"))
    painter.setFont(QFont("Segoe UI", 31, QFont.Weight.Bold))
    painter.drawText(49, 202, "MacTorrent")
    painter.setPen(QColor("#a8bacd"))
    painter.setFont(QFont("Segoe UI", 12))
    painter.drawText(52, 235, "A considered desktop experience for your torrents.")
    painter.setPen(QColor("#72869d"))
    painter.setFont(QFont("Segoe UI", 9))
    painter.drawText(52, 303, f"VERSION {__version__}   ·   WINDOWS READY")
    painter.end()
    return pixmap


def make_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#143653"))
    painter.drawRoundedRect(2, 2, 60, 60, 15, 15)
    painter.setPen(QColor("#5ee0c4"))
    painter.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "M")
    painter.end()
    return QIcon(pixmap)


class AddTorrentDialog(QDialog):
    """Collect a torrent source and its destination."""

    def __init__(self, download_path: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add torrent")
        self.setMinimumWidth(520)
        self._selected_file = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(12)

        title = QLabel("Add a torrent")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        intro = QLabel("Choose a .torrent file or paste a magnet link.")
        intro.setObjectName("mutedLabel")
        layout.addWidget(intro)

        layout.addWidget(self._field_label("Torrent file"))
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText("Select a .torrent file…")
        browse_file = QPushButton("Browse")
        browse_file.setObjectName("secondaryButton")
        browse_file.clicked.connect(self.browse_torrent_file)
        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(browse_file)
        layout.addLayout(file_row)

        layout.addWidget(self._field_label("Or use a magnet link"))
        self.magnet_input = QLineEdit()
        self.magnet_input.setPlaceholderText("magnet:?xt=urn:btih:…")
        layout.addWidget(self.magnet_input)

        layout.addWidget(self._field_label("Save to"))
        path_row = QHBoxLayout()
        self.save_path_input = QLineEdit(download_path)
        browse_folder = QPushButton("Choose folder")
        browse_folder.setObjectName("secondaryButton")
        browse_folder.clicked.connect(self.browse_save_path)
        path_row.addWidget(self.save_path_input, 1)
        path_row.addWidget(browse_folder)
        layout.addLayout(path_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add torrent")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addSpacing(8)
        layout.addWidget(buttons)

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def browse_torrent_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose torrent file", "", "Torrent files (*.torrent)"
        )
        if file_path:
            self._selected_file = file_path
            self.file_input.setText(file_path)
            self.magnet_input.clear()

    def browse_save_path(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Choose download folder", self.save_path_input.text()
        )
        if path:
            self.save_path_input.setText(path)

    def get_result(self) -> tuple[str, str, str]:
        magnet = self.magnet_input.text().strip()
        source = magnet if magnet else self._selected_file
        method = "magnet" if magnet else "file"
        return method, source, self.save_path_input.text().strip()


@dataclass
class TorrentEntry:
    handle: object
    name: str
    save_path: str
    source: str


class TorrentClient(QMainWindow):
    """Main window and torrent lifecycle controller."""

    COLUMNS = ("Torrent", "Progress", "Download", "Upload", "Status", "Location")

    def __init__(self):
        super().__init__()
        self.settings = QSettings()
        self.download_path = self.settings.value(
            "download_path", default_download_directory(), type=str
        )
        self.torrents: list[TorrentEntry] = []
        self.setWindowTitle(f"MacTorrent · v{__version__}")
        self.setMinimumSize(900, 590)
        self.resize(1240, 760)
        self.setAcceptDrops(True)

        alert_mask = (
            lt.alert.category_t.error_notification
            | lt.alert.category_t.peer_notification
            | lt.alert.category_t.port_mapping_notification
            | lt.alert.category_t.storage_notification
            | lt.alert.category_t.tracker_notification
            | lt.alert.category_t.status_notification
        )
        self.session = lt.session(
            {
                "alert_mask": alert_mask,
                "enable_dht": True,
                "enable_lsd": True,
                "enable_natpmp": True,
                "enable_upnp": True,
                "listen_interfaces": "0.0.0.0:0",
            }
        )
        self.setup_ui()
        self.setup_stylesheet()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)

    def setup_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(30, 26, 30, 16)
        root_layout.setSpacing(20)
        self.setCentralWidget(root)

        header = QHBoxLayout()
        identity = QHBoxLayout()
        identity.setSpacing(14)
        logo = QLabel("M")
        logo.setObjectName("brandMark")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(48, 48)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        group = QLabel("MACLEOD SOFTWARE GROUP")
        group.setObjectName("eyebrow")
        name = QLabel("MacTorrent")
        name.setObjectName("appTitle")
        brand.addWidget(group)
        brand.addWidget(name)
        identity.addWidget(logo)
        identity.addLayout(brand)
        header.addLayout(identity)
        header.addStretch(1)
        self.connection_badge = QLabel("●  READY")
        self.connection_badge.setObjectName("readyBadge")
        header.addWidget(self.connection_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        root_layout.addLayout(header)

        intro = QHBoxLayout()
        intro_text = QVBoxLayout()
        intro_text.setSpacing(4)
        heading = QLabel("Your transfers, at a glance.")
        heading.setObjectName("sectionTitle")
        subtitle = QLabel("A clear view of everything moving in and out.")
        subtitle.setObjectName("mutedLabel")
        intro_text.addWidget(heading)
        intro_text.addWidget(subtitle)
        intro.addLayout(intro_text)
        intro.addStretch(1)
        self.add_button = QPushButton("+   Add torrent")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_torrent)
        intro.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignBottom)
        root_layout.addLayout(intro)

        self.stat_values: dict[str, QLabel] = {}
        stats = QHBoxLayout()
        stats.setSpacing(12)
        for key, title, initial in (
            ("active", "ACTIVE TORRENTS", "0"),
            ("down", "DOWNLOAD SPEED", "0 KB/s"),
            ("up", "UPLOAD SPEED", "0 KB/s"),
            ("complete", "COMPLETED", "0"),
        ):
            card = QFrame()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 15, 18, 15)
            card_layout.setSpacing(8)
            label = QLabel(title)
            label.setObjectName("statLabel")
            value = QLabel(initial)
            value.setObjectName("statValue")
            self.stat_values[key] = value
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            stats.addWidget(card, 1)
        root_layout.addLayout(stats)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(9)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search torrents…")
        self.search_input.textChanged.connect(self.filter_torrents)
        toolbar.addWidget(self.search_input, 1)
        for text, name, slot in (
            ("Pause", "secondaryButton", self.pause_selected),
            ("Resume", "secondaryButton", self.resume_selected),
            ("Remove", "dangerButton", self.remove_selected),
            ("Clear completed", "secondaryButton", self.clear_completed),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.clicked.connect(slot)
            toolbar.addWidget(button)
        all_menu = QMenu(self)
        all_menu.addAction("Pause all torrents", self.pause_all)
        all_menu.addAction("Resume all torrents", self.resume_all)
        all_button = QPushButton("All torrents  ▾")
        all_button.setObjectName("secondaryButton")
        all_button.setMenu(all_menu)
        toolbar.addWidget(all_button)
        root_layout.addLayout(toolbar)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(62)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(84)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 112)
        self.table.setColumnWidth(3, 112)
        self.table.setColumnWidth(4, 126)
        self.table.setSortingEnabled(False)

        self.empty_state = QWidget()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.addStretch(1)
        self.empty_title = QLabel("Nothing downloading yet")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_copy = QLabel(
            "Add a torrent file or magnet link to get started.\n"
            "You can also drop a .torrent file anywhere in this window."
        )
        self.empty_copy.setObjectName("mutedLabel")
        self.empty_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_copy.setWordWrap(True)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_copy)
        empty_layout.addStretch(1)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.table)
        self.content_stack.addWidget(self.empty_state)
        root_layout.addWidget(self.content_stack, 1)

        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Downloads are saved to {self.download_path}")

    def setup_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f4f7fb;
                color: #17253a;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QFrame#statCard, QTableWidget, QWidget#emptyState {
                background: #ffffff;
                border: 1px solid #e5eaf1;
                border-radius: 12px;
            }
            QLabel#brandMark {
                background: #143653;
                color: #5ee0c4;
                border-radius: 12px;
                font-size: 21pt;
                font-weight: 700;
            }
            QLabel#eyebrow, QLabel#statLabel {
                color: #74849a;
                font-size: 8pt;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#appTitle {
                color: #13243a;
                font-size: 17pt;
                font-weight: 700;
            }
            QLabel#sectionTitle, QLabel#dialogTitle {
                color: #14253c;
                font-size: 17pt;
                font-weight: 700;
            }
            QLabel#dialogTitle { font-size: 16pt; }
            QLabel#mutedLabel { color: #718198; }
            QLabel#readyBadge {
                background: #e8f7f3;
                color: #17745f;
                border: 1px solid #c8ece2;
                border-radius: 12px;
                padding: 7px 12px;
                font-size: 8pt;
                font-weight: 700;
            }
            QLabel#statValue {
                color: #172a42;
                font-size: 19pt;
                font-weight: 700;
            }
            QLabel#fieldLabel {
                color: #43546a;
                font-size: 9pt;
                font-weight: 600;
            }
            QLabel#emptyTitle {
                color: #24364d;
                font-size: 15pt;
                font-weight: 700;
                padding: 8px;
            }
            QPushButton {
                min-height: 36px;
                padding: 0 14px;
                border: 1px solid #dbe3ed;
                border-radius: 8px;
                background: #ffffff;
                color: #304258;
                font-weight: 600;
            }
            QPushButton:hover { background: #f2f6fb; border-color: #becbda; }
            QPushButton:pressed { background: #e9eff6; }
            QPushButton#primaryButton {
                min-height: 42px;
                padding: 0 18px;
                border: none;
                background: #176b70;
                color: #ffffff;
                font-size: 10pt;
            }
            QPushButton#primaryButton:hover { background: #12595e; }
            QPushButton#secondaryButton { background: #ffffff; }
            QPushButton#dangerButton {
                background: #ffffff;
                color: #a33c48;
                border-color: #edd7da;
            }
            QPushButton#dangerButton:hover {
                background: #fff4f4;
                border-color: #dfb5ba;
            }
            QLineEdit {
                min-height: 38px;
                padding: 0 12px;
                border: 1px solid #dbe3ed;
                border-radius: 8px;
                background: #ffffff;
                color: #203149;
                selection-background-color: #c6e9e1;
            }
            QLineEdit:focus { border: 1px solid #4ba99c; }
            QTableWidget {
                border: 1px solid #e5eaf1;
                outline: 0;
                selection-background-color: #e4f3f1;
                selection-color: #152b40;
            }
            QTableWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #eff2f6;
            }
            QTableWidget::item:selected { background: #e4f3f1; }
            QHeaderView::section {
                background: #f8fafc;
                color: #74849a;
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid #e8edf3;
                font-size: 8pt;
                font-weight: 700;
            }
            QProgressBar {
                min-height: 14px;
                max-height: 14px;
                border: none;
                border-radius: 7px;
                background: #e9eef4;
                color: #466077;
                text-align: center;
                font-size: 8pt;
            }
            QProgressBar::chunk {
                border-radius: 7px;
                background: #25a18e;
            }
            QStatusBar {
                background: #f4f7fb;
                color: #718198;
                border-top: 1px solid #e5eaf1;
                font-size: 9pt;
            }
            QDialog { background: #f4f7fb; }
            QDialogButtonBox QPushButton { min-width: 88px; }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(
            url.isLocalFile() and url.toLocalFile().lower().endswith(".torrent")
            for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        added = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if url.isLocalFile() and file_path.lower().endswith(".torrent"):
                self.add_torrent_file(file_path, self.download_path)
                added = True
        if added:
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_torrent(self) -> None:
        dialog = AddTorrentDialog(self.download_path, self)
        if not dialog.exec():
            return
        method, source, save_path = dialog.get_result()
        if not source:
            QMessageBox.warning(
                self, "Torrent source required", "Choose a torrent file or enter a magnet link."
            )
            return
        if not save_path:
            QMessageBox.warning(
                self, "Download folder required", "Choose where MacTorrent should save files."
            )
            return
        try:
            resolved_path = self._prepare_save_path(save_path)
        except OSError as error:
            QMessageBox.critical(
                self, "Download folder unavailable", f"Could not use this folder:\n{error}"
            )
            return

        if method == "file":
            self.add_torrent_file(source, resolved_path)
        else:
            self.add_magnet_link(source, resolved_path)

    def add_torrent_file(self, file_path: str, save_path: str) -> None:
        try:
            path = Path(file_path).expanduser().resolve(strict=True)
            if not path.is_file() or path.suffix.lower() != ".torrent":
                raise ValueError("Choose a valid .torrent file.")
            save_path = self._prepare_save_path(save_path)
            torrent_info = lt.torrent_info(str(path))
            handle = self.session.add_torrent(
                {
                    "ti": torrent_info,
                    "save_path": save_path,
                    "storage_mode": lt.storage_mode_t.storage_mode_sparse,
                }
            )
            self.add_to_table(handle, torrent_info.name(), save_path, str(path))
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Could not add torrent", str(error))

    def add_magnet_link(self, magnet_link: str, save_path: str) -> None:
        if not re.match(r"^magnet:\?", magnet_link, re.IGNORECASE):
            QMessageBox.warning(
                self, "Invalid magnet link", "Paste a valid magnet link beginning with magnet:?"
            )
            return
        try:
            save_path = self._prepare_save_path(save_path)
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = save_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse
            handle = self.session.add_torrent(params)
            self.add_to_table(
                handle,
                "Retrieving metadata…",
                save_path,
                magnet_link,
            )
            self.status_bar.showMessage("Magnet link added; retrieving torrent metadata…", 5000)
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Could not add magnet link", str(error))

    def _prepare_save_path(self, save_path: str) -> str:
        directory = Path(save_path).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        resolved_path = str(directory.resolve())
        self.download_path = resolved_path
        self.settings.setValue("download_path", resolved_path)
        return resolved_path

    def add_to_table(
        self, handle: object, name: str, save_path: str, source: str
    ) -> None:
        entry = TorrentEntry(handle, name, save_path, source)
        self.torrents.append(entry)
        self.table.insertRow(self.table.rowCount())
        row = self.table.rowCount() - 1
        name_item = QTableWidgetItem(name)
        name_item.setToolTip(name)
        self.table.setItem(row, 0, name_item)
        progress = QProgressBar()
        progress.setRange(0, 1000)
        progress.setValue(0)
        progress.setFormat("0%")
        self.table.setCellWidget(row, 1, progress)
        for column in (2, 3, 4, 5):
            self.table.setItem(row, column, QTableWidgetItem("—"))
        self.table.item(row, 5).setToolTip(save_path)
        self.content_stack.setCurrentWidget(self.table)
        self.update_progress()

    def selected_rows(self) -> list[int]:
        return sorted({index.row() for index in self.table.selectionModel().selectedRows()})

    def pause_selected(self) -> None:
        for row in self.selected_rows():
            if row < len(self.torrents):
                self._pause(self.torrents[row])
        self.update_progress()

    def resume_selected(self) -> None:
        for row in self.selected_rows():
            if row < len(self.torrents):
                self._resume(self.torrents[row])
        self.update_progress()

    def pause_all(self) -> None:
        for entry in self.torrents:
            self._pause(entry)
        self.update_progress()

    def resume_all(self) -> None:
        for entry in self.torrents:
            self._resume(entry)
        self.update_progress()

    @staticmethod
    def _pause(entry: TorrentEntry) -> None:
        if entry.handle.is_valid():
            entry.handle.pause()

    @staticmethod
    def _resume(entry: TorrentEntry) -> None:
        if entry.handle.is_valid():
            entry.handle.resume()

    def remove_selected(self) -> None:
        rows = self.selected_rows()
        if not rows:
            self.status_bar.showMessage("Select one or more torrents to remove.", 4000)
            return
        for row in reversed(rows):
            if row < len(self.torrents):
                entry = self.torrents.pop(row)
                if entry.handle.is_valid():
                    self.session.remove_torrent(entry.handle)
                self.table.removeRow(row)
        self._show_content()
        self.update_progress()
        self.status_bar.showMessage("Selected torrents removed. Downloaded files were kept.", 5000)

    def clear_completed(self) -> None:
        rows = [
            row
            for row, entry in enumerate(self.torrents)
            if self._is_complete(entry)
        ]
        for row in reversed(rows):
            entry = self.torrents.pop(row)
            if entry.handle.is_valid():
                self.session.remove_torrent(entry.handle)
            self.table.removeRow(row)
        self._show_content()
        self.update_progress()
        if rows:
            self.status_bar.showMessage(
                f"Removed {len(rows)} completed torrent(s). Downloaded files were kept.", 5000
            )
        else:
            self.status_bar.showMessage("There are no completed torrents to clear.", 4000)

    def filter_torrents(self, query: str) -> None:
        term = query.strip().casefold()
        visible_rows = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            matches = not term or (item is not None and term in item.text().casefold())
            self.table.setRowHidden(row, not matches)
            visible_rows += int(matches)
        if not self.torrents:
            self.empty_title.setText("Nothing downloading yet")
            self.empty_copy.setText(
                "Add a torrent file or magnet link to get started.\n"
                "You can also drop a .torrent file anywhere in this window."
            )
            self.content_stack.setCurrentWidget(self.empty_state)
        elif visible_rows == 0:
            self.empty_title.setText("No matching torrents")
            self.empty_copy.setText("Try a different name or clear the search.")
            self.content_stack.setCurrentWidget(self.empty_state)
        else:
            self.content_stack.setCurrentWidget(self.table)

    def _show_content(self) -> None:
        if not self.torrents:
            self.content_stack.setCurrentWidget(self.empty_state)
        else:
            self.filter_torrents(self.search_input.text())

    @staticmethod
    def _is_complete(entry: TorrentEntry) -> bool:
        if not entry.handle.is_valid():
            return False
        try:
            return entry.handle.status().progress >= 1.0
        except RuntimeError:
            return False

    @staticmethod
    def _format_size(size: int) -> str:
        units = ("B", "KB", "MB", "GB", "TB")
        value = float(max(0, size))
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    @staticmethod
    def _get_state(status: object) -> str:
        if status.paused:
            return "Paused"
        if status.progress >= 1.0:
            return (
                "Seeding"
                if status.state == getattr(lt.torrent_status.states, "seeding", None)
                else "Completed"
            )
        state_labels = (
            ("checking_files", "Checking files"),
            ("checking_resume_data", "Checking files"),
            ("downloading_metadata", "Retrieving metadata"),
            ("downloading", "Downloading"),
            ("finished", "Completed"),
            ("seeding", "Seeding"),
            ("queued_for_checking", "Queued"),
            ("queued_for_download", "Queued"),
            ("queued_for_seed", "Queued"),
            ("allocating", "Preparing files"),
            ("moving_storage", "Moving files"),
        )
        states = lt.torrent_status.states
        for state_name, label in state_labels:
            state_value = getattr(states, state_name, None)
            if state_value is not None and status.state == state_value:
                return label
        return "Connecting"

    def update_progress(self) -> None:
        total_down = 0
        total_up = 0
        complete = 0
        active = 0
        invalid_rows: list[int] = []

        for row, entry in enumerate(self.torrents):
            if not entry.handle.is_valid():
                invalid_rows.append(row)
                continue
            try:
                status = entry.handle.status()
            except RuntimeError:
                invalid_rows.append(row)
                continue

            if status.has_metadata and entry.name == "Retrieving metadata…":
                entry.name = status.name
                self.table.item(row, 0).setText(entry.name)
            progress = max(0.0, min(1.0, float(status.progress)))
            down = max(0, int(status.download_rate))
            up = max(0, int(status.upload_rate))
            total_down += down
            total_up += up
            state = self._get_state(status)
            complete += int(progress >= 1.0)
            active += int(not status.paused)

            progress_bar = self.table.cellWidget(row, 1)
            if isinstance(progress_bar, QProgressBar):
                progress_bar.setValue(round(progress * 1000))
                progress_bar.setFormat(f"{progress * 100:.1f}%")
            self.table.item(row, 2).setText(f"{self._format_size(down)}/s")
            self.table.item(row, 3).setText(f"{self._format_size(up)}/s")
            state_item = self.table.item(row, 4)
            state_item.setText(state)
            state_item.setForeground(
                QColor("#17745f" if state in ("Completed", "Seeding") else "#52657b")
            )
            self.table.item(row, 5).setText(entry.save_path)
            wanted = int(getattr(status, "total_wanted", 0))
            done = int(getattr(status, "total_wanted_done", 0))
            name_item = self.table.item(row, 0)
            name_item.setToolTip(
                f"{entry.name}\n{self._format_size(done)} of {self._format_size(wanted)}"
                f"\nSaved to: {entry.save_path}"
            )

        for row in reversed(invalid_rows):
            if row < len(self.torrents):
                self.torrents.pop(row)
                self.table.removeRow(row)

        self.stat_values["active"].setText(str(active))
        self.stat_values["down"].setText(f"{self._format_size(total_down)}/s")
        self.stat_values["up"].setText(f"{self._format_size(total_up)}/s")
        self.stat_values["complete"].setText(str(complete))
        if self.torrents:
            self.connection_badge.setText("●  RUNNING")
            self.connection_badge.setObjectName("readyBadge")
        else:
            self.connection_badge.setText("●  READY")
        self._show_content()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MacTorrent")
    app.setOrganizationName("Macleod Software Group")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(make_app_icon())

    splash = QSplashScreen(make_splash_pixmap())
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    window = TorrentClient()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
