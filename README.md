## Macleods Torrent Client 
*Version: 1.1.0
Author: Macleods Torrent Team* 
License: MIT License

**Macleods Torrent Client** is a modern, cross-platform BitTorrent client built with Python, libtorrent, and PyQt6. It provides a user-friendly interface for managing torrent downloads, supporting both .torrent files and magnet links. Designed for performance and security, it includes advanced features like torrent prioritization, encrypted downloads, and robust error handling, making it ideal for both casual users and advanced cyber operations.
Features

Intuitive UI: Clean, Tailwind CSS-inspired interface with drag-and-drop support for .torrent files.
Torrent Management: Add, remove, pause, resume, and clear completed torrents with ease.
Magnet Link Support: Seamlessly handle magnet links with metadata fetching.
Priority Control: Set High, Normal, or Low priority for torrents to optimize bandwidth.
Security: Optional post-download encryption and strict path validation to prevent unauthorized access.
Logging: Detailed logs (mactorrent.log) for auditing and debugging.
Cross-Platform: Runs on Linux, Windows, and macOS with consistent behavior.
Configuration: Customizable settings via ~/.torrentrc (e.g., save path, port range).
Stealth: Randomized listen ports and generic naming to minimize detection.

Installation
Prerequisites

Python: 3.8 or higher
Dependencies:
libtorrent (python-libtorrent)
PyQt6


Optional:
icon.ico for custom window icon (place in the same directory)



Steps

Clone the Repository (or download mactorrent.py):
git clone https://github.com/yourusername/macleods-torrent.git
cd macleods-torrent


Install Dependencies:On Linux (e.g., Kali, Ubuntu):
sudo apt update
sudo apt install python3 python3-pip python3-libtorrent
pip3 install PyQt6

On Windows:
pip install python-libtorrent PyQt6

On macOS:
brew install libtorrent-rasterbar
pip3 install python-libtorrent PyQt6


Run the Client:
python3 mactorrent.py



Configuration
The client creates a ~/.torrentrc file on first run with default settings:
[General]
save_path = ./downloads
port_min = 6881
port_max = 6891
encrypt_downloads = false

Edit this file to customize:

save_path: Default download directory.
port_min/port_max: Range for randomized listen ports.
encrypt_downloads: Enable post-download encryption (requires additional setup).

Usage

Launch the Client:Run python3 mactorrent.py to open the main window.

Add a Torrent:

Click "Add Torrent" to open the dialog.
Choose "Torrent File" to select a .torrent file or "Magnet Link" to paste a URL.
Specify the download directory (defaults to ./downloads).
Set priority (High, Normal, Low).
Drag and drop .torrent files directly onto the window for quick addition.


Manage Torrents:

Remove Torrent: Select a torrent and click to remove (files remain on disk).
Pause/Resume All: Control all torrents at once.
Clear Completed: Remove torrents marked as "Completed".
Monitor progress, speeds, and status in the table.


View Logs:Check mactorrent.log in the working directory for detailed operation logs.


Security Notes

Private Usage: Use private networks or VPNs to mask torrent activity.
Encryption: Enable encrypt_downloads in ~/.torrentrc for sensitive files (requires external encryption tools).
Path Validation: The client prevents directory traversal attacks by resolving and validating save paths.
Logging: Logs are stored locally and contain no sensitive data by default, but secure mactorrent.log in operational environments.

Building an Executable
To create a standalone executable (e.g., for Windows):

Install PyInstaller:pip3 install pyinstaller


Run:pyinstaller --onefile --icon=icon.ico mactorrent.py


Find the executable in the dist/ directory.

Troubleshooting

libtorrent errors: Ensure python-libtorrent is installed and matches your Python version.
UI not rendering: Verify PyQt6 is installed correctly.
Port conflicts: Edit ~/.torrentrc to change port_min/port_max.
Logs: Check mactorrent.log for detailed error messages.

Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch (git checkout -b feature/YourFeature).
Commit changes (git commit -m "Add YourFeature").
Push to the branch (git push origin feature/YourFeature).
Open a Pull Request.

License
This project is licensed under the MIT License. See LICENSE for details.
Contact
For support, contact the Macleods Torrent Team at support@macleods.io (fictional for this example).

Built with security and performance in mind for advanced torrent management.
