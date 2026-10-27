# Free Proxy Scraper

Desktop app for **Windows** and **Linux** that pulls the latest public proxy list from [ProxyScrape](https://proxyscrape.com/free-proxy-list) and shows it in a clean purple-on-black UI.

Pair it with **[Free Proxy Checker](https://github.com/aonpa/Free-Proxy-Checker/)** to test which proxies actually work.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/theme-purple%20%26%20black-8b5cf6?style=for-the-badge" alt="Theme" />
  <img src="https://img.shields.io/badge/source-ProxyScrape-030008?style=for-the-badge" alt="Source" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge" alt="License" />
</p>

## Features

- **Fresh lists** from ProxyScrape’s public API (the same dataset as [their free proxy page](https://proxyscrape.com/free-proxy-list)), refreshed continuously
- **Protocol filter** — All, HTTP, HTTPS, SOCKS4, or SOCKS5
- **Table view** — protocol, IP, port, country, anonymity, and latency, with live search
- **Smooth overlay** while fetching, with a clickable link to Free Proxy Checker
- **Export & copy** — save as `.txt` or copy the full list (`protocol://ip:port`)
- **Auto-fetch on launch** so the window opens with the newest list

## Download (no Python required)

Pre-built binaries are on **[GitHub Releases](https://github.com/aonpa/Free-Proxy-Scraper/releases)**. Push a version tag (`v1.0.0`, …) or run the **Release** workflow from the Actions tab.

| Platform | File |
|----------|------|
| Windows | `FreeProxyScraper-Windows.exe` |
| Linux | `FreeProxyScraper-Linux` |

1. Open **Releases** on this repository.
2. Download the file for your OS.
3. **Windows:** run the `.exe`.
4. **Linux:** `chmod +x FreeProxyScraper-Linux` then `./FreeProxyScraper-Linux`.

> On Windows, SmartScreen may warn on first run — choose *More info* → *Run anyway* if you downloaded from this repo’s Releases.

## Run from source

### Requirements

- Python **3.11** or newer
- Internet access (lists are fetched from `api.proxyscrape.com`)

### Install

```bash
git clone https://github.com/aonpa/Free-Proxy-Scraper.git
cd Free-Proxy-Scraper
python -m pip install -r requirements.txt
```

### Start the app

```bash
python main.py
```

## How to use

1. Choose a **Protocol** in the sidebar, or leave **All**.
2. Click **Fetch latest list** (this also runs when the app starts).
3. While the list is downloading, a centered overlay explains how to verify proxies and links to [Free Proxy Checker](https://github.com/aonpa/Free-Proxy-Checker/) — click the button to open the repo in your browser.
4. Browse the table. Use the filter box, click a column header to sort, or double-click a row to copy that proxy.
5. Use **Export to file** or **Copy all** when you are ready.

## Check proxies

Scraped entries are **public and unverified**. Test them with:

**https://github.com/aonpa/Free-Proxy-Checker/**

1. Export the list from this app.
2. Open Free Proxy Checker and load the file.
3. Run a scan and export the working set.

## Data source

Official ProxyScrape public API:

```
https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json
```

This app does not scrape the HTML page; it uses the documented JSON endpoint (up to 6,000 rows, fastest first). Public proxies can go stale quickly — always verify before you rely on them.

## Publish a release (maintainers)

```bash
git tag v1.0.0
git push origin v1.0.0
```

Or: **Actions** → **Release** → **Run workflow** and enter a tag name.

Artifacts:

- `FreeProxyScraper-Windows.exe` — windowed one-file build
- `FreeProxyScraper-Linux` — one-file binary

CI also builds on every push to `main` / `master` (artifacts only, no GitHub Release).

## Related projects

| Project | Description |
|---------|-------------|
| [Free Proxy Checker](https://github.com/aonpa/Free-Proxy-Checker/) | Test proxy lists in parallel and export valid / invalid results |
| [ProxyScrape free list](https://proxyscrape.com/free-proxy-list) | Source site and public API |

## License

MIT — see [LICENSE](LICENSE).
