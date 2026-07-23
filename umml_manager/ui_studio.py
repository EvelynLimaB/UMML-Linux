from __future__ import annotations

from tkinter import ttk

from .studio import LEGACY_TOOLS


class StudioPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.tool_buttons = {}
        self.tool_mutating = {}
        self.columnconfigure(0, weight=1)
        ttk.Label(
            self,
            text=(
                "All legacy editing features remain available through the "
                "compatibility Studio. The legacy host requires the game to be "
                "closed because it contains mutating callbacks even when opened at "
                "the full workspace."
            ),
            style="Muted.TLabel",
            wraplength=850,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        cards = ttk.Frame(self)
        cards.grid(row=1, column=0, sticky="nsew")
        for column in range(2):
            cards.columnconfigure(column, weight=1)
        for index, tool in enumerate(LEGACY_TOOLS):
            card = ttk.Frame(cards, style="Surface.TFrame", padding=15)
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0 if index % 2 == 0 else 7, 7 if index % 2 == 0 else 0),
                pady=6,
            )
            card.columnconfigure(0, weight=1)
            ttk.Label(card, text=tool.name, style="CardTitle.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(
                card,
                text=tool.description,
                style="SurfaceMuted.TLabel",
                wraplength=380,
            ).grid(row=1, column=0, sticky="w", pady=(4, 10))
            button = ttk.Button(
                card,
                text="Open",
                style="Accent.TButton" if tool.id == "full" else "TButton",
                command=lambda item=tool: app.launch_legacy_tool(item.id),
            )
            button.grid(row=2, column=0, sticky="w")
            self.tool_buttons[tool.id] = button
            # Every card launches the same compatibility host. Its lifetime watcher
            # closes the entire host when Umamusume runs, including the full workspace.
            self.tool_mutating[tool.id] = True
