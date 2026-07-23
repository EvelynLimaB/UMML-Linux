from __future__ import annotations

import webbrowser
from tkinter import messagebox

from .deployment import ApplyEngine
from .studio import open_path


class ButtonStateActions:
    """Keep visible button state aligned with the existing action backends.

    Backend validation remains authoritative. This layer records whether an action
    is semantically available so temporary busy-state disabling can be reversed
    correctly when a background task completes.
    """

    def _refresh_game_status(self):
        result = super()._refresh_game_status()
        if self.game_status.get() == "Game status unknown":
            self._game_running = True
            self.game_status.set("Game status unknown; writes blocked")
            self.refresh_action_states()
        return result

    def apply_profile(self):
        """Apply through the complete fail-closed deployment boundary."""

        if getattr(self, "_game_running", False):
            messagebox.showwarning(
                "Close the game first",
                "Close Umamusume before applying a profile.",
                parent=self.root,
            )
            return
        if not self.dat_path.get().strip():
            messagebox.showinfo(
                "Game data required",
                "Run installation auto-detection in Settings first.",
                parent=self.root,
            )
            return
        resolution = self.current_resolution()
        if resolution.blocking_issues:
            messagebox.showwarning(
                "Profile is not ready",
                "The profile was not applied. Open Conflicts for the complete "
                f"list of {len(resolution.blocking_issues)} blocking issue(s).",
                parent=self.root,
            )
            self.show_page("conflicts")
            return

        def operation():
            return ApplyEngine(
                self.store,
                self.dat_path.get(),
                game_dir=self.game_dir.get() or None,
            ).apply(resolution)

        def finished(result):
            recovery = (
                f"; recovered {result.recovered_transactions} interrupted "
                "transaction(s)"
                if result.recovered_transactions
                else ""
            )
            messagebox.showinfo(
                "Profile applied",
                f"Installed {result.installed}; restored {result.restored}; "
                f"unchanged {result.unchanged}{recovery}",
                parent=self.root,
            )
            self.status.set(f"Applied {resolution.profile}")
            self.refresh_action_states()

        self._run_task(
            "Applying profile transactionally…",
            operation,
            finished,
        )

    def save_settings(self, silent: bool = False):
        """Clear stale installation verification after typed path/region edits."""

        try:
            saved = self.store.load_settings()
        except Exception:
            saved = {}
        saved_target = (
            str(saved.get("dat_path", "")),
            str(saved.get("meta_path", "")),
            str(saved.get("game_dir", "")),
            str(saved.get("region", "global")),
        )
        current_target = (
            self.dat_path.get(),
            self.meta_path.get(),
            self.game_dir.get(),
            self.region.get(),
        )
        detected_save = self.installation_status.get().startswith("Detected ")
        had_verified_identity = bool(
            saved.get("installation_key") or saved.get("metadata_fingerprint")
        )
        if (
            had_verified_identity
            and current_target != saved_target
            and not detected_save
        ):
            self.installation_key.set("")
            self.metadata_fingerprint.set("")
            self.installation_status.set(
                "Manual target changes were saved. Auto-detect again to restore "
                "verified installation identity and metadata fingerprinting."
            )
        return super().save_settings(silent=silent)

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
