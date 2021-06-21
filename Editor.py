import json
import tempfile
import tkinter as tk
from tkinter import ttk, StringVar, filedialog, messagebox
from pdf2image import convert_from_path as cfp
from pdf2image.exceptions import PDFPageCountError
from pathlib import Path
from PIL.ImageTk import PhotoImage, Image
from ui import Canvas, TouchRect, ExtendedRect, TouchRegion


class TypeChooser(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Choose Type")
        self.parent = parent
        self._create_widgets()
        self.wm_protocol("WM_DELETE_WINDOW", self._destroyed)
        self.bind("<Return>", self._get_results)

    def _destroyed(self):
        self.parent.destroy()

    def _create_widgets(self):
        self.map_type = StringVar(None, "standard")
        self.orientation = StringVar(None, "portrait")
        ttk.Radiobutton(self, text="Standard", variable=self.map_type, value="standard").grid(column=0, row=0,
                                                                                              sticky="nesw")
        ttk.Radiobutton(self, text="Edge to Edge", variable=self.map_type, value="edgeToEdge").grid(column=0, row=1,
                                                                                                    sticky="nesw")
        ttk.Separator(self, orient="vertical").grid(column=1, row=0, rowspan=3, sticky="ns")
        ttk.Radiobutton(self, text="Portrait", variable=self.orientation, value="portrait").grid(column=2, row=0,
                                                                                                 sticky="nsw")
        ttk.Radiobutton(self, text="Landscape", variable=self.orientation, value="landscape").grid(column=2, row=1,
                                                                                                   sticky="nsw")
        submit = ttk.Button(self, text="Submit")
        submit.grid(column=1, row=3)
        submit.bind("<Button-1>", self._get_results)

    def _get_results(self, _):
        wd = filedialog.askdirectory(title="Choose the deltaskin directory:", initialdir="~/")
        if wd == "":
            messagebox.showerror(title="No File!", message="No directory was specified!")
        else:
            self.parent.results = [Path(wd), self.map_type.get(), self.orientation.get()]
            self.parent.ready()
            self.parent.deiconify()
            self.destroy()


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sel_img: TouchRect = None
        self.bind("<Button-1>", self.__info)
        self.bind("<Shift-1>", self.__info)
        self.bind("<Button-2>", self.__redraw)

    def ready(self):
        config = json.load((self.results[0] / "info.json").open())
        self.title(f"{config['name']} | {self.results[2].capitalize()}")
        self.mapping = config['representations']['iphone'][self.results[1]][self.results[2]]
        self.__create_widgets()

    def __create_widgets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            try:
                try:
                    cfp(self.results[0] / self.mapping["assets"]["resizable"],
                        size=(self.mapping["mappingSize"]["width"],
                        self.mapping["mappingSize"]["height"]))[0].save(tmpdir / "temp.png", "PNG")
                except KeyError:
                    cfp(self.results[0] / self.mapping["assets"]["large"],
                        size=(self.mapping["mappingSize"]["width"],
                              self.mapping["mappingSize"]["height"]))[0].save(tmpdir / "temp.png", "PNG")
                background_file = Image.open(tmpdir / "temp.png")
            except PDFPageCountError:  # Assume it's already a png
                background_file = Image.open(self.results[0] / self.mapping["assets"]["large"])

            print(background_file.filename)
            background_file = background_file.resize(size=(self.mapping["mappingSize"]["width"],
                                                           self.mapping["mappingSize"]["height"]))
            self.canv_image = PhotoImage(background_file)
            self.canvas = Canvas(self, width=self.mapping["mappingSize"]["width"],
                                    height=self.mapping["mappingSize"]["height"])
            self.canvas.background = self.canv_image  # tkinter why??
            self.canvas.create_image(0, 0, image=self.canv_image, anchor="nw")
            self.canvas.pack()

        dext = self.mapping['extendedEdges']
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

    def __sel(self):
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

    def __info(self, event):
        if self.canvas.find_withtag("sel"):
            self.__redraw(None)
        sel = self.canvas.find_closest(event.x, event.y)
        print(sel)
        print(len(self.canvas.images))
        if event.state == 1:
            overlapped = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            if len(overlapped) > 2:
                sel = (overlapped[1],)
        if sel[0] == 1:
            return
        sel_img = [i for i in self.canvas.images if i.name == self.canvas.itemcget(sel, "image")][0]
        self.sel_img = sel_img
        print(self.sel_img.parent.input)
        self.canvas.addtag_withtag("sel", sel)
        self.__sel()

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
    root.withdraw()
    chooser = TypeChooser(root)
    root.mainloop()
