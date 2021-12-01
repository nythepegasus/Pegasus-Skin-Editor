#!/usr/bin/env python3
import json
import tkinter as tk
from tkinter import StringVar, filedialog, messagebox, ttk
from pathlib import Path
from handlers import dskin_handler
from ui import Representation


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.wd = Path(filedialog.askopenfilename(initialdir=Path(".").absolute(),
                                                  filetypes=[("Skin conf", "json"), ("Skin file", "deltaskin")]))
        if self.wd.suffix not in [".json", ".deltaskin"]:
            messagebox.showerror("No File Selected!", "Please select a file to continue.")
            # TODO: Raise an error we can restart from
            raise SystemExit("No file selected")  # Temp
        elif self.wd.suffix == ".deltaskin":
            self.config_data, self.zfile = dskin_handler(self.wd)
            self.OTYPE = "zip"
        elif self.wd.suffix == ".json":
            self.config_data = json.load(self.wd.open())
            self.OTYPE = "dir"

        self.title(self.config_data["name"])

        self.notebook = ttk.Notebook()
        self.notebook.enable_traversal()
        self.notebook.pack(anchor="nw")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self.cur_selected = StringVar(None, "")
        statusbar = tk.Label(self, textvariable=self.cur_selected, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.SKIN_TYPES = []
        self.reprs = {}

        representations = self.config_data["representations"]["iphone"]
        for map_type in representations:
            for orientation in representations[map_type]:
                skin_str = f"{map_type.capitalize()[0:1]} | {orientation.capitalize()[0:1]}"
                self.SKIN_TYPES.append(skin_str)
                cur_repr = representations[map_type][orientation]
                self.reprs[skin_str] = Representation(cur_repr["items"], cur_repr["mappingSize"],
                                                      cur_repr["extendedEdges"], cur_repr["assets"])
                self.reprs[skin_str].pack(fill="both", expand=True)
                self.notebook.add(self.reprs[skin_str], text=skin_str)

        for canv in [self.reprs[r] for r in self.reprs]:
            self.config(**canv.mapping_size)

        self.eval('tk::PlaceWindow . center')
        self.deiconify()

    def _on_tab_change(self, event):
        self.cur_canv = self.reprs[self.notebook.tab(self.notebook.index("current"), "text")]
        size = tuple(self.cur_canv.mapping_size.values())
        self.notebook.config(width=size[0], height=size[1])

        self.eval('tk::PlaceWindow . center')

        self.cur_canv.drag_data = {"x": 0, "y": 0, "item": None}


if __name__ == '__main__':
    Editor().mainloop()
