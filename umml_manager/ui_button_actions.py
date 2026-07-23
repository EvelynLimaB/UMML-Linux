from __future__ import annotations

import webbrowser
from tkinter import messagebox

from .studio import open_path


class ButtonStateActions:
    """Keep visible button state aligned with the existing action backends.

    Backend validation remains authoritative. This layer records whether an action
    is semantically available so temporary busy-state disabling can be reversed
    correctly when a background task completes.
    """

    def browse_gamebanana(self):
        signature = (
            self.gb_region.get().strip().casefold(),
            self.gb_sort.get().strip().casefold(),
            self.gb_query.get().strip(),
        )
        previous = getattr(self, "_gb_browse_signature", None)
        if previous != signature:
            self.gb_page = 1
            self._gb_browse_signature = signature
        return super().browse_gamebanana()

    def _clear_gamebanana_selection(self):
        self._gb_install_enabled = False
        self._gb_install_text = "Install"
        result = super()._clear_gamebanana_selection()
        self.refresh_action_states()
        return result

    def _show_gamebanana_page(self, page):
        result = super()._show_gamebanana_page(page)
        self._gb_can_previous = page.page > 1
        self._gb_can_next = bool(page.has_more)
        self.refresh_action_states()
        return result

    def select_gamebanana_mod(self):
        result = super().select_gamebanana_mod()
        self.refresh_action_states()
        return result

    def _configure_gamebanana_files(
        self,
        mod,
        *,
        details_complete: bool,
        loading: bool = False,
    ) -> None:
        if mod.files:
            self._gb_install_enabled = True
            self._gb_install_text = "Install"
        elif details_complete:
            self._gb_install_enabled = False
            self._gb_install_text = "No files"
        else:
            self._gb_install_enabled = True
            self._gb_install_text = "Install latest"
        super()._configure_gamebanana_files(
            mod,
            details_complete=details_complete,
            loading=loading,
        )
        self.refresh_action_states()

    def _show_local_candidates(self, candidates):
        result = super()._show_local_candidates(candidates)
        self.refresh_action_states()
        return result

    def open_gamebanana_page(self):
        selected = self.gb_selected
        if selected is None or str(selected.id) not in self.gb_results:
            self.status.set("Select a GameBanana mod before opening its page")
            self.refresh_action_states()
            return
        try:
            opened = webbrowser.open(selected.profile_url)
        except Exception as exc:
            messagebox.showerror(
                "Could not open GameBanana",
                str(exc),
                parent=self.root,
            )
            return
        if not opened:
            messagebox.showwarning(
                "Browser did not open",
                "No desktop web browser accepted the GameBanana page request.",
                parent=self.root,
            )

    def open_local_candidate(self):
        candidate = self.selected_local_candidate()
        if candidate is None:
            self.status.set("Select a detected package before opening its location")
            self.refresh_action_states()
            return
        target = candidate.path.parent if candidate.kind == "archive" else candidate.path
        try:
            open_path(target)
        except Exception as exc:
            messagebox.showerror(
                "Could not open location",
                str(exc),
                parent=self.root,
            )

    def import_local_candidate(self):
        if self.selected_local_candidate() is None:
            self.status.set("Select a detected package before importing it")
            self.refresh_action_states()
            return
        return super().import_local_candidate()
