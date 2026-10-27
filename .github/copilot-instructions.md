# Free Proxy Scraper

Python + CustomTkinter GUI in `main.py`.

- Entry: `python main.py`
- Dependencies: `requirements.txt`
- CI builds PyInstaller artifacts in `.github/workflows/build.yml`
- Releases (Windows + Linux) are published by `.github/workflows/release.yml`

Network fetches run on a background thread. UI updates go through `queue` + `after()`.
