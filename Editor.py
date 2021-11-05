#!/usr/bin/env python3
import io
import json
import platform
import tkinter as tk
from typing import Union
from tkinter import StringVar, filedialog, messagebox
from pdf2image import convert_from_bytes as cfb
from pdf2image import convert_from_path as cfp
from pdf2image.exceptions import PDFPageCountError
from pathlib import Path
from PIL.ImageTk import PhotoImage, Image
from ui import Canvas, TouchRect, ExtendedRect, TouchRegion, ButtonSelect
from handlers import dskin_handler


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.wd = Path(filedialog.askopenfilename(initialdir=Path(".").absolute(),
                                                  filetypes=[("Skin conf", "json"), ("Skin file", "deltaskin")]))
        if self.wd == Path(""):
            messagebox.showerror("No Directory Selected!", "Please select a directory to proceed.")
            raise SystemExit("No directory selected.")
        elif self.wd.suffix == ".json":
            self.open_type = "dir"
            self.config_data = json.load(self.wd.open())
        elif self.wd.suffix == ".deltaskin":
            self.config_data, self.zfile = dskin_handler(self.wd)
            self.open_type = "archive"

        self.map_type = StringVar(None, "standard")
        self.orientation = StringVar(None, "landscape")
        self.cur_selected = StringVar(None, "")

        self.EDITED = False

        self.ready()
        self.deiconify()
        self.sel_img: TouchRect = None

        self.bind("<Button-1>", self.__info)
        self.bind("<Shift-1>", self.__info)
        self.bind("<Command-s>", self.__save)
        self.bind("<Command-a>", self.__new_button)
        self.bind("<Command-e>", self.__edit_button)
        self.bind("<Command-d>", self.__delete_button)
        for bind in ["1", "2", "3", "4"]:
            self.bind(bind, self.__change_layout)
        for bind in ["+", "=", "<plusminus>", "<notequal>", "<endash>", "<emdash>", "-", "_",
                     "<Left>", "<Right>", "<Up>", "<Down>"]:
            self.bind(bind, self.__update)

    def __change_layout(self, event):
        if event.state == 8:
            if event.keysym == "1":
                self.map_type.set("standard")
                self.orientation.set("portrait")
            elif event.keysym == "2":
                self.map_type.set("edgeToEdge")
                self.orientation.set("portrait")
            elif event.keysym == "3":
                self.map_type.set("standard")
                self.orientation.set("landscape")
            elif event.keysym == "4":
                self.map_type.set("edgeToEdge")
                self.orientation.set("landscape")
            self.ready()

    def __new_button(self, _):
        buttons = ButtonSelect(self.config_data['gameTypeIdentifier'])
        buttons.wait_window(buttons)

        if buttons.ret_value is None or len(buttons.ret_value) == 0:
            return
        self.__add_button(buttons.ret_value)

    def __edit_button(self, _):
        if self.sel_img is None:
            return
        buttons = ButtonSelect(self.config_data['gameTypeIdentifier'], self.sel_img.parent.input)
        buttons.wait_window(buttons)

        if buttons.ret_value is None or len(buttons.ret_value) == 0:
            return

        self.sel_img.parent.input = buttons.ret_value

        self.cur_selected.set(f"Input: {self.sel_img.parent.input}"
                              f"X: {self.sel_img.coords[0]} Y: {self.sel_img.coords[1]} "
                              f"W: {self.sel_img.dims[0]} H: {self.sel_img.dims[1]}")

    def __delete_button(self, _):
        if self.sel_img is None:
            return

        self.canvas.regions.pop(self.canvas.regions.index(self.sel_img.parent))
        self.canvas.redraw(self.canv_image)

        self.cur_selected.set(f"")
        self.sel_img = None

    def __add_button(self, inputs: Union[list, dict], frame: dict = None, extended_edges: dict = None):
        if frame is None:
            print((self.winfo_x(), self.winfo_y()))
            x = self.winfo_x() // 2 + 25
            y = self.winfo_y() // 2 - 25
            frame = {'x': x, 'y': y, 'width': 100, 'height': 100}
        if 'extendedEdges' in self.mapping.keys():
            default_extended_edges = self.mapping['extendedEdges']
        else:
            default_extended_edges = {"top": 0, "bottom": 0, "left": 0, "right": 0}
        if extended_edges is None:
            extended_edges = default_extended_edges
        item = {'inputs': inputs, 'frame': frame, 'extendedEdges': extended_edges}
        iext = item['extendedEdges'] if "extendedEdges" in item.keys() else extended_edges.copy()
        for i in default_extended_edges.keys():
            if i not in iext.keys():
                iext[i] = default_extended_edges[i]

        width_add = (0 if 'left' not in iext.keys() else iext['left']) + \
                    (0 if 'right' not in iext.keys() else iext['right']) + frame['width']
        height_add = (0 if 'top' not in iext.keys() else iext['top']) + \
                     (0 if 'bottom' not in iext.keys() else iext['bottom']) + frame['height']

        ex_x = frame['x'] - (0 if 'left' not in iext.keys() else iext['left'])
        ex_y = frame['y'] - (0 if 'top' not in iext.keys() else iext['top'])

        touch_rect = TouchRect("#0000ff80", [frame['width'], frame['height']], [frame['x'], frame['y']])

        extended_rect = ExtendedRect("#ff000080", [width_add, height_add], [ex_x, ex_y])
        region = TouchRegion(self.canvas, touch_rect, extended_rect, item['inputs'])
        region.create()
        self.canvas.regions.append(region)

    def ready(self):
        if self.EDITED:
            save = messagebox.askyesno("Not Saved", "Do you want to save before swapping?")
            if save:
                self.__save()
            else:
                cont = messagebox.askyesno("Continue Anyway?", "Do you want to continue anyway?")
                if not cont:
                    return

        self.EDITED = False
        self.cur_selected.set("")

        for widget in self.winfo_children():
            widget.destroy()
        self.title(f"{self.config_data['name']} | {self.map_type.get()}")
        self.mapping = self.config_data['representations']['iphone'][self.map_type.get()][self.orientation.get()]

        w = self.mapping["mappingSize"]["width"]
        if platform.system() == "Windows" or platform.system() == "Linux":
            h = self.mapping["mappingSize"]["height"] + 40
        else:
            h = self.mapping["mappingSize"]["height"] + 25
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()

        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.__create_widgets()
        self.__create_menus()

    def __create_menus(self):
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar)
        filemenu.add_command(label="Save..", accelerator="Command-s", command=self.__save)

        menubar.add_cascade(label="File", menu=filemenu)

        typemenu = tk.Menu(menubar)
        typemenu.add_radiobutton(label="Standard", value="standard", variable=self.map_type, command=self.ready)
        typemenu.add_radiobutton(label="Edge To Edge", value="edgeToEdge", variable=self.map_type, command=self.ready)
        typemenu.add_separator()
        typemenu.add_radiobutton(label="Portrait", value="portrait", variable=self.orientation, command=self.ready)
        typemenu.add_radiobutton(label="Landscape", value="landscape", variable=self.orientation, command=self.ready)

        menubar.add_cascade(label="Type", menu=typemenu)

        self.config(menu=menubar)

    def __create_widgets(self):
        size = (self.mapping["mappingSize"]["width"], self.mapping["mappingSize"]["height"])
        which_key = list(self.mapping["assets"].keys())[0]
        try:
            if "resizable" in self.mapping["assets"].keys():
                if self.open_type == "dir":
                    image = cfp(Path(self.wd.parent / self.mapping["assets"][which_key]), size=size, fmt="png")[0]
                else:
                    image = cfb(self.zfile.read(self.mapping["assets"][which_key]), size=size, fmt="png")[0]
            else:
                if self.open_type == "dir":
                    image = Image.open(self.wd.parent / self.mapping["assets"][which_key]).resize(size)
                else:

                    image = Image.open(io.BytesIO(self.zfile.read(self.mapping["assets"][which_key]))).resize(size)
        except (PDFPageCountError, KeyError) as e:
            if isinstance(e, KeyError):
                raise SystemExit("Couldn't get the correct key!")
            else:
                raise SystemExit("Couldn't get PDF information! Check your Poppler version.")
        self.canv_image = PhotoImage(image)
        self.canvas = Canvas(self, width=image.width, height=image.height)
        self.canvas.background = self.canv_image
        self.canvas.create_image(0, 0, image=self.canv_image, anchor="nw")
        self.canvas.pack()

        statusbar = tk.Label(self, textvariable=self.cur_selected, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        for item in self.mapping['items']:
            self.__add_button(item['inputs'], item['frame'],
                              item['extendedEdges'] if 'extendedEdges' in item.keys() else None)

    def __save(self, _=None):
        self.canvas.save()
        self.focus_force()

    def __info(self, event: tk.Event):
        if self.canvas.find_withtag("sel"):
            self.canvas.redraw(self.canv_image)
        sel = self.canvas.find_closest(event.x, event.y)
        if event.state == 1:
            overlapped = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            if len(overlapped) > 2:
                sel = (overlapped[-2],)
        try:
            sel_img = [i for i in self.canvas.images if i.name == self.canvas.itemcget(sel, "image")][0]
        except IndexError:
            return
        if sel_img == "pyimage1":
            return
        self.sel_img = sel_img
        self.cur_selected.set(f"Input: {self.sel_img.parent.input}"
                              f"X: {self.sel_img.coords[0]} Y: {self.sel_img.coords[1]} "
                              f"W: {self.sel_img.dims[0]} H: {self.sel_img.dims[1]}")
        self.canvas.addtag_withtag("sel", sel)

    def __update(self, event):
        self.EDITED = True
        x, y = 0, 0
        if isinstance(self.sel_img, TouchRect):
            if event.char in ["-", "–", "—", "_"]:
                y -= 0 if self.sel_img.height() + y <= 0 else 1 if event.char == "–" else 5 if event.char == "—" else 0
                x -= 0 if self.sel_img.width() + x <= 0 else 1 if event.char == "-" else 5 if event.char == "_" else 0
            elif event.char in ["=", "+", "≠", "±"]:
                y += 1 if event.char == "≠" else 5 if event.char == "±" else 0
                x += 1 if event.char == "=" else 5 if event.char == "+" else 0
            self.sel_img.parent.update(x, y, True)
        if event.keysym in ["Left", "Right", "Up", "Down"]:
            if isinstance(self.sel_img, ExtendedRect):
                if event.keysym == "Right":
                    x = 5 if event.state == 112 else -5 if event.state == 113 else 1 if event.state == 96 else -1
                    rev = False
                elif event.keysym == "Left":
                    x = -5 if event.state == 112 else 5 if event.state == 113 else -1 if event.state == 96 else 1
                    rev = True
                elif event.keysym == "Up":
                    y = -5 if event.state == 112 else 5 if event.state == 113 else -1 if event.state == 96 else 1
                    rev = True
                elif event.keysym == "Down":
                    y = 5 if event.state == 112 else -5 if event.state == 113 else 1 if event.state == 96 else -1
                    rev = False
                self.sel_img.parent.update(x, y, False, rev)
            elif isinstance(self.sel_img, TouchRect):
                if event.keysym == "Right":
                    x = 5 if event.state == 112 else 10 if event.state == 97 else 20 if event.state == 113 else 1
                elif event.keysym == "Left":
                    x = -5 if event.state == 112 else -10 if event.state == 97 else -20 if event.state == 113 else -1
                elif event.keysym == "Up":
                    y = -5 if event.state == 112 else -10 if event.state == 97 else -20 if event.state == 113 else -1
                elif event.keysym == "Down":
                    y = 5 if event.state == 112 else 10 if event.state == 97 else 20 if event.state == 113 else 1
                self.sel_img.parent.move(x, y)
        self.cur_selected.set(f"Input: {self.sel_img.parent.input}"
                              f"X: {self.sel_img.coords[0]} Y: {self.sel_img.coords[1]} "
                              f"W: {self.sel_img.dims[0]} H: {self.sel_img.dims[1]}")


if __name__ == '__main__':
    Editor().mainloop()
