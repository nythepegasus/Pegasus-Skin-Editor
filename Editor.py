import json
import tempfile
import tkinter as tk
from tkinter import ttk, StringVar, filedialog, messagebox
from pdf2image import convert_from_path as cfp
from pdf2image.exceptions import PDFPageCountError
from pathlib import Path
from PIL.ImageTk import PhotoImage, Image
from ui import Canvas, TouchRect, ExtendedRect, TouchRegion


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.wd = Path(filedialog.askdirectory(title="Choose the deltaskin directory:",
                                               initialdir=Path(".").absolute()))
        if self.wd == Path(""):
            messagebox.showerror("No Directory Selected!", "Please select a directory to proceed.")
            exit(1)
        self.map_type = StringVar(None, "standard")
        self.orientation = StringVar(None, "landscape")
        self.ready()
        self.deiconify()
        self.sel_img: TouchRect = None

        self.bind("<Button-1>", self.__info)
        self.bind("<Shift-1>", self.__info)
        self.bind("<Button-2>", self.__redraw)
        self.bind("+", self.__increase)
        self.bind("=", self.__increase)
        self.bind("<plusminus>", self.__increase)
        self.bind("<notequal>", self.__increase)
        self.bind("<endash>", self.__decrease)
        self.bind("<emdash>", self.__decrease)
        self.bind("-", self.__decrease)
        self.bind("_", self.__decrease)
        self.bind("<Left>", self.__move)
        self.bind("<Right>", self.__move)
        self.bind("<Up>", self.__move)
        self.bind("<Down>", self.__move)

    def ready(self):
        for widget in self.winfo_children():
            widget.destroy()
        config = json.load((self.wd / "info.json").open())
        self.title(f"{config['name']} | {self.map_type.get()}")
        self.mapping = config['representations']['iphone'][self.map_type.get()][self.orientation.get()]

        w = self.mapping["mappingSize"]["width"]
        h = self.mapping["mappingSize"]["height"]

        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()

        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.__create_widgets()
        self.__create_menus()

    def __create_menus(self):

        menubar = tk.Menu(self)

        typemenu = tk.Menu(menubar)
        typemenu.add_radiobutton(label="Standard", value="standard", variable=self.map_type, command=self.ready)
        typemenu.add_radiobutton(label="Edge To Edge", value="edgeToEdge", variable=self.map_type, command=self.ready)
        typemenu.add_separator()
        typemenu.add_radiobutton(label="Portrait", value="portrait", variable=self.orientation, command=self.ready)
        typemenu.add_radiobutton(label="Landscape", value="landscape", variable=self.orientation, command=self.ready)

        menubar.add_cascade(label="Type", menu=typemenu)

        self.config(menu=menubar)

    def __create_widgets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            try:
                try:
                    cfp(self.wd / self.mapping["assets"]["resizable"],
                        size=(self.mapping["mappingSize"]["width"],
                        self.mapping["mappingSize"]["height"]))[0].save(tmpdir / "temp.png", "PNG")
                except KeyError:
                    cfp(self.wd / self.mapping["assets"]["large"],
                        size=(self.mapping["mappingSize"]["width"],
                              self.mapping["mappingSize"]["height"]))[0].save(tmpdir / "temp.png", "PNG")
                background_file = Image.open(tmpdir / "temp.png")
            except PDFPageCountError:  # Assume it's already a png
                background_file = Image.open(self.wd / self.mapping["assets"]["large"])

            background_file = background_file.resize(size=(self.mapping["mappingSize"]["width"],
                                                           self.mapping["mappingSize"]["height"]))
            self.canv_image = PhotoImage(background_file)
            self.canvas = Canvas(self, width=self.mapping["mappingSize"]["width"],
                                    height=self.mapping["mappingSize"]["height"])
            self.canvas.background = self.canv_image  # tkinter why??
            self.canvas.create_image(0, 0, image=self.canv_image, anchor="nw")
            self.canvas.pack()
        try:
            dext = self.mapping['extendedEdges']
        except KeyError:
            dext = {"top": 0, "bottom": 0, "left": 0, "right": 0}
        for item in self.mapping['items']:
            iext = item['extendedEdges'] if "extendedEdges" in item.keys() else dext.copy()
            for i in dext.keys():
                if i not in iext.keys():
                    iext[i] = dext[i]
            iframe = item["frame"]

            width_add = (0 if 'left' not in iext.keys() else iext['left']) + \
                        (0 if 'right' not in iext.keys() else iext['right']) + \
                        iframe['width']
            height_add = (0 if 'top' not in iext.keys() else iext['top']) + \
                         (0 if 'bottom' not in iext.keys() else iext['bottom']) + \
                         iframe['height']

            ex_x = iframe['x'] - (0 if 'left' not in iext.keys() else iext['left'])
            ex_y = iframe['y'] - (0 if 'top' not in iext.keys() else iext['top'])

            rectImg = TouchRect("#0000ff80", [iframe['width'], iframe['height']], [iframe['x'], iframe['y']])

            rectImg1 = ExtendedRect("#ff000080", [width_add, height_add], [ex_x, ex_y])
            region = TouchRegion(self.canvas, rectImg, rectImg1, item['inputs'])
            region.create()
            self.canvas.regions.append(region)

    def __redraw(self, _):
        self.canvas.delete("all")
        self.canvas.background = self.canv_image
        self.canvas.create_image(0, 0, image=self.canv_image, anchor="nw")
        for region in self.canvas.regions:
            region.create()

    def __info(self, event):
        if self.canvas.find_withtag("sel"):
            self.__redraw(None)
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
        self.canvas.addtag_withtag("sel", sel)

    def __decrease(self, event):
        x, y = 0, 0
        if event.char in ["—", "–"]:
            y -= 1 if event.char == "–" else 5
            if self.sel_img.height() + y <= 0:
                y = 0
        else:
            x -= 1 if event.char == "-" else 5
            if self.sel_img.width() + x <= 0:
                x = 0
        if isinstance(self.sel_img, ExtendedRect):
            self.sel_img.parent.update(w=x, h=y, touch=False)
        else:
            self.sel_img.parent.update(w=x, h=y, touch=True)

    def __increase(self, event):
        x, y = 0, 0
        if event.char in ["±", "≠"]:
            y += 1 if event.char == "≠" else 5
        else:
            x += 1 if event.char == "=" else 5
        if isinstance(self.sel_img, ExtendedRect):
            self.sel_img.parent.update(w=x, h=y, touch=False)
        else:
            self.sel_img.parent.update(w=x, h=y, touch=True)

    def __move(self, event):
        if self.canvas.find_withtag("sel"):
            x, y = 0, 0
            if event.keysym in ["Left", "Right"]:
                x = 1 if event.keysym == "Right" else -1
                if event.state == 112:
                    x = 5 if event.keysym == "Right" else -5
                elif event.state == 97:
                    x = 10 if event.keysym == "Right" else -10
                elif event.state == 113:
                    x = 20 if event.keysym == "Right" else -20
            else:
                y = 1 if event.keysym == "Down" else -1
                if event.state == 112:
                    y = 5 if event.keysym == "Down" else -5
                elif event.state == 97:
                    y = 10 if event.keysym == "Down" else -10
                elif event.state == 113:
                    y = 20 if event.keysym == "Down" else -20
            if isinstance(self.sel_img, ExtendedRect):
                self.sel_img.parent.update(x, y, False)
            else:
                self.sel_img.parent.move(x, y)


if __name__ == '__main__':
    root = Editor()
    root.mainloop()
