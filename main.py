import math
import queue
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlencode

import customtkinter as ctk
import requests

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

BG = "#030008"
SURFACE = "#0e051a"
SURFACE_ALT = "#120820"
BORDER = "#1e1b4b"
ACCENT = "#8b5cf6"
ACCENT_HOVER = "#7c3aed"
ACCENT_SOFT = "#a78bfa"
DANGER = "#ef4444"
MUTED = "#94a3b8"
SUCCESS = "#22c55e"
FONT_UI = ("Segoe UI", 12)
FONT_UI_BOLD = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_MONO = ("Consolas", 11)

CHECKER_REPO = "https://github.com/aonpa/Free-Proxy-Checker/"
SCRAPER_REPO = "https://github.com/aonpa/Free-Proxy-Scraper"
API_BASE = "https://api.proxyscrape.com/v4/free-proxy-list/get"
PAGE_SIZE = 2000
MAX_PAGES = 3
OVERLAY_MIN_SECONDS = 2.2


def blend_hex(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = (int(a.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    br, bg, bb = (int(b.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


class PulseCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            height=72,
            highlightthickness=0,
            bd=0,
            bg=SURFACE_ALT,
            **kwargs,
        )
        self._phase = 0.0
        self.bind("<Configure>", lambda _e: self.draw())

    def tick(self, dt: float = 0.04) -> None:
        self._phase = (self._phase + dt) % (math.pi * 2)
        self.draw()

    def draw(self) -> None:
        w = max(self.winfo_width(), 2)
        h = max(self.winfo_height(), 2)
        self.delete("all")
        cx, cy = w / 2, h / 2
        for i in range(4):
            wave = (math.sin(self._phase + i * 0.7) + 1) / 2
            r = 10 + i * 9 + wave * 8
            color = blend_hex(ACCENT, SURFACE_ALT, 0.15 + i * 0.18)
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2)
        core = 7 + 3 * math.sin(self._phase * 1.4)
        self.create_oval(cx - core, cy - core, cx + core, cy + core, fill=ACCENT, outline="")


class ProxyScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Free Proxy Scraper")
        self.geometry("1100x760")
        self.minsize(920, 640)
        self.configure(fg_color=BG)

        self.proxies: list[dict] = []
        self._fetching = False
        self._ui_queue: queue.Queue = queue.Queue()
        self._overlay_visible = False
        self._overlay_opened_at = 0.0
        self._pending_promo = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_overlay()
        self.after(40, self._poll_ui)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=248, fg_color=SURFACE, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=24, pady=(28, 20))
        ctk.CTkLabel(brand, text="Free", font=FONT_TITLE, text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Proxy Scraper",
            font=("Segoe UI", 11),
            text_color=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=(0, 12))

        proto_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        proto_frame.pack(pady=6, padx=20, fill="x")
        ctk.CTkLabel(proto_frame, text="Protocol", text_color=MUTED, font=FONT_UI).pack(anchor="w")
        self.protocol_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            proto_frame,
            values=["All", "HTTP", "HTTPS", "SOCKS4", "SOCKS5"],
            variable=self.protocol_var,
            fg_color=BG,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=SURFACE_ALT,
            font=FONT_UI,
        ).pack(fill="x", pady=(4, 0))

        btn_style = {
            "corner_radius": 14,
            "height": 42,
            "font": FONT_UI_BOLD,
            "fg_color": ACCENT,
            "hover_color": ACCENT_HOVER,
        }
        self.btn_fetch = ctk.CTkButton(
            self.sidebar,
            text="Fetch latest list",
            command=self.start_fetch,
            **btn_style,
        )
        self.btn_fetch.pack(pady=(14, 6), padx=20, fill="x")

        export_style = {
            **btn_style,
            "fg_color": SURFACE_ALT,
            "hover_color": BORDER,
            "border_width": 1,
            "border_color": BORDER,
            "font": FONT_UI,
        }
        ctk.CTkButton(
            self.sidebar,
            text="Export to file",
            command=self.export_proxies,
            **export_style,
        ).pack(pady=6, padx=20, fill="x")
        ctk.CTkButton(
            self.sidebar,
            text="Copy all",
            command=self.copy_all,
            **export_style,
        ).pack(pady=4, padx=20, fill="x")

        ctk.CTkButton(
            self.sidebar,
            text="Open Proxy Checker",
            command=lambda: webbrowser.open(CHECKER_REPO),
            fg_color="transparent",
            hover_color=SURFACE_ALT,
            text_color=ACCENT_SOFT,
            font=("Segoe UI", 11, "underline"),
            height=28,
        ).pack(side="bottom", pady=(8, 4))
        ctk.CTkLabel(
            self.sidebar,
            text="github.com/aonpa/Free-Proxy-Scraper",
            font=("Segoe UI", 10),
            text_color="#4c4668",
        ).pack(side="bottom", pady=(0, 16))

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        header_row = ctk.CTkFrame(main, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(
            header_row,
            text="Live proxy list",
            font=("Segoe UI", 20, "bold"),
            text_color="#e2e8f0",
        ).pack(side="left")
        self.status_chip = ctk.CTkLabel(
            header_row,
            text="  Ready  ",
            font=("Segoe UI", 11),
            text_color=MUTED,
            fg_color=SURFACE,
            corner_radius=20,
        )
        self.status_chip.pack(side="right")

        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        self.stat_count = self._stat_card(stats, "Proxies", "0", 0, ACCENT)
        self.stat_countries = self._stat_card(stats, "Countries", "—", 1)
        self.stat_source = self._stat_card(stats, "Source", "ProxyScrape", 2)
        self.stat_updated = self._stat_card(stats, "Last fetch", "—", 3, MUTED)

        search_row = ctk.CTkFrame(main, fg_color="transparent")
        search_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        search_row.grid_columnconfigure(0, weight=1)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render_rows())
        ctk.CTkEntry(
            search_row,
            textvariable=self.search_var,
            placeholder_text="Filter by IP, country, protocol…",
            fg_color=SURFACE,
            border_color=BORDER,
            height=36,
            font=FONT_UI,
        ).grid(row=0, column=0, sticky="ew")

        list_shell = ctk.CTkFrame(
            main, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER
        )
        list_shell.grid(row=3, column=0, sticky="nsew")
        list_shell.grid_columnconfigure(0, weight=1)
        list_shell.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            list_shell,
            text="Double-click a row to copy that proxy",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        table_host = tk.Frame(list_shell, bg=BG, highlightthickness=0)
        table_host.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        table_host.grid_columnconfigure(0, weight=1)
        table_host.grid_rowconfigure(0, weight=1)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Proxy.Treeview",
            background=BG,
            foreground="#e2e8f0",
            fieldbackground=BG,
            rowheight=28,
            font=FONT_MONO,
            borderwidth=0,
        )
        style.configure(
            "Proxy.Treeview.Heading",
            background=SURFACE,
            foreground=ACCENT_SOFT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Proxy.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")],
        )
        style.layout("Proxy.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        columns = ("protocol", "ip", "port", "country", "anonymity", "latency")
        self.tree = ttk.Treeview(
            table_host,
            columns=columns,
            show="headings",
            style="Proxy.Treeview",
            selectmode="browse",
        )
        headings = {
            "protocol": "Protocol",
            "ip": "IP",
            "port": "Port",
            "country": "Country",
            "anonymity": "Anonymity",
            "latency": "Latency",
        }
        widths = {"protocol": 90, "ip": 160, "port": 70, "country": 150, "anonymity": 110, "latency": 90}
        for key, title in headings.items():
            self.tree.heading(key, text=title, command=lambda k=key: self._sort_by(k))
            self.tree.column(key, width=widths[key], anchor="w")

        yscroll = ttk.Scrollbar(table_host, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._copy_selected)
        self._sort_column = "latency"
        self._sort_reverse = False

    def _stat_card(self, parent, title, value, col, value_color="#e2e8f0"):
        card = ctk.CTkFrame(
            parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 10), text_color=MUTED).pack(
            anchor="w", padx=14, pady=(12, 0)
        )
        val = ctk.CTkLabel(
            card, text=value, font=("Segoe UI", 18, "bold"), text_color=value_color
        )
        val.pack(anchor="w", padx=14, pady=(2, 12))
        return val

    def _build_overlay(self):
        self.dimmer = ctk.CTkFrame(self, fg_color="#020006", corner_radius=0)
        self.overlay = ctk.CTkFrame(self, fg_color="transparent")

        glow = ctk.CTkFrame(self.overlay, fg_color=ACCENT, corner_radius=24)
        glow.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.64, relheight=0.58)
        self.overlay_glow = glow

        card = ctk.CTkFrame(
            self.overlay,
            fg_color=SURFACE_ALT,
            corner_radius=20,
            border_width=2,
            border_color=BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.62, relheight=0.56)
        self.overlay_card = card

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=36, pady=28)

        self.pulse = PulseCanvas(inner)
        self.pulse.pack(fill="x", pady=(0, 8))

        self.overlay_title = ctk.CTkLabel(
            inner,
            text="Fetching the latest proxies",
            font=("Segoe UI", 20, "bold"),
            text_color="#f1f5f9",
            justify="center",
        )
        self.overlay_title.pack(pady=(4, 10))

        self.overlay_body = ctk.CTkLabel(
            inner,
            text=(
                "To check these proxies, use Free Proxy Checker —\n"
                "a desktop tool for Windows and Linux."
            ),
            font=("Segoe UI", 14),
            text_color=MUTED,
            justify="center",
        )
        self.overlay_body.pack(pady=(0, 16))

        self.overlay_link = ctk.CTkButton(
            inner,
            text="github.com/aonpa/Free-Proxy-Checker",
            command=lambda: webbrowser.open(CHECKER_REPO),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=FONT_UI_BOLD,
            corner_radius=12,
            height=42,
        )
        self.overlay_link.pack(fill="x", pady=(0, 8))

        self.overlay_dismiss = ctk.CTkButton(
            inner,
            text="Got it",
            command=self._hide_overlay,
            fg_color="transparent",
            hover_color=BORDER,
            text_color=MUTED,
            font=FONT_UI,
            height=32,
        )

    def _show_overlay(self, ready: bool = False):
        self._overlay_visible = True
        if not ready:
            self._overlay_opened_at = time.monotonic()
            self.overlay_title.configure(text="Fetching the latest proxies")
            self.overlay_dismiss.pack_forget()
        else:
            self.overlay_title.configure(text="List ready")
            if not self.overlay_dismiss.winfo_ismapped():
                self.overlay_dismiss.pack(pady=(4, 0))
        self.dimmer.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.dimmer.lift()
        self.overlay.lift()

    def _hide_overlay(self):
        self._overlay_visible = False
        self._pending_promo = False
        self.overlay.place_forget()
        self.dimmer.place_forget()

    def _tick_overlay(self):
        if not self._overlay_visible:
            return
        self.pulse.tick(0.05)
        pulse = (math.sin(time.monotonic() * 2.2) + 1) / 2
        self.overlay_glow.configure(fg_color=blend_hex(ACCENT, "#3b0764", 0.35 + pulse * 0.4))
        self.overlay_card.configure(
            border_color=blend_hex(ACCENT_SOFT, BORDER, 1.0 - pulse * 0.7)
        )
        lift = 0.5 + math.sin(time.monotonic() * 1.15) * 0.008
        self.overlay_card.place(relx=0.5, rely=lift, anchor="center", relwidth=0.62, relheight=0.56)
        self.overlay_glow.place(
            relx=0.5, rely=lift, anchor="center", relwidth=0.64, relheight=0.58
        )

    def _poll_ui(self):
        try:
            while True:
                kind, *payload = self._ui_queue.get_nowait()
                if kind == "status":
                    self._set_status(payload[0], payload[1] if len(payload) > 1 else MUTED)
                elif kind == "proxies":
                    self._apply_proxies(*payload)
                elif kind == "error":
                    self._on_fetch_error(payload[0])
                elif kind == "done":
                    self._on_fetch_done()
        except queue.Empty:
            pass
        self._tick_overlay()
        if self._pending_promo and not self._fetching:
            elapsed = time.monotonic() - self._overlay_opened_at
            if elapsed >= OVERLAY_MIN_SECONDS:
                self._pending_promo = False
                if self.proxies:
                    self._show_overlay(ready=True)
                else:
                    self._hide_overlay()
        self.after(40, self._poll_ui)

    def _set_status(self, text: str, color=MUTED):
        self.status_chip.configure(text=f"  {text}  ", text_color=color)

    def _apply_proxies(self, rows: list[dict], fetched_at: str, countries: int):
        self.proxies = rows
        self.stat_count.configure(text=f"{len(rows):,}")
        self.stat_countries.configure(text=str(countries) if countries else "—")
        self.stat_updated.configure(text=fetched_at)
        self._render_rows()

    def _filtered(self) -> list[dict]:
        q = self.search_var.get().strip().lower()
        if not q:
            return self.proxies
        out = []
        for row in self.proxies:
            hay = " ".join(
                str(row.get(k, "")).lower()
                for k in ("proxy", "protocol", "ip", "country", "anonymity", "port")
            )
            if q in hay:
                out.append(row)
        return out

    def _sort_by(self, column: str):
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = column != "latency"
        self._render_rows()

    def _render_rows(self):
        rows = self._filtered()
        key = self._sort_column
        numeric = key in {"port", "latency_ms"}
        if key == "latency":
            rows = sorted(rows, key=lambda r: r.get("latency_ms", 10**9), reverse=self._sort_reverse)
        else:
            rows = sorted(
                rows,
                key=lambda r: (r.get(key) if not numeric else int(r.get(key) or 0)) or "",
                reverse=self._sort_reverse,
            )
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            tag = "odd" if i % 2 else "even"
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    row.get("protocol", ""),
                    row.get("ip", ""),
                    row.get("port", ""),
                    row.get("country", ""),
                    row.get("anonymity", ""),
                    row.get("latency", ""),
                ),
                tags=(tag, row.get("proxy", "")),
            )
        self.tree.tag_configure("even", background=BG)
        self.tree.tag_configure("odd", background=SURFACE)

    def _copy_selected(self, _event=None):
        item = self.tree.focus()
        if not item:
            return
        tags = self.tree.item(item, "tags")
        proxy = tags[1] if len(tags) > 1 else ""
        if not proxy:
            vals = self.tree.item(item, "values")
            if len(vals) >= 3:
                proxy = f"{vals[0]}://{vals[1]}:{vals[2]}"
        if proxy:
            self.clipboard_clear()
            self.clipboard_append(proxy)
            self._set_status("Copied", SUCCESS)

    def start_fetch(self):
        if self._fetching:
            return
        self._fetching = True
        self._pending_promo = False
        self.btn_fetch.configure(state="disabled", text="Fetching…")
        self._set_status("Fetching", ACCENT)
        self._show_overlay(ready=False)
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _request_params(self, skip: int) -> dict:
        proto = self.protocol_var.get().lower()
        params = {
            "request": "display_proxies",
            "proxy_format": "protocolipport",
            "format": "json",
            "limit": PAGE_SIZE,
            "skip": skip,
        }
        if proto == "https":
            params["protocol"] = "http"
            params["ssl"] = "yes"
        elif proto != "all":
            params["protocol"] = proto
        return params

    def _fetch_worker(self):
        try:
            collected: list[dict] = []
            total_countries = 0
            for page in range(MAX_PAGES):
                url = f"{API_BASE}?{urlencode(self._request_params(page * PAGE_SIZE))}"
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                payload = resp.json()
                total_countries = payload.get("total_countries") or total_countries
                batch = payload.get("proxies") or []
                collected.extend(batch)
                if not payload.get("nextpage") or len(batch) < PAGE_SIZE:
                    break
            rows = [self._normalize(item) for item in collected if item]
            rows = [r for r in rows if r.get("proxy")]
            rows.sort(key=lambda r: r.get("latency_ms", 10**9))
            stamp = datetime.now().strftime("%H:%M:%S")
            self._ui_queue.put(("proxies", rows, stamp, total_countries))
            self._ui_queue.put(("status", "Ready", MUTED))
        except Exception as exc:
            self._ui_queue.put(("error", str(exc)))
        finally:
            self._ui_queue.put(("done",))

    @staticmethod
    def _normalize(item: dict) -> dict:
        ip_data = item.get("ip_data") or {}
        timeout = item.get("timeout")
        try:
            latency_ms = float(timeout)
        except (TypeError, ValueError):
            latency_ms = 10**9
        latency = f"{int(latency_ms)} ms" if latency_ms < 10**8 else "—"
        return {
            "proxy": item.get("proxy") or "",
            "protocol": str(item.get("protocol") or "").lower(),
            "ip": item.get("ip") or "",
            "port": item.get("port") or "",
            "country": ip_data.get("country") or item.get("country") or "—",
            "anonymity": item.get("anonymity") or "—",
            "latency": latency,
            "latency_ms": latency_ms,
        }

    def _on_fetch_error(self, message: str):
        self._hide_overlay()
        self._set_status("Error", DANGER)
        messagebox.showerror(
            "Free Proxy Scraper",
            f"Could not fetch proxies.\n\n{message}",
        )

    def _on_fetch_done(self):
        self._fetching = False
        self.btn_fetch.configure(state="normal", text="Fetch latest list")
        if self.proxies:
            self._pending_promo = True
        else:
            self._hide_overlay()

    def _proxy_lines(self) -> list[str]:
        return [row["proxy"] for row in self.proxies if row.get("proxy")]

    def export_proxies(self):
        lines = self._proxy_lines()
        if not lines:
            messagebox.showwarning("Free Proxy Scraper", "Fetch a proxy list first.")
            return
        path = filedialog.asksaveasfilename(
            initialfile="proxies.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Free Proxy Scraper - {SCRAPER_REPO}\n")
            f.write(f"# Verify with Free Proxy Checker - {CHECKER_REPO}\n")
            f.write("# ----------------------------------------------\n")
            f.write("\n".join(lines))
            f.write("\n")

    def copy_all(self):
        lines = self._proxy_lines()
        if not lines:
            messagebox.showwarning("Free Proxy Scraper", "Nothing to copy yet.")
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self._set_status("Copied", SUCCESS)


if __name__ == "__main__":
    app = ProxyScraperApp()
    app.after(280, app.start_fetch)
    app.mainloop()
