import tkinter as tk
from PIL.ImageTk import PhotoImage, Image


class Canvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images = []
        self.regions = []


class TouchRect(PhotoImage):
    def __init__(self, color: str, dims: list, coords: list):
        self.parent: "TouchRegion" = None
        self.color = color
        self.dims = dims
        self.coords = coords
        self.orig = Image.new("RGBA", (self.dims[0], self.dims[1]), self.color)
        super().__init__(self.orig)
        self.name = str(self._PhotoImage__photo)

    def create(self, update=False):
        self.canvas = self.parent.canvas
        try:
            self.canvas.images.pop(self.canvas.images.index(self))
        except:
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

    def create(self):
        self.extendedRect.create()
        self.touchRect.create()

    def update(self, w, h, touch: bool):
        if touch:
            self.extendedRect.update(self.extendedColor, w, h)
            self.touchRect.update(self.touchColor, w, h)
        else:
            self.extendedRect.update(self.extendedColor, w, h)
            self.touchRect.move(0, 0)

    def move(self, x, y):
        self.extendedRect.move(x, y)
        self.touchRect.move(x, y)
