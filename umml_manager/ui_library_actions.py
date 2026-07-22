from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

from .engine import ApplyEngine
from .legacy_adapter import LegacyAssetAdapter
from .models import Profile
from .resolver import resolve_profile
from .studio import open_path


class LibraryActions:
    def profile(self) -> Profile:
        try:
            return self.store.get_profile(self.profile_name.get())
        except Exception:
            profile = Profile(self.profile_name.get() or "Default", [])
            self.store.save_profile(profile)
            return profile

    def selected_id(self):
        return self.library.selected_id()

    def refresh(self):
        profiles = self.store.list_profiles()
        if not profiles:
            self.store.save_profile(Profile("Default", []))
            profiles = self.store.list_profiles()
        names = [item.name for item in profiles]
        self.library.profile_box.configure(values=names)
        if self.profile_name.get() not in names:
            self.profile_name.set(names[0])
        profile = self.profile()
        self.profile_badge.configure(text=f"Profile: {profile.name}")
        order = {mod_id: index + 1 for index, mod_id in enumerate(profile.enabled)}
        needle = self.search_library.get().casefold().strip()
        mods = self.store.list_mods()
        if needle:
            mods = [
                mod
                for mod in mods
                if needle
                in f"{mod.name} {mod.author} {mod.id} {mod.description}".casefold()
            ]
        mods.sort(key=lambda mod: (order.get(mod.id, 10**9), mod.name.casefold()))
        tree = self.library.tree
        tree.delete(*tree.get_children())
        for mod in mods:
            tree.insert(
                "",
                "end",
                iid=mod.id,
                text=mod.name,
                values=(
                    order.get(mod.id, "off"),
                    mod.version,
                    mod.source.provider,
                    "prepared" if mod.files else "needs prepare",
                ),
            )
        self.status.set(
            f"{len(mods)} mod(s); {len(profile.enabled)} enabled in {profile.name}"
        )
        self.save_settings(silent=True)

    def show_selected_mod(self):
        mod_id = self.selected_id()
        if not mod_id:
            return
        mod = self.store.get_mod(mod_id)
        self.library.mod_title.configure(text=mod.name)
        self.library.mod_meta.configure(
            text=f"{mod.author or 'Unknown author'} • {mod.version} • {mod.source.provider}"
        )
        enabled = mod_id in self.profile().enabled
        self.library.mod_state.configure(
            text=("Enabled" if enabled else "Disabled")
            + (" • prepared" if mod.files else " • needs preparation")
        )
        self.library.set_description(
            mod.description or "No description was supplied by this package."
        )

    def new_profile(self):
        name = simpledialog.askstring(
            "New profile", "Profile name:", parent=self.root
        )
        if name and name.strip():
            self.store.save_profile(Profile(name.strip(), []))
            self.profile_name.set(name.strip())
            self.refresh()

    def toggle_mod(self):
        mod_id = self.selected_id()
        if not mod_id:
            return
        profile = self.profile()
        profile.enabled = (
            [item for item in profile.enabled if item != mod_id]
            if mod_id in profile.enabled
            else profile.enabled + [mod_id]
        )
        self.store.save_profile(profile)
        self.refresh()
        if self.library.tree.exists(mod_id):
            self.library.tree.selection_set(mod_id)
            self.show_selected_mod()

    def move_mod(self, delta: int):
        mod_id = self.selected_id()
        profile = self.profile()
        if not mod_id or mod_id not in profile.enabled:
            return
        old = profile.enabled.index(mod_id)
        new = max(0, min(len(profile.enabled) - 1, old + delta))
        profile.enabled.pop(old)
        profile.enabled.insert(new, mod_id)
        self.store.save_profile(profile)
        self.refresh()
        self.library.tree.selection_set(mod_id)

    def import_folder(self):
        path = filedialog.askdirectory(parent=self.root)
        if path:
            self._import(lambda: self.store.import_folder(path))

    def import_archive(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            filetypes=(
                ("Supported archives", "*.zip *.tar *.tar.gz *.tgz"),
                ("All files", "*"),
            ),
        )
        if path:
            self._import(lambda: self.store.import_archive(path))

    def _import(self, operation):
        self._run_task("Importing mod…", operation, self._finish_import)

    def _finish_import(self, record):
        self.refresh()
        if self.library.tree.exists(record.id):
            self.library.tree.selection_set(record.id)
            self.library.tree.see(record.id)
            self.show_selected_mod()
        self.status.set(f"Imported {record.name}")
        self.show_page("library")

    def prepare_selected(self):
        mod_id = self.selected_id()
        if not mod_id:
            return
        if not self.meta_path.get().strip():
            messagebox.showinfo(
                "Metadata required",
                "Run installation auto-detection in Settings first.",
                parent=self.root,
            )
            return
        self._run_task(
            f"Preparing {mod_id}…",
            lambda: LegacyAssetAdapter(self.store, self.meta_path.get()).prepare(
                self.store.get_mod(mod_id)
            ),
            lambda record: (
                self.refresh(),
                self.status.set(f"Prepared {len(record.files)} asset(s)"),
            ),
        )

    def create_workspace(self):
        mod_id = self.selected_id()
        if not mod_id:
            return
        try:
            path = self.store.create_workspace(mod_id)
            open_path(path)
            self.status.set(f"Editable copy created at {path}")
        except Exception as exc:
            messagebox.showerror("Workspace failed", str(exc), parent=self.root)

    def remove_selected(self):
        mod_id = self.selected_id()
        if not mod_id:
            return
        if any(mod_id in profile.enabled for profile in self.store.list_profiles()):
            messagebox.showwarning(
                "Mod is enabled",
                "Disable this mod in every profile before removing it.",
                parent=self.root,
            )
            return
        if messagebox.askyesno(
            "Remove mod",
            f"Remove {mod_id} from the manager registry? Preserved source files are not deleted.",
            parent=self.root,
        ):
            self.store.remove_mod(mod_id)
            self.refresh()

    def render_plan(self):
        resolution = resolve_profile(self.profile(), self.store.list_mods())
        lines = [
            f"PROFILE     {resolution.profile}",
            f"FILES       {len(resolution.winners)}",
            f"CONFLICTS   {len(resolution.conflicts)}",
            f"UNPREPARED  {len(resolution.unprepared)}",
            "",
        ]
        if resolution.missing:
            lines.append("Missing mods: " + ", ".join(resolution.missing))
        if resolution.unprepared:
            lines.append(
                "Enabled but not prepared: " + ", ".join(resolution.unprepared)
            )
            lines.append("These mods block deployment until they are prepared.\n")
        if resolution.conflicts:
            lines.extend(("Conflict winners", "=" * 72))
            for conflict in resolution.conflicts:
                lines.append(
                    f"{conflict.path}\n  winner: {conflict.winner}\n"
                    f"  overrides: {', '.join(conflict.overridden)}\n"
                )
        elif not resolution.unprepared and not resolution.missing:
            lines.append("No file conflicts in this profile.")
        self._set_text(self.plan_text, "\n".join(lines))

    def show_plan(self):
        self.show_page("conflicts")

    def apply_profile(self):
        if not self.dat_path.get().strip():
            messagebox.showinfo(
                "Game data required",
                "Run installation auto-detection in Settings first.",
                parent=self.root,
            )
            return
        resolution = resolve_profile(self.profile(), self.store.list_mods())
        if resolution.missing or resolution.unprepared:
            details = []
            if resolution.missing:
                details.append("Missing: " + ", ".join(resolution.missing))
            if resolution.unprepared:
                details.append("Needs preparation: " + ", ".join(resolution.unprepared))
            messagebox.showwarning(
                "Profile is not ready",
                "The profile was not applied.\n\n" + "\n".join(details),
                parent=self.root,
            )
            self.show_page("conflicts")
            return
        operation = lambda: ApplyEngine(
            self.store,
            self.dat_path.get(),
            game_dir=self.game_dir.get() or None,
        ).apply(resolution)

        def finished(result):
            messagebox.showinfo(
                "Profile applied",
                f"Installed {result.installed}; restored {result.restored}; unchanged {result.unchanged}",
                parent=self.root,
            )
            self.status.set(f"Applied {resolution.profile}")

        self._run_task("Applying profile transactionally…", operation, finished)
