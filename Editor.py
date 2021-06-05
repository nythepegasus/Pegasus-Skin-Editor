import json
import tempfile
#  from pprint import pprint
from pdf2image import convert_from_path
from pathlib import Path
from PIL.ImageTk import PhotoImage, Image
import tkinter as tk
from tkinter import ttk, StringVar, filedialog, messagebox


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


class Info(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._create_widgets()

    def _create_widgets(self):
        self.inputs = StringVar()
        self.frame_x = StringVar()
        self.frame_y = StringVar()
        self.width = StringVar()
        self.height = StringVar()
        ttk.Label(self, text="Inputs: ").grid(row=0)
        ttk.Label(self, textvariable=self.inputs).grid(row=0, column=1)
        ttk.Label(self, text="Frame X: ").grid(row=1)
        ttk.Label(self, textvariable=self.frame_x).grid(row=1, column=1)
        ttk.Label(self, text="Frame Y: ").grid(row=2)
        ttk.Label(self, textvariable=self.frame_y).grid(row=2, column=1)
        ttk.Label(self, text="Width: ").grid(row=3)
        ttk.Label(self, textvariable=self.width).grid(row=3, column=1)
        ttk.Label(self, text="Height: ").grid(row=4)
        ttk.Label(self, textvariable=self.height).grid(row=4, column=1)


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()

    def ready(self):
        config = json.load((self.results[0] / "info.json").open())
        self.title(f"{config['name']} | {self.results[2].capitalize()}")
        self.mapping = config['representations']['iphone'][self.results[1]][self.results[2]]
        self._create_widgets()
        self.bind("<Button-1>", self.collision)

    def _create_widgets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self.canvas = tk.Canvas(self, width=self.mapping["mappingSize"]["width"],
                                    height=self.mapping["mappingSize"]["height"])
            convert_from_path(self.results[0] / self.mapping["assets"]["resizable"],
                              size=(self.mapping["mappingSize"]["width"],
                                    self.mapping["mappingSize"]["height"]))[0].save(tmpdir / "temp.png", "PNG")
            print(str(tmpdir / "temp.png"))
            image = PhotoImage(Image.open(str(tmpdir / "temp.png")))
            self.canvas.background = image  # TKinter why??
            self.canvas.create_image(0, 0, image=image, anchor="nw")
        self.canvas.ext_boxes = []
        self.canvas.inp_boxes = []
        for item in self.mapping["items"]:
            dext = self.mapping['extendedEdges']
            iext = item['extendedEdges'] if "extendedEdges" in item.keys() else dext
            iframe = item['frame']
            left = (iext['left'] if "left" in iext.keys() else dext['left'])
            right = (iext['right'] if "right" in iext.keys() else dext['right'])
            top = (iext['top'] if "top" in iext.keys() else dext['top'])
            bottom = (iext['bottom'] if "bottom" in iext.keys() else dext['bottom'])
            ex_x = iframe['x'] - left
            ex_y = iframe['y'] - top
            ex_w = iframe['x'] + iframe['width'] + right
            ex_h = iframe['y'] + iframe['height'] + bottom
            self.canvas.ext_boxes.append([ex_x, ex_y, ex_w, ex_h])
            self.canvas.create_rectangle(ex_x, ex_y, ex_w, ex_h, outline="#f51637",
                                         width=3, fill="", stipple="gray25")
            self.canvas.create_rectangle(iframe['x'], iframe['y'],
                                         iframe['x'] + iframe['width'], iframe['y'] + iframe['height'],
                                         outline='#594ced', width=3, fill="", stipple="gray25")

            self.canvas.inp_boxes.append([iframe['x'], iframe['y'],
                                          iframe['x'] + iframe['width'], iframe['y'] + iframe['height']])
        self.canvas.pack()

    def collision(self, pos):
        print(f"X: {pos.x}\nY: {pos.y}")
        for inp in self.canvas.inp_boxes:
            if inp[0] < pos.x < inp[2]:
                if inp[1] < pos.y < inp[3]:
                    sel = self.canvas.find_closest(inp[0], inp[1])
                    break
        else:
            sel = None
        if sel is None:
            for ext in self.canvas.ext_boxes:
                if ext[0] < pos.x < ext[2]:
                    if ext[1] < pos.y < ext[3]:
                        sel = self.canvas.find_closest(ext[0]+6, ext[1])
                        if len(self.canvas.find_below(sel)) == 1:
                            sel = self.canvas.find_below(sel)
                        break
            else:
                sel = None
        if sel is not None:
            self.canvas.itemconfig(sel, outline="#00ff00")


if __name__ == '__main__':
    root = Editor()
    root.withdraw()
    chooser = TypeChooser(root)
    root.mainloop()
