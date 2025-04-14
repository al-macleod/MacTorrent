#!/usr/bin/env python3
import sys
import libtorrent as lt
import time
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit, QRadioButton,
    QDialogButtonBox, QDialog, QStatusBar, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent

__version__ = "1.0.0"
__author__ = "Macleods Torrent Team"

class AddTorrentDialog(QDialog):
    """Dialog for adding a torrent via file or magnet link."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Torrent")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Torrent type selection
        self.file_radio = QRadioButton("Torrent File")
        self.magnet_radio = QRadioButton("Magnet Link")
        self.file_radio.setChecked(True)
        layout.addWidget(QLabel("<b>Select Torrent Source:</b>"))
        layout.addWidget(self.file_radio)
        layout.addWidget(self.magnet_radio)

        # Magnet link input
        self.magnet_input = QLineEdit()
        self.magnet_input.setPlaceholderText("Enter magnet link (e.g., magnet:?xt=urn:btih:...)")
        self.magnet_input.setEnabled(False)
        layout.addWidget(self.magnet_input)

        # Save path input
        self.save_path_input = QLineEdit()
        self.save_path_input.setText("./downloads/")
        self.save_path_input.setPlaceholderText("Enter download directory")
        self.save_path_button = QPushButton("Browse")
        self.save_path_button.clicked.connect(self.browse_save_path)
        save_path_layout = QHBoxLayout()
        save_path_layout.addWidget(self.save_path_input)
        save_path_layout.addWidget(self.save_path_button)
        layout.addWidget(QLabel("<b>Download Directory:</b>"))
        layout.addLayout(save_path_layout)

        # Connect signals
        self.magnet_radio.toggled.connect(self.toggle_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def toggle_input(self):
        """Enable/disable magnet link input based on radio button selection."""
        self.magnet_input.setEnabled(self.magnet_radio.isChecked())

    def browse_save_path(self):
        """Open a directory dialog to select the save path."""
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", "./")
        if path:
            self.save_path_input.setText(path)

    def get_result(self):
        """Return the selected method, data, and save path."""
        method = "file" if self.file_radio.isChecked() else "magnet"
        data = None if method == "file" else self.magnet_input.text()
        save_path = self.save_path_input.text()
        return method, data, save_path

class TorrentClient(QMainWindow):
    """Main window for the Macleods Torrent Client."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Macleods Torrent Client v{__version__}")
        self.setMinimumSize(800, 400)
        self.setAcceptDrops(True)

        # Initialize libtorrent session
        alert_mask = (
            lt.alert.category_t.error_notification |
            lt.alert.category_t.peer_notification |
            lt.alert.category_t.port_mapping_notification |
            lt.alert.category_t.storage_notification |
            lt.alert.category_t.tracker_notification |
            lt.alert.category_t.status_notification
        )
        self.session = lt.session({
            'alert_mask': alert_mask,
            'enable_dht': True,
            'enable_lsd': True,
            'enable_natpmp': True,
            'enable_upnp': True,
            'listen_interfaces': '0.0.0.0:6881'  # Listen on port 6881
        })
        self.torrents = []

        self.setup_ui()
        self.setup_stylesheet()

        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)

    def setup_ui(self):
        """Set up the main UI components."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        main_widget.setLayout(layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        buttons = [
            ("Add Torrent", self.add_torrent),
            ("Remove Torrent", self.remove_torrent),
            ("Pause All", self.pause_all),
            ("Resume All", self.resume_all),
            ("Clear Completed", self.clear_completed)
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)
        layout.addLayout(button_layout)

        # Torrent table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Progress", "Down Speed", "Up Speed", "Status"])
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def setup_stylesheet(self):
        """Apply a Tailwind CSS-inspired stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9fafb;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #bfdbfe;
                color: black;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 8px;
                border: 1px solid #e5e7eb;
                font-weight: 500;
            }
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QRadioButton {
                padding: 4px;
            }
            QDialog {
                background-color: #f9fafb;
            }
            QLabel {
                color: #1f2937;
                font-weight: 500;
            }
            QStatusBar {
                background-color: #f3f4f6;
                color: #1f2937;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for .torrent files."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.torrent'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events for .torrent files."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.torrent'):
                self.add_torrent_file(file_path, "./downloads/")
        event.acceptProposedAction()

    def add_torrent(self):
        """Open the Add Torrent dialog."""
        dialog = AddTorrentDialog(self)
        if dialog.exec():
            method, data, save_path = dialog.get_result()
            if method == "file":
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select Torrent File", "", "Torrent Files (*.torrent)"
                )
                if file_path:
                    self.add_torrent_file(file_path, save_path)
            elif method == "magnet" and data:
                if self.validate_magnet_link(data):
                    self.add_magnet_link(data, save_path)
                else:
                    QMessageBox.warning(self, "Invalid Magnet Link", "Please enter a valid magnet link.")

    def validate_magnet_link(self, magnet_link):
        """Validate the magnet link format."""
        return bool(re.match(r'^magnet:\?xt=urn:[a-z0-9]+:[a-zA-Z0-9]+', magnet_link))

    def add_torrent_file(self, file_path, save_path):
        """Add a torrent from a .torrent file."""
        try:
            torrent_info = lt.torrent_info(file_path)
            torrent_handle = self.session.add_torrent({
                'ti': torrent_info,
                'save_path': save_path,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse
            })
            self.add_to_table(torrent_handle, torrent_info.name())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add torrent file: {str(e)}")

    def add_magnet_link(self, magnet_link, save_path):
        """Add a torrent from a magnet link."""
        try:
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = save_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse
            torrent_handle = self.session.add_torrent(params)
            name = "Fetching metadata..."
            while not torrent_handle.has_metadata() and torrent_handle.is_valid():
                time.sleep(0.1)
                alerts = self.session.pop_alerts()
                for alert in alerts:
                    if isinstance(alert, lt.torrent_added_alert) and alert.handle == torrent_handle:
                        name = torrent_handle.status().name
                        break
            if torrent_handle.has_metadata():
                name = torrent_handle.torrent_file().name()
            self.add_to_table(torrent_handle, name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add magnet link: {str(e)}")

    def add_to_table(self, torrent_handle, name):
        """Add a torrent to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem("0%"))
        self.table.setItem(row, 2, QTableWidgetItem("0 KB/s"))
        self.table.setItem(row, 3, QTableWidgetItem("0 KB/s"))
        self.table.setItem(row, 4, QTableWidgetItem("Downloading"))
        self.torrents.append(torrent_handle)

    def update_progress(self):
        """Update torrent progress, speed, and status."""
        total_down_speed = 0
        total_up_speed = 0
        for row, handle in enumerate(self.torrents[:]):
            if handle.is_valid():
                status = handle.status()
                progress = status.progress * 100
                down_speed = status.download_rate / 1024
                up_speed = status.upload_rate / 1024
                total_down_speed += down_speed
                total_up_speed += up_speed
                self.table.setItem(row, 1, QTableWidgetItem(f"{progress:.1f}%"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{down_speed:.1f} KB/s"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{up_speed:.1f} KB/s"))
                self.table.setItem(row, 4, QTableWidgetItem(self.get_status_text(status)))
            else:
                self.torrents.pop(row)
                self.table.removeRow(row)
        self.status_bar.showMessage(
            f"Down: {total_down_speed:.1f} KB/s | Up: {total_up_speed:.1f} KB/s | Torrents: {len(self.torrents)}"
        )

    def get_status_text(self, status):
        """Return the appropriate status text based on torrent state."""
        if status.paused:
            return "Paused"
        elif status.progress == 1.0:
            return "Completed"
        elif status.state == lt.torrent_status.states.checking_files:
            return "Checking"
        elif status.state == lt.torrent_status.states.downloading_metadata:
            return "Fetching Metadata"
        else:
            return "Downloading"

    def remove_torrent(self):
        """Remove the selected torrent."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a torrent to remove.")
            return
        row = selected_rows[0].row()
        handle = self.torrents[row]
        if handle.is_valid():
            self.session.remove_torrent(handle, 0)  # 0 = don't delete files
        self.torrents.pop(row)
        self.table.removeRow(row)

    def pause_all(self):
        """Pause all torrents."""
        for handle in self.torrents:
            if handle.is_valid():
                handle.pause()
        self.status_bar.showMessage("All torrents paused")

    def resume_all(self):
        """Resume all torrents."""
        for handle in self.torrents:
            if handle.is_valid():
                handle.resume()
        self.status_bar.showMessage("All torrents resumed")

    def clear_completed(self):
        """Remove completed torrents from the table."""
        for row in reversed(range(self.table.rowCount())):
            if self.table.item(row, 4).text() == "Completed":
                handle = self.torrents[row]
                if handle.is_valid():
                    self.session.remove_torrent(handle, 0)
                self.torrents.pop(row)
                self.table.removeRow(row)
        self.status_bar.showMessage("Completed torrents cleared")

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))  # Assumes icon.ico exists in the same directory
    window = TorrentClient()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
