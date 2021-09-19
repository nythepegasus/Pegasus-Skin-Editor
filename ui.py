import tkinter as tk
import zipfile
from pprint import pprint
from tkinter import filedialog, messagebox
from PIL.ImageTk import PhotoImage, Image
import json


class ButtonSelect(tk.Toplevel):
    def __init__(self, orientation, pre_sel=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Buttons")
        self.pre_sel = pre_sel
        if isinstance(self.pre_sel, dict):
            self.pre_sel = str(self.pre_sel)
        self.ret_value = None
        self.sel_buttons = []
        self.dpad = {"up": "up", "down": "down", "left": "left", "right": "right"}

        self.bind("<Return>", self._get_vars)
        self.bind("<Escape>", lambda _: self.destroy())

        self.universal_buttons = ["a", "b", "start", str(self.dpad), "thumbstick", "quickSave",
                                  "quickLoad", "fastForward", "toggleFastForward", "menu"]
        self.gbc_buttons = self.universal_buttons + ["select"]
        self.gba_buttons = self.gbc_buttons + ["l", "r"]
        self.nds_buttons = self.gba_buttons + ["x", "y"]
        self.nes_buttons = self.gbc_buttons
        self.snes_buttons = self.nes_buttons + ["x", "y"]
        self.n64_buttons = self.universal_buttons + ["cUp", "cDown", "cLeft", "cRight", "l", "r", "z"]
        self.sg_buttons = self.universal_buttons + ["c", "x", "y", "mode", "z"]

        if orientation == "com.rileytestut.delta.game.gbc":
            self.BUTTONS = self.gbc_buttons
        elif orientation == "com.rileytestut.delta.game.gba":
            self.BUTTONS = self.gba_buttons
        elif orientation == "com.rileytestut.delta.game.nds":
            self.BUTTONS = self.nds_buttons
        elif orientation == "com.rileytestut.delta.game.nes":
            self.BUTTONS = self.nes_buttons
        elif orientation == "com.rileytestut.delta.game.snes":
            self.BUTTONS = self.snes_buttons
        elif orientation == "com.rileytestut.delta.game.n64":
            self.BUTTONS = self.n64_buttons
        else:
            self.BUTTONS = self.sg_buttons
        self.BUTTONS.sort(key=len)
        self.__create_widgets()

    def __create_widgets(self):
        for button in self.BUTTONS:
            but_var = tk.StringVar(self, value=button)
            self.sel_buttons.append(but_var)
            ch_button = tk.Checkbutton(self, text=button, variable=but_var, onvalue=button, offvalue="")
            ch_button.deselect()
            if self.pre_sel is not None:
                if len(self.pre_sel) > 0:
                    if button in self.pre_sel:
                        ch_button.select()
            ch_button.pack()
        submit = tk.Button(self, text="Submit", command=lambda: self._get_vars(None))
        submit.pack()

    def _get_vars(self, _):
        test = [v.get() for v in self.sel_buttons if v.get() == str(self.dpad)]

        self.ret_value = [v.get() for v in self.sel_buttons if v.get() != ""]
        if len(self.ret_value) == 0:
            messagebox.showwarning("Nothing Selected!", "You have to select some buttons before submitting.")
            print(self.ret_value)
            self.focus_force()
            return
        if len(test) == 1:
            if len(self.ret_value) > 1:
                messagebox.showwarning("Too many selected!", "You can't have other buttons selected with dpad.")
                self.focus_force()
                return
            else:
                self.ret_value = self.dpad
        self.destroy()


class SaveDialog(tk.Toplevel):
    def __init__(self, sel_game_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ret_dict = None

        self.game_types = [
            "com.rileytestut.delta.game.gbc",
            "com.rileytestut.delta.game.gba",
            "com.rileytestut.delta.game.ds",
            "com.rileytestut.delta.game.nes",
            "com.rileytestut.delta.game.snes",
            "com.rileytestut.delta.game.n64"
        ]

        self.sel_game_type = self.game_types[0] if sel_game_type is None else sel_game_type

        self.bind("<Return>", self.__get_vars)
        self.bind("<Escape>", lambda _: self.destroy())

        self._name_var = tk.StringVar(self, value="Default Skin Name")
        self._identifier_var = tk.StringVar(self, value="com.example.default")
        self._game_type_var = tk.StringVar(self, value=self.sel_game_type)
        self._debug_var = tk.BooleanVar(self, value=False)
        self._overwrite_var = tk.BooleanVar(self, value=True)
        self.__create_widgets()

    def __create_widgets(self):
        self.name = tk.Entry(self, justify="center")
        self.name.insert(tk.END, self._name_var.get())
        self.name.pack()

        self.identifier = tk.Entry(self, justify="center")
        self.identifier.insert(tk.END, self._identifier_var.get())
        self.identifier.pack()

        self.game_type = tk.OptionMenu(self, self._game_type_var, *self.game_types)
        self.game_type.pack()

        self.debug = tk.Checkbutton(self, text="Debug", variable=self._debug_var)
        self.debug.pack()

        self.overwrite = tk.Checkbutton(self, text="Overwrite", variable=self._overwrite_var)
        self.overwrite.pack()

        self.submit = tk.Button(self, text="Submit", command=self.__get_vars)
        self.submit.pack()

    def __get_vars(self, _=None):
        self.ret_dict = {
            "name": self._name_var.get(),
            "identifier": self._identifier_var.get(),
            "gameTypeIdentifier": self._game_type_var.get(),
            "debug": self._debug_var.get(),
            "overwrite": self._overwrite_var.get()
        }
        self.destroy()


class Canvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = None
        self.images = []
        self.regions = []

    def save(self):
        self.master.mapping["items"].clear()
        for region in self.regions:
            touch_coords = region.touchRect.coords
            touch_dims = region.touchRect.dims
            extended_coords = region.extendedRect.coords
            extended_dims = region.extendedRect.dims
            frame = {'x': touch_coords[0], 'y': touch_coords[1], 'width': touch_dims[0], 'height': touch_dims[1]}
            extendedEdges = {
                'left': touch_coords[0] - extended_coords[0],
                'top': touch_coords[1] - extended_coords[1],
                'right': (extended_dims[0] + extended_coords[0]) - (touch_coords[0] + touch_dims[0]),
                'bottom': (extended_dims[1] + extended_coords[1]) - (touch_coords[1] + touch_dims[1])
            }
            self.master.mapping["items"].append({"inputs": region.input, "frame": frame,
                                                 "extendedEdges": extendedEdges})
        save_dialog = SaveDialog(self.master.config_data["gameTypeIdentifier"])
        save_dialog.wait_window(save_dialog)
        save_values = save_dialog.ret_dict

        if save_values is None:
            return

        self.master.config_data["name"] = save_values["name"]
        self.master.config_data["identifier"] = save_values["identifier"]
        self.master.config_data["gameTypeIdentifier"] = save_values["gameTypeIdentifier"]
        self.master.config_data["debug"] = save_values["debug"]

        if save_values["overwrite"]:
            if self.master.open_type == "dir":
                json.dump(self.master.config_data, self.master.wd.open("w"), indent=4)
            else:
                with zipfile.ZipFile(self.master.wd.parent / f"{self.master.wd.stem}_edited{self.master.wd.suffix}",
                                     "w") as zfile:
                    zfile.writestr("info.json", json.dumps(self.master.config_data, indent=4))
                    for file in self.master.zfile.filelist:
                        if file.filename != "info.json":
                            zfile.writestr(file.filename, self.master.zfile.open(file).read())
        else:
            conf_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")],
                                                     initialdir=self.master.wd.parent, title="Choose Config File")
            if conf_file == '':
                return
            json.dump(self.master.config_data, open(conf_file, "w"), indent=4)

    def redraw(self, background):
        self.delete("all")
        self.background = background
        self.create_image(0, 0, image=background, anchor="nw")
        for region in self.regions:
            region.create()


class TouchRect(PhotoImage):
    def __init__(self, color: str, dims: list, coords: list):
        self.parent: "TouchRegion" = None
        self.canvas = None
        self.color = color
        self.dims = dims
        self.coords = coords
        self.orig = Image.new("RGBA", (self.dims[0], self.dims[1]), self.color)
        super().__init__(self.orig)
        self.name = str(self._PhotoImage__photo)

    def create(self, update: bool = False):
        self.canvas = self.parent.canvas
        try:
            self.canvas.images.pop(self.canvas.images.index(self))
        except (IndexError, ValueError):
            pass
        if update:
            self.canvas.create_image(self.coords[0], self.coords[1], image=self, anchor="nw", tags="sel")
        else:
            self.canvas.create_image(self.coords[0], self.coords[1], image=self, anchor="nw")
        self.canvas.images.append(self)
        self.name = str(self._PhotoImage__photo)

    def move(self, x=0, y=0):
        self.canvas.delete(self)
        self.canvas.images.pop(self.canvas.images.index(self))
        self.coords[0] += x
        self.coords[1] += y
        super().__init__(self.orig)
        self.create(True)

    def update(self, color, w=0, h=0):
        self.canvas.delete(self)
        self.canvas.images.pop(self.canvas.images.index(self))
        self.color = color
        self.dims[0] += w
        self.dims[1] += h
        self.orig = Image.new("RGBA", (self.dims[0], self.dims[1]), self.color)
        super().__init__(self.orig)
        self.create(True)


class ExtendedRect(TouchRect):
    def __init__(self, color: str, dims: list, coords: list):
        super().__init__(color, dims, coords)


class TouchRegion:
    def __init__(self, canvas: Canvas, touchRect: TouchRect, extendedRect: TouchRect, input):
        self.canvas = canvas
        self.input = input
        self.touchRect = touchRect
        self.extendedRect = extendedRect
        self.touchRect.parent = self
        self.extendedRect.parent = self
        self.touchColor = "#0000ff80"
        self.extendedColor = "#ff000080"

    def create(self, update: bool = False):
        self.extendedRect.create(update)
        self.touchRect.create(update)

    def update(self, w, h, touch: bool, rev: bool = False):
        if touch:
            self.extendedRect.update(self.extendedColor, w, h)
            self.touchRect.update(self.touchColor, w, h)
        else:
            if rev:
                if w < 0 or h < 0:
                    self.extendedRect.update(self.extendedColor, -w, -h)
                    self.extendedRect.move(w, h)
                else:
                    self.extendedRect.update(self.extendedColor, -w, -h)
            else:
                if self.touchRect.coords[0] <= self.extendedRect.coords[0] - w:
                    self.extendedRect.coords[0] = self.touchRect.coords[0]
                    w = 0
                elif self.touchRect.coords[1] <= self.extendedRect.coords[1] + h:
                    self.extendedRect.coords[1] = self.touchRect.coords[1]
                    h = 0
                if w > 0 or h > 0:
                    self.extendedRect.update(self.extendedColor, w, h)
                else:
                    self.extendedRect.update(self.extendedColor, w, h)
                    self.extendedRect.move(-w, -h)
            self.touchRect.update(self.touchColor)

    def move(self, x, y):
        self.extendedRect.move(x, y)
        self.touchRect.move(x, y)


if __name__ == '__main__':
    root = tk.Tk()
    SaveDialog(root)
    root.mainloop()