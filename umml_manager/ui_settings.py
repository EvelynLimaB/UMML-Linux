from __future__ import annotations

from tkinter import ttk


class SettingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=1)
        paths = ttk.LabelFrame(self, text="Game and metadata paths", padding=14)
        paths.grid(row=0, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)
        self._row(paths, 0, "Persistent dat", app.dat_path, app.choose_dat)
        self._row(paths, 1, "Decrypted meta DB", app.meta_path, app.choose_meta)
        self._row(paths, 2, "Game directory", app.game_dir, app.choose_game_dir)
        region = ttk.Frame(paths, style="Surface.TFrame")
        region.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(region, text="Region", style="Surface.TLabel").pack(side="left")
        ttk.Combobox(region, textvariable=app.region, values=("global", "japan"), state="readonly", width=12).pack(side="left", padx=8)

        actions = ttk.Frame(self, padding=(0, 12, 0, 0))
        actions.grid(row=1, column=0, sticky="ew")
        ttk.Button(actions, text="Save settings", style="Accent.TButton", command=app.save_settings).pack(side="left")
        ttk.Button(actions, text="Run diagnostics", command=app.run_diagnostics).pack(side="left", padx=8)
        ttk.Button(actions, text="Open manager data", command=lambda: app.open_manager_path("root")).pack(side="right")
        ttk.Button(actions, text="Open workspaces", command=lambda: app.open_manager_path("workspaces")).pack(side="right", padx=8)

    @staticmethod
    def _row(parent, row, label, variable, command):
        ttk.Label(parent, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, padx=(8, 0), pady=4)
