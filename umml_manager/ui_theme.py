from __future__ import annotations

from tkinter import ttk

BACKGROUND = "#111019"
SIDEBAR = "#191725"
SURFACE = "#242131"
SURFACE_2 = "#2e2a3e"
TEXT = "#f5f1fb"
MUTED = "#b8afc6"
ACCENT = "#9b78e2"
ACCENT_ACTIVE = "#ad8cf0"
SUCCESS = "#72d3a3"
WARNING = "#efc66f"
DANGER = "#ef8291"


def configure_theme(root) -> None:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    root.configure(background=BACKGROUND)
    style.configure(".", background=BACKGROUND, foreground=TEXT, fieldbackground=SURFACE_2)
    style.configure("TFrame", background=BACKGROUND)
    style.configure("Sidebar.TFrame", background=SIDEBAR)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("TLabel", background=BACKGROUND, foreground=TEXT, font=("TkDefaultFont", 10))
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Surface.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("SurfaceMuted.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("Title.TLabel", font=("TkDefaultFont", 21, "bold"))
    style.configure("PageTitle.TLabel", font=("TkDefaultFont", 17, "bold"))
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=TEXT, font=("TkDefaultFont", 11, "bold"))
    style.configure("Badge.TLabel", background=SURFACE_2, foreground=TEXT, padding=(9, 4), font=("TkDefaultFont", 9, "bold"))
    style.configure("Good.Badge.TLabel", background="#204535", foreground=SUCCESS, padding=(9, 4), font=("TkDefaultFont", 9, "bold"))
    style.configure("Warning.Badge.TLabel", background="#4c3d22", foreground=WARNING, padding=(9, 4), font=("TkDefaultFont", 9, "bold"))
    style.configure("TButton", background=SURFACE_2, foreground=TEXT, padding=(10, 7), borderwidth=0)
    style.map("TButton", background=[("active", "#3a354b"), ("pressed", "#454057")])
    style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", padding=(12, 8), font=("TkDefaultFont", 10, "bold"))
    style.map("Accent.TButton", background=[("active", ACCENT_ACTIVE), ("disabled", "#625a70")])
    style.configure("Danger.TButton", foreground=DANGER)
    style.configure("Nav.TButton", background=SIDEBAR, foreground=MUTED, anchor="w", padding=(18, 11), borderwidth=0)
    style.map("Nav.TButton", background=[("active", SURFACE)], foreground=[("active", TEXT)])
    style.configure("Active.Nav.TButton", background=SURFACE, foreground=TEXT, anchor="w", padding=(18, 11), font=("TkDefaultFont", 10, "bold"))
    style.configure("TLabelframe", background=SURFACE, foreground=TEXT, borderwidth=0, relief="flat")
    style.configure("TLabelframe.Label", background=SURFACE, foreground=TEXT, font=("TkDefaultFont", 10, "bold"))
    style.configure("TEntry", fieldbackground=SURFACE_2, foreground=TEXT, insertcolor=TEXT, borderwidth=0, padding=7)
    style.configure("TCombobox", fieldbackground=SURFACE_2, background=SURFACE_2, foreground=TEXT, arrowcolor=TEXT, padding=6)
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT, rowheight=30, borderwidth=0)
    style.configure("Treeview.Heading", background=SURFACE_2, foreground=TEXT, relief="flat", padding=7, font=("TkDefaultFont", 9, "bold"))
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])
    style.configure("TNotebook", background=BACKGROUND, borderwidth=0)
    style.configure("TNotebook.Tab", background=SURFACE_2, foreground=MUTED, padding=(14, 8))
    style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])
    style.configure("Horizontal.TProgressbar", troughcolor=SURFACE_2, background=ACCENT)
