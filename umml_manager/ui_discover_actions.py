from __future__ import annotations

import webbrowser
from pathlib import Path
from tkinter import filedialog

from .discovery import ModCandidate, default_search_roots, scan_mod_candidates
from .providers.gamebanana import GameBananaClient, GameBananaPage
from .studio import open_path


class DiscoverActions:
    def browse_gamebanana(self):
        self._run_task(
            "Browsing Umamusume GameBanana…",
            lambda: GameBananaClient().browse(
                region=self.gb_region.get(),
                page=self.gb_page,
                sort=self.gb_sort.get(),
                query=self.gb_query.get(),
            ),
            self._show_gamebanana_page,
        )

    def _clear_gamebanana_selection(self):
        self.gb_selected = None
        self.discover.gb_title.configure(text="Select a mod")
        self.discover.gb_meta.configure(
            text="Choose a result to inspect its files and metadata."
        )
        self.discover.gb_stats.configure(text="")
        self.discover.set_gb_description("")
        self.discover.gb_files.configure(values=())
        self.discover.gb_files.set("")
        self.discover.open_gb_button.configure(state="disabled")
        self.discover.install_gb_button.configure(state="disabled")

    def _show_gamebanana_page(self, page: GameBananaPage):
        tree = self.discover.gb_tree
        tree.delete(*tree.get_children())
        self.gb_results = {}
        self._clear_gamebanana_selection()
        for mod in page.mods:
            key = str(mod.id)
            self.gb_results[key] = mod
            tree.insert(
                "",
                "end",
                iid=key,
                text=mod.name,
                values=(
                    mod.author,
                    mod.version or "—",
                    f"{mod.downloads:,}",
                ),
            )
        self.gb_page = page.page
        self.discover.page_label.configure(
            text=f"Page {page.page}"
            + (f" • {page.total} records" if page.total else "")
        )
        self.discover.prev_button.configure(
            state="normal" if page.page > 1 else "disabled"
        )
        self.discover.next_button.configure(
            state="normal" if page.has_more else "disabled"
        )
        self.status.set(f"Loaded {len(page.mods)} GameBanana mod(s)")

    def select_gamebanana_mod(self):
        selected = self.discover.gb_tree.selection()
        if not selected:
            self._clear_gamebanana_selection()
            return
        mod = self.gb_results.get(selected[0])
        if not mod:
            self._clear_gamebanana_selection()
            return
        self.gb_selected = mod
        self.discover.gb_title.configure(text=mod.name)
        self.discover.gb_meta.configure(
            text=f"{mod.author or 'Unknown author'} • {mod.category or 'Mod'} • "
            f"{mod.version or 'Unversioned'}"
        )
        self.discover.gb_stats.configure(
            text=f"{mod.downloads:,} downloads • {mod.likes:,} likes • {mod.views:,} views"
        )
        self.discover.set_gb_description(
            mod.description or "No description was returned by GameBanana."
        )
        self.discover.gb_files.configure(
            values=[
                f"{item.id} — {item.name} ({item.downloads:,} downloads)"
                for item in mod.files
            ]
        )
        if mod.files:
            self.discover.gb_files.current(0)
            self.discover.install_gb_button.configure(state="normal")
        else:
            self.discover.gb_files.set("")
            self.discover.install_gb_button.configure(state="disabled")
        self.discover.open_gb_button.configure(state="normal")

    def change_gamebanana_page(self, delta: int):
        target = self.gb_page + delta
        if target < 1:
            return
        self.gb_page = target
        self.browse_gamebanana()

    def install_gamebanana_mod(self):
        mod = self.gb_selected
        if not mod or str(mod.id) not in self.gb_results:
            self._clear_gamebanana_selection()
            return
        file_id = None
        selected = self.discover.gb_files.get()
        if selected:
            try:
                file_id = int(selected.split("—", 1)[0].strip())
            except ValueError:
                pass
        self._run_task(
            f"Downloading {mod.name}…",
            lambda: GameBananaClient().import_mod(
                self.store, str(mod.id), file_id=file_id
            ),
            self._finish_import,
        )

    def open_gamebanana_page(self):
        if self.gb_selected and str(self.gb_selected.id) in self.gb_results:
            webbrowser.open(self.gb_selected.profile_url)

    def add_scan_root(self):
        path = filedialog.askdirectory(parent=self.root)
        if not path:
            return
        values = [
            item.strip() for item in self.scan_roots.get().split(";") if item.strip()
        ]
        if path not in values:
            values.append(path)
            self.scan_roots.set("; ".join(values))
        self.save_settings(silent=True)

    def scan_local_mods(self):
        roots = [
            Path(item.strip()).expanduser()
            for item in self.scan_roots.get().split(";")
            if item.strip()
        ]
        self._run_task(
            "Scanning for mod folders and archives…",
            lambda: scan_mod_candidates(roots or default_search_roots()),
            self._show_local_candidates,
        )

    def _show_local_candidates(self, candidates: list[ModCandidate]):
        tree = self.discover.local_tree
        tree.delete(*tree.get_children())
        self.local_candidates = {}
        for index, candidate in enumerate(candidates):
            key = str(index)
            self.local_candidates[key] = candidate
            tree.insert(
                "",
                "end",
                iid=key,
                text=candidate.name,
                values=(
                    candidate.kind,
                    candidate.confidence,
                    candidate.reason,
                    str(candidate.path),
                ),
            )
        self.status.set(f"Detected {len(candidates)} local mod candidate(s)")

    def selected_local_candidate(self):
        selected = self.discover.local_tree.selection()
        return self.local_candidates.get(selected[0]) if selected else None

    def open_local_candidate(self):
        candidate = self.selected_local_candidate()
        if candidate:
            open_path(
                candidate.path.parent if candidate.kind == "archive" else candidate.path
            )

    def import_local_candidate(self):
        candidate = self.selected_local_candidate()
        if candidate:
            self._import(
                lambda: self.store.import_archive(candidate.path)
                if candidate.kind == "archive"
                else self.store.import_folder(candidate.path)
            )
