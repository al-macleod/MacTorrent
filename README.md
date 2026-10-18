# MacTorrent

MacTorrent is a PyQt6 desktop BitTorrent client from **Macleod Software Group**.
It provides a branded startup splash, a responsive transfer dashboard, and
straightforward controls for managing torrent and magnet-link downloads.

## Features

- Add `.torrent` files, magnet links, or drop torrent files into the window.
- Monitor progress, transfer speeds, status, and destination for each torrent.
- Pause, resume, remove, or clear completed torrents individually or in batches.
- Search the current torrent list.
- Keep downloaded files when removing a torrent from the client.
- Remember the last download location between launches.
- Use native Windows download paths and the Segoe UI desktop font when available.

## Requirements

- Python 3.10 or newer
- PyQt6
- Python bindings for libtorrent (`python-libtorrent`)

Install the Python dependencies:

```powershell
py -m pip install PyQt6 python-libtorrent
```

If `py` is not available, use `python -m pip` in its place. Python-libtorrent
binary availability depends on the Python version and platform; use a supported
wheel or the platform's package manager if pip cannot install it.

## Run

From the repository directory:

```powershell
py mactorrent.py
```

MacTorrent uses the operating system's standard Downloads location and creates a
`MacTorrent` subfolder when a download is added. The last selected destination
is stored in the application settings. On Windows, settings are managed by
`QSettings` under the Macleod Software Group organization.

## Notes

- Removing a torrent removes it from the client; it does not delete downloaded
  files.
- Magnet metadata is retrieved asynchronously, so the interface stays
  responsive while peers are found.
- This client does not currently provide encryption, bandwidth scheduling,
  queue persistence, or configurable network ports.
- Only download and share content you have the right to access and distribute.
