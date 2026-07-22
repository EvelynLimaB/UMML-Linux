from __future__ import annotations

from tkinter import ttk


class SettingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=1)

        start = ttk.LabelFrame(self, text="Installation setup", padding=14)
        start.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        start.columnconfigure(0, weight=1)
        ttk.Label(
            start,
            text=(
                "UMML normally finds Steam/Proton and prepares the metadata database "
                "for you. Manual paths are only needed for unusual installations."
            ),
            style="SurfaceMuted.TLabel",
            wraplength=880,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            start,
            text="Auto-detect installation",
            style="Accent.TButton",
            command=app.autofill_installation,
        ).grid(row=0, column=1, sticky="e", padx=(16, 0))
        ttk.Label(
            start,
            textvariable=app.installation_status,
            style="Surface.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        paths = ttk.LabelFrame(self, text="Detected game and metadata paths", padding=14)
        paths.grid(row=1, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)
        self._row(
            paths,
            0,
            "Game asset data (Persistent/dat)",
            app.dat_path,
            app.choose_dat,
        )
        self._row(
            paths,
            1,
            "Prepared metadata database",
            app.meta_path,
            app.choose_meta,
        )
        self._row(
            paths,
            2,
            "Game installation directory",
            app.game_dir,
            app.choose_game_dir,
        )
        region = ttk.Frame(paths, style="Surface.TFrame")
        region.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(region, text="Region", style="Surface.TLabel").pack(side="left")
        ttk.Combobox(
            region,
            textvariable=app.region,
            values=("global", "japan", "taiwan"),
            state="readonly",
            width=12,
        ).pack(side="left", padx=8)
        ttk.Label(
            paths,
            text=(
                "The metadata field should point to UMML's readable "
                "meta_decrypted_*.db cache, not the game's encrypted file named meta."
            ),
            style="SurfaceMuted.TLabel",
            wraplength=880,
            justify="left",
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))

        actions = ttk.Frame(self, padding=(0, 12, 0, 0))
        actions.grid(row=2, column=0, sticky="ew")
        ttk.Button(
            actions,
            text="Save settings",
            style="Accent.TButton",
            command=app.save_settings,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Run diagnostics",
            command=app.run_diagnostics,
        ).pack(side="left", padx=8)
        ttk.Button(
            actions,
            text="Open manager data",
            command=lambda: app.open_manager_path("root"),
        ).pack(side="right")
        ttk.Button(
            actions,
            text="Open workspaces",
            command=lambda: app.open_manager_path("workspaces"),
        ).pack(side="right", padx=8)

    @staticmethod
    def _row(parent, row, label, variable, command):
        ttk.Label(parent, text=label, style="Surface.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", pady=4
        )
        ttk.Button(parent, text="Browse", command=command).grid(
            row=row, column=2, padx=(8, 0), pady=4
        )
