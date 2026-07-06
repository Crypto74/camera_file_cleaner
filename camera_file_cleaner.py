"""Camera File Cleaner - delete low-resolution preview files in one go.

Cameras leave small preview files next to the real video files on the
SD card:
    .LRF - DJI low-resolution preview video
    .LRV - GoPro low-resolution preview video
    .THM - GoPro thumbnail image

These can all be deleted safely; the original videos are untouched.
Deletion is permanent.
"""

import json
import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CONFIG_FILE = Path.home() / ".camera_cleaner.json"

FILE_TYPES = [
    (".lrf", "LRF (DJI)"),
    (".lrv", "LRV (GoPro)"),
    (".thm", "THM (GoPro)"),
]


def format_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024 or unit == "TB":
            if unit == "B":
                return f"{num_bytes} {unit}"
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024


class CameraCleaner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Camera File Cleaner - LRF / LRV / THM (DJI & GoPro)")
        self.geometry("700x480")
        self.minsize(520, 320)

        self.folder = None
        self.files = []

        self._build_menu()
        self._build_ui()
        self._load_config()

        self.bind("<Control-o>", lambda e: self.open_folder())
        self.bind("<Delete>", lambda e: self.delete_all())
        self.bind("<F5>", lambda e: self.refresh())
        # re-read the folder whenever the window regains focus, so changes
        # made in Explorer or a newly inserted SD card show up automatically
        self.bind("<FocusIn>", self._on_focus)

    # ------------------------------------------------------------ UI
    def _build_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", accelerator="Ctrl+O",
                             command=self.open_folder)
        filemenu.add_separator()
        filemenu.add_command(label="Delete", accelerator="Del",
                             command=self.delete_all)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 8, 8, 0))
        top.pack(fill="x")
        self.folder_var = tk.StringVar(value="No folder selected")
        ttk.Label(top, textvariable=self.folder_var).pack(side="left")

        typebar = ttk.Frame(self, padding=(8, 6, 8, 0))
        typebar.pack(fill="x")
        ttk.Label(typebar, text="File types:").pack(side="left")
        self.type_vars = {}
        for ext, label in FILE_TYPES:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(typebar, text=label, variable=var,
                            command=self._types_changed
                            ).pack(side="left", padx=(10, 0))
            self.type_vars[ext] = var

        bottom = ttk.Frame(self, padding=(8, 4, 8, 8))
        bottom.pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(value="0 files")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")
        self.delete_btn = ttk.Button(bottom, text="Delete all listed files",
                                     command=self.delete_all,
                                     state="disabled")
        self.delete_btn.pack(side="right")

        frame = ttk.Frame(self, padding=8)
        frame.pack(side="top", fill="both", expand=True)

        columns = ("size", "modified")
        self.tree = ttk.Treeview(frame, columns=columns,
                                 show="tree headings")
        self.tree.heading("#0", text="Filename")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        self.tree.column("#0", width=350)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("modified", width=150, anchor="center")

        scroll = ttk.Scrollbar(frame, orient="vertical",
                               command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------- config
    def _load_config(self):
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for ext, enabled in data.get("types", {}).items():
            if ext in self.type_vars:
                self.type_vars[ext].set(bool(enabled))
        last = data.get("last_folder")
        if last and os.path.isdir(last):
            self.load_folder(last)

    def _save_config(self):
        try:
            CONFIG_FILE.write_text(json.dumps({
                "last_folder": str(self.folder) if self.folder else None,
                "types": {ext: var.get()
                          for ext, var in self.type_vars.items()},
            }), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------ actions
    def _types_changed(self):
        self.refresh()
        self._save_config()

    def _on_focus(self, event):
        if event.widget is self and self.folder:
            self.refresh()

    def open_folder(self):
        initial = str(self.folder) if self.folder else None
        chosen = filedialog.askdirectory(title="Select folder",
                                         initialdir=initial)
        if chosen:
            self.load_folder(chosen)
            self._save_config()

    def load_folder(self, folder):
        self.folder = Path(folder)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.files = []
        if not self.folder:
            return
        if not self.folder.is_dir():
            self.folder_var.set(f"{self.folder} (not found)")
            self.status_var.set("0 files")
            self.delete_btn.config(state="disabled")
            return

        enabled = {ext for ext, var in self.type_vars.items() if var.get()}
        self.folder_var.set(str(self.folder))
        total = 0
        counts = {ext: 0 for ext in enabled}
        for path in sorted(self.folder.glob("*"),
                           key=lambda p: p.name.lower()):
            ext = path.suffix.lower()
            if path.is_file() and ext in enabled:
                try:
                    stat = path.stat()
                except OSError:
                    continue
                self.files.append(path)
                counts[ext] += 1
                total += stat.st_size
                modified = datetime.fromtimestamp(
                    stat.st_mtime).strftime("%d-%m-%Y %H:%M")
                self.tree.insert("", "end", text=path.name,
                                 values=(format_size(stat.st_size), modified))

        count = len(self.files)
        breakdown = ", ".join(f"{n} {ext[1:].upper()}"
                              for ext, n in counts.items() if n)
        status = f"{count} file{'s' if count != 1 else ''}"
        if breakdown and len(counts) > 1:
            status += f" ({breakdown})"
        if count:
            status += f" - total {format_size(total)}"
        self.status_var.set(status)
        self.delete_btn.config(state="normal" if count else "disabled")

    def delete_all(self):
        if not self.files:
            messagebox.showinfo("Camera File Cleaner",
                                "There are no files to delete.")
            return

        count = len(self.files)
        if not messagebox.askyesno(
                "Confirm deletion",
                f"Are you sure you want to permanently delete {count} "
                f"preview file{'s' if count != 1 else ''}?\n\n"
                "This cannot be undone.",
                icon="warning", default="no"):
            return

        errors = []
        deleted = 0
        for path in self.files:
            try:
                path.unlink()
                deleted += 1
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")

        self.refresh()
        if errors:
            messagebox.showwarning(
                "Partially completed",
                f"{deleted} of {count} files deleted.\n\nErrors:\n"
                + "\n".join(errors[:10]))
        else:
            messagebox.showinfo(
                "Done",
                f"{deleted} file{'s' if deleted != 1 else ''} deleted.")


if __name__ == "__main__":
    CameraCleaner().mainloop()
