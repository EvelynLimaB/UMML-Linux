from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .ui_theme import SURFACE, SURFACE_2, TEXT, MUTED


class LibraryPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(0, 0, 0, 10))
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Profile").grid(row=0, column=0, padx=(0, 7))
        self.profile_box = ttk.Combobox(toolbar, textvariable=app.profile_name, state="readonly", width=22)
        self.profile_box.grid(row=0, column=1, sticky="w")
        self.profile_box.bind("<<ComboboxSelected>>", lambda _e: app.refresh())
        ttk.Button(toolbar, text="New profile", command=app.new_profile).grid(row=0, column=2, padx=4)
        ttk.Entry(toolbar, textvariable=app.search_library, width=26).grid(row=0, column=3, padx=(14, 4))
        ttk.Button(toolbar, text="Search", command=app.refresh).grid(row=0, column=4)
        ttk.Button(toolbar, text="Import folder", command=app.import_folder).grid(row=0, column=5, padx=(14, 4))
        ttk.Button(toolbar, text="Import archive", command=app.import_archive).grid(row=0, column=6, padx=4)

        left = ttk.Frame(self, style="Surface.TFrame", padding=10)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 7))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(left, columns=("order", "version", "source", "state"), show="tree headings", selectmode="browse")
        for column, title, width in (("#0", "Mod", 280), ("order", "Order", 70), ("version", "Version", 90), ("source", "Source", 100), ("state", "State", 120)):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="center" if column != "#0" else "w")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: app.show_selected_mod())
        self.tree.bind("<Double-1>", lambda _e: app.toggle_mod())

        details = ttk.Frame(self, style="Surface.TFrame", padding=16)
        details.grid(row=1, column=1, sticky="nsew", padx=(7, 0))
        details.columnconfigure(0, weight=1)
        details.rowconfigure(4, weight=1)
        self.mod_title = ttk.Label(details, text="Select a mod", style="CardTitle.TLabel")
        self.mod_title.grid(row=0, column=0, sticky="w")
        self.mod_meta = ttk.Label(details, text="", style="SurfaceMuted.TLabel")
        self.mod_meta.grid(row=1, column=0, sticky="w", pady=(3, 10))
        self.mod_state = ttk.Label(details, text="", style="Badge.TLabel")
        self.mod_state.grid(row=2, column=0, sticky="w", pady=(0, 10))
        self.description = tk.Text(details, wrap="word", height=12, background=SURFACE_2, foreground=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0, padx=10, pady=10)
        self.description.grid(row=4, column=0, sticky="nsew")
        self.description.configure(state="disabled")
        buttons = ttk.Frame(details, style="Surface.TFrame")
        buttons.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Enable / disable", command=app.toggle_mod).pack(side="left")
        ttk.Button(buttons, text="↑", width=3, command=lambda: app.move_mod(-1)).pack(side="left", padx=(6, 2))
        ttk.Button(buttons, text="↓", width=3, command=lambda: app.move_mod(1)).pack(side="left", padx=2)
        ttk.Button(buttons, text="Prepare", command=app.prepare_selected).pack(side="left", padx=(8, 2))
        ttk.Button(buttons, text="Edit copy", command=app.create_workspace).pack(side="left", padx=2)
        ttk.Button(buttons, text="Remove", style="Danger.TButton", command=app.remove_selected).pack(side="right")

        actions = ttk.Frame(self, padding=(0, 10, 0, 0))
        actions.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(actions, text="Preview conflicts", command=app.show_plan).pack(side="left")
        ttk.Button(actions, text="Apply profile", style="Accent.TButton", command=app.apply_profile).pack(side="right")

    def selected_id(self):
        selected = self.tree.selection()
        return selected[0] if selected else None

    def set_description(self, value: str) -> None:
        self.description.configure(state="normal")
        self.description.delete("1.0", "end")
        self.description.insert("1.0", value)
        self.description.configure(state="disabled")
