from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .discovery import default_search_roots
from .providers.gamebanana import GameBananaMod
from .store import ManagerStore, default_root
from .ui_discover import DiscoverPage
from .ui_discover_actions import DiscoverActions
from .ui_library import LibraryPage
from .ui_library_actions import LibraryActions
from .ui_settings import SettingsPage
from .ui_studio import StudioPage
from .ui_system_actions import SystemActions
from .ui_theme import BACKGROUND, SURFACE, TEXT, configure_theme


class ManagerGUI(LibraryActions, DiscoverActions, SystemActions):
    def __init__(self, root: tk.Tk, store: ManagerStore | None = None):
        self.root = root
        self.store = store or ManagerStore(default_root())
        settings = self.store.load_settings()
        self.profile_name = tk.StringVar(value=str(settings.get("profile", "Default")))
        self.dat_path = tk.StringVar(value=str(settings.get("dat_path", "")))
        self.meta_path = tk.StringVar(value=str(settings.get("meta_path", "")))
        self.game_dir = tk.StringVar(value=str(settings.get("game_dir", "")))
        self.region = tk.StringVar(value=str(settings.get("region", "global")))
        self.search_library = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.page_title = tk.StringVar(value="Library")
        self.game_status = tk.StringVar(value="Game status: checking…")
        self.gb_region = tk.StringVar(value=str(settings.get("gamebanana_region", self.region.get())))
        self.gb_sort = tk.StringVar(value="updated")
        self.gb_query = tk.StringVar()
        self.gb_page = 1
        self.gb_results: dict[str, GameBananaMod] = {}
        self.gb_selected: GameBananaMod | None = None
        roots = settings.get("scan_roots") or [str(path) for path in default_search_roots()]
        self.scan_roots = tk.StringVar(value="; ".join(str(item) for item in roots))
        self.local_candidates = {}
        self._busy = False
        self._nav_buttons = {}

        root.title("UMML Manager")
        root.geometry("1220x780")
        root.minsize(980, 650)
        root.configure(background=BACKGROUND)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        configure_theme(root)
        self._build_header()
        self._build_body()
        self._build_footer()
        self.refresh()
        self.show_page("library")
        self._refresh_game_status()

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(22, 15, 22, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="UMML", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.page_title, style="PageTitle.TLabel").grid(row=0, column=1, sticky="w", padx=(16, 0))
        badges = ttk.Frame(header)
        badges.grid(row=0, column=2, sticky="e")
        self.profile_badge = ttk.Label(badges, text="Profile: Default", style="Badge.TLabel")
        self.profile_badge.pack(side="left", padx=4)
        self.game_badge = ttk.Label(badges, textvariable=self.game_status, style="Warning.Badge.TLabel")
        self.game_badge.pack(side="left", padx=4)

    def _build_body(self):
        body = ttk.Frame(self.root)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(body, style="Sidebar.TFrame", padding=(10, 18))
        sidebar.grid(row=0, column=0, sticky="ns")
        for key, label in (("library", "Library"), ("discover", "Discover"), ("studio", "Studio"), ("conflicts", "Conflicts"), ("settings", "Settings")):
            button = ttk.Button(sidebar, text=label, style="Nav.TButton", width=18, command=lambda item=key: self.show_page(item))
            button.pack(fill="x", pady=2)
            self._nav_buttons[key] = button
        ttk.Separator(sidebar).pack(fill="x", pady=14)
        ttk.Button(sidebar, text="Run diagnostics", style="Nav.TButton", command=self.run_diagnostics).pack(fill="x")

        self.content = ttk.Frame(body, padding=(18, 8, 22, 18))
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.library = LibraryPage(self.content, self)
        self.discover = DiscoverPage(self.content, self)
        self.studio = StudioPage(self.content, self)
        self.conflicts = self._build_conflicts_page()
        self.settings = SettingsPage(self.content, self)
        self.pages = {"library": self.library, "discover": self.discover, "studio": self.studio, "conflicts": self.conflicts, "settings": self.settings}
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _build_conflicts_page(self):
        page = ttk.Frame(self.content)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        top = ttk.Frame(page)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(top, text="Resolved profile plan and file ownership", style="Muted.TLabel").pack(side="left")
        ttk.Button(top, text="Refresh plan", style="Accent.TButton", command=self.render_plan).pack(side="right")
        self.plan_text = tk.Text(page, wrap="none", background=SURFACE, foreground=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0, padx=12, pady=12, font=("TkFixedFont", 10))
        self.plan_text.grid(row=1, column=0, sticky="nsew")
        self.plan_text.configure(state="disabled")
        return page

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding=(22, 7, 22, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=210)
        self.progress.grid(row=0, column=1, sticky="e")

    def show_page(self, key: str):
        self.pages[key].tkraise()
        self.page_title.set(key.title())
        for name, button in self._nav_buttons.items():
            button.configure(style="Active.Nav.TButton" if name == key else "Nav.TButton")
        if key == "conflicts":
            self.render_plan()

    @staticmethod
    def _set_text(widget: tk.Text, value: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    ManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
