#!/usr/bin/env python3
import io
import yaml
import json
import tkinter as tk
import argparse
import zipfile
from dialogs import SaveDialog
from tkinter import StringVar, filedialog, messagebox, ttk
from pdf2image import convert_from_bytes as cfb
from pdf2image import convert_from_path as cfp
from pdf2image.exceptions import PDFPageCountError
from PIL.ImageTk import Image
from pathlib import Path
from handlers import dskin_handler
from ui import Representation


class Editor(tk.Tk):
    def __init__(self, file=None):
        super().__init__()
        self.withdraw()
        if file is None:
            self.wd = Path(
                filedialog.askopenfilename(
                    initialdir=Path(".").absolute(),
                    filetypes=[("Skin conf", "json"), ("Skin file", "deltaskin")],
                )
            )
        else:
            self.wd = Path(file)
        if self.wd.suffix not in [".json", ".deltaskin"]:
            messagebox.showerror(
                "No File Selected!", "Please select a file to continue."
            )
            # TODO: Raise an error we can restart from
            raise SystemExit("No file selected")
        elif self.wd.suffix == ".deltaskin":
            self.config_data, self.zfile = dskin_handler(self.wd)
            self.OTYPE = "zip"
        elif self.wd.suffix == ".json":
            self.config_data = yaml.load(self.wd.open(), yaml.Loader)
            self.OTYPE = "dir"
        self.cur_canv = None

        self.title(self.config_data["name"])

        self.notebook = ttk.Notebook()
        self.notebook.enable_traversal()
        self.notebook.pack(anchor="nw")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self.bind("<Command-s>", self.save_all)

        self.cur_selected = StringVar(None, "")
        statusbar = tk.Label(self, textvariable=self.cur_selected, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.SKIN_TYPES = []
        self.reprs = {}

        representations = self.config_data["representations"]["iphone"]
        for map_type in representations:
            for orientation in representations[map_type]:
                skin_str = (
                    f"{map_type.capitalize()[0:1]} | {orientation.capitalize()[0:1]}"
                )
                self.SKIN_TYPES.append(skin_str)
                cur_repr = representations[map_type][orientation]
                key = next(iter(cur_repr["assets"].keys()))
                size = tuple(cur_repr["mappingSize"].values())
                size = int(size[0]), int(size[1])
                try:
                    if "resizable" in cur_repr["assets"]:
                        if self.OTYPE == "dir":
                            bg_image = cfp(
                                Path(self.wd.parent / cur_repr["assets"][key]),
                                size=size,
                                fmt="png",
                            )[0]
                        else:
                            bg_image = cfb(
                                self.zfile.read(cur_repr["mappingSize"][key]), size=size, fmt="png"
                            )[0]
                    else:
                        if self.OTYPE == "dir":
                            bg_image = Image.open(self.wd.parent / cur_repr["mappingSize"][key]).resize(
                                size
                            )
                        else:
                            bg_image = Image.open(
                                io.BytesIO(self.zfile.read(cur_repr["mappingSize"][key]))
                            ).resize(size)
                except (PDFPageCountError, KeyError) as e:
                    if isinstance(e, KeyError):
                        raise SystemExit("Couldn't get the correct key!")
                    else:
                        raise SystemExit(
                            "Couldn't get PDF information! Check your Poppler version."
                        )

                self.reprs[skin_str] = Representation(cur_repr, self.config_data["gameTypeIdentifier"], bg_image)
                self.reprs[skin_str].pack(fill="both", expand=True)
                self.notebook.add(self.reprs[skin_str], text=skin_str)
                self.reprs[skin_str].selected_text = self.cur_selected

        for canv in [self.reprs[r] for r in self.reprs]:
            self.config(**canv.mapping_size)

        self.eval("tk::PlaceWindow . center")
        self.deiconify()

    def _on_tab_change(self, _):
        try:
            self.cur_canv.save()
        except AttributeError:
            pass
        self.cur_canv = self.reprs[
            self.notebook.tab(self.notebook.index("current"), "text")
        ]
        self.cur_canv.focus_set()
        size = list(self.cur_canv.mapping_size.values())
        size = int(size[0]) + 1, int(size[1]) + 1
        self.notebook.config(width=size[0], height=size[1])

        self.eval("tk::PlaceWindow . center")

        self.cur_canv.selected = None
        self.cur_selected.set("")

    def save_all(self, _):
        for canv in self.reprs.values():
            canv.save()
        save_dialog = SaveDialog(self.config_data)
        save_dialog.wait_window(save_dialog)
        save_values = save_dialog.ret_dict
        if save_values is not None:
            self.config_data["name"] = save_values["name"]
            self.title(self.config_data["name"])
            self.config_data["identifier"] = save_values["identifier"]
            self.config_data["gameTypeIdentifier"] = save_values["gameTypeIdentifier"]
            self.config_data["debug"] = save_values["debug"]
            if save_values["overwrite"]:
                if self.OTYPE == "dir":
                    json.dump(self.config_data, self.wd.open("w"), indent=2)
                else:
                    with zipfile.ZipFile(self.wd) as zfile:
                        zfile.writestr("info.json", json.dumps(self.config_data, indent=2))
                        for file in self.zfile.filelist:
                            if file.filename != "info.json":
                                zfile.writestr(file.filename, self.zfile.open(file).read())
            else:
                if self.OTYPE == "dir":
                    conf_file = filedialog.asksaveasfilename(
                        defaultextension=".json",
                        filetypes=[("JSON Files", ".json")],
                        initialdir=self.wd.parent,
                        title="Choose New Config File",
                    )
                    if not conf_file:
                        return
                else:
                    with zipfile.ZipFile(self.wd.parent / f"{self.wd.stem}_edited{self.wd.suffix}") as zfile:
                        zfile.writestr("info.json", json.dumps(self.config_data, indent=2))
                        for file in self.zfile.filelist:
                            if file.filename != "info.json":
                                zfile.writestr(file.filename, self.zfile.open(file).read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='[DEBUGGER] Only for debugging application from CLI')
    parser.add_argument("opt_pos_arg", type=str, nargs="?", help="File to open on launch")
    args = parser.parse_args()
    print(args.opt_pos_arg)
    Editor(args.opt_pos_arg).mainloop()
