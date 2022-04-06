import tkinter as tk
from resources import BUTTON_NAMES
from dialogs import ButtonSelect
from typing import Optional
from PIL.ImageTk import PhotoImage, Image


class Region:
    def __init__(self, representation: "Representation", item: dict):
        self.representation = representation
        self._config = item
        self.inputs = self._config["inputs"]
        self.frame = self._config["frame"]

        self.tch_tag = None
        self.ext_tag = None
        self._pi_t = None
        self._pi_e = None
        self.touch = None
        self.extended = None

        if "extendedEdges" in self._config.keys():
            self.extended_edges = self._config["extendedEdges"]
            for key in self.representation.extended_edges.keys():
                if key not in self.extended_edges:
                    self.extended_edges[key] = self.representation.extended_edges[key]
        else:
            self.extended_edges = self.representation.extended_edges

        self.create_images(self.frame, self.extended_edges)

    def create_images(self, frame, extended_edges):
        width = int(frame["width"])
        height = int(frame["height"])
        coords = (int(frame["x"]), int(frame["y"]))

        top = extended_edges["top"]
        bottom = extended_edges["bottom"]
        left = extended_edges["left"]
        right = extended_edges["right"]

        self.touch = Image.new("RGBA", (width, height), "#0000ff80")
        self.extended = Image.new(
            "RGBA", (left + width + right, top + height + bottom), "#ff000080"
        )

        self._pi_t = PhotoImage(self.touch)
        self._pi_e = PhotoImage(self.extended)

        self.ext_tag = self.representation.create_image(
            coords[0] - left, coords[1] - top, image=self._pi_e, anchor="nw"
        )
        self.tch_tag = self.representation.create_image(
            *coords, image=self._pi_t, anchor="nw"
        )

        self.representation.images.update({str(self.tch_tag): self})
        self.representation.images.update({str(self.ext_tag): self})

    def move(self, delta_x, delta_y):
        self.representation.move(self.ext_tag, delta_x, delta_y)
        self.representation.move(self.tch_tag, delta_x, delta_y)

    def resize_touch(self, delta_w, delta_h):
        if delta_w < 0 or delta_h < 0:
            self.resize_extended(delta_w, delta_h, True)
        else:
            self.resize_extended(delta_w, delta_h)
        tx1, ty1, tx2, ty2 = self.representation.bbox(self.tch_tag)
        self.representation.images.pop(str(self.tch_tag))
        self.representation.delete(self.tch_tag)

        w = tx2 - tx1
        h = ty2 - ty1

        self.touch = self.touch.resize((w + delta_w, h + delta_h))
        self._pi_t = PhotoImage(self.touch)
        self.tch_tag = self.representation.create_image(
            tx1, ty1, image=self._pi_t, anchor="nw"
        )

        self.representation.sel_tag = self.tch_tag
        self.representation.images.update({str(self.tch_tag): self})

    def resize_extended(self, delta_w, delta_h, opposite=False):
        x1, y1, x2, y2 = self.representation.bbox(self.ext_tag)
        tx1, ty1, tx2, ty2 = self.representation.bbox(self.tch_tag)

        if opposite:
            if (
                tx1 < x1 + delta_w
                or ty1 < y1 + delta_h
                or tx2 > x2 + delta_w
                or ty2 > y2 + delta_h
            ):
                return

        self.representation.images.pop(str(self.ext_tag))
        self.representation.delete(self.ext_tag)

        w = x2 - x1
        h = y2 - y1

        if opposite:
            self.extended = self.extended.resize((w - abs(delta_w), h - abs(delta_h)))
            self._pi_e = PhotoImage(self.extended)

            if delta_w < 0 or delta_h < 0:
                self.ext_tag = self.representation.create_image(
                    x1, y1, image=self._pi_e, anchor="nw"
                )
            if delta_w > 0:
                self.ext_tag = self.representation.create_image(
                    x1 + delta_w, y1, image=self._pi_e, anchor="nw"
                )
            if delta_h > 0:
                self.ext_tag = self.representation.create_image(
                    x1, y1 + delta_h, image=self._pi_e, anchor="nw"
                )
        else:
            self.extended = self.extended.resize((w + abs(delta_w), (h + abs(delta_h))))
            self._pi_e = PhotoImage(self.extended)

            if delta_w > 0 or delta_h > 0:
                self.ext_tag = self.representation.create_image(
                    x1, y1, image=self._pi_e, anchor="nw"
                )
            if delta_w < 0:
                self.ext_tag = self.representation.create_image(
                    x1 + delta_w, y1, image=self._pi_e, anchor="nw"
                )
            if delta_h < 0:
                self.ext_tag = self.representation.create_image(
                    x1, y1 + delta_h, image=self._pi_e, anchor="nw"
                )

        self.representation.sel_tag = self.ext_tag
        self.representation.tag_raise(self.tch_tag)
        self.representation.images.update({str(self.ext_tag): self})

    def delete(self):
        self.representation.delete(self.ext_tag)
        self.representation.delete(self.tch_tag)
        self.representation.images.pop(str(self.tch_tag))
        self.representation.images.pop(str(self.ext_tag))


class Representation(tk.Canvas):
    def __init__(self, cur_repr: dict, game_type: str, bg_image: Image):
        super().__init__()
        self.regions: list[Region] = []
        self.selected: Optional[Region] = None
        self.cur_repr = cur_repr
        self.images: dict[str:Region] = {}
        self.sel_tag = 0
        self.selected_data = {"x": 0, "y": 0}
        self.selected_text = None
        self.game_type = game_type

        self.mapping_size = cur_repr["mappingSize"]
        self._items = cur_repr["items"]
        if "extendedEdges" in cur_repr.keys():
            self.extended_edges = cur_repr["extendedEdges"]
        else:
            self.extended_edges = {
                "top": 0,
                "bottom": 0,
                "left": 0,
                "right": 0
            }
        self.assets = cur_repr["assets"]

        self._bg_image = PhotoImage(bg_image)
        self.create_image(0, 0, image=self._bg_image, anchor="nw", tag="nodrag")

        for item in self._items:
            self.regions.append(Region(self, item))

        self.bind("<Button-1>", self.select_region)
        self.bind("<Escape>", self.deselect_region)
        self.bind("<ButtonRelease-1>", self.drag_stop)
        self.bind("<B1-Motion>", self.drag)
        self.bind("d", self.delete_region)

    def statusbar_updater(self):
        try:
            key = next(
                key for key in BUTTON_NAMES.keys() if key in str(self.selected.inputs)
            )
            key = BUTTON_NAMES[key]
        except StopIteration:
            if isinstance(self.selected.inputs, list):
                if len(self.selected.inputs) > 1:
                    key = ", ".join([i.title() for i in self.selected.inputs])
                else:
                    key = self.selected.inputs[0].title()
            else:
                key = self.selected.inputs

        x1, y1, x2, y2 = self.bbox(self.sel_tag)
        self.selected_text.set(
            f"{key} | X: {x1} Y: {y1} | W: {x2 - x1} H: {y2 - y1}"
        )

    def select_region(self, event):
        sel = self.find_closest(event.x, event.y)
        if event.state == 1:
            overlapped = self.find_overlapping(event.x, event.y, event.x, event.y)
            if len(overlapped) > 2:
                sel = (overlapped[-2],)

        if "nodrag" in self.gettags(sel[0]):
            return

        self.sel_tag = sel[0]
        self.selected = self.images[f"{sel[0]}"]
        if self.selected.ext_tag == self.sel_tag:
            for bind in ["<Left>", "<Right>", "<Up>", "<Down>"]:
                self.unbind(bind)
                self.bind(bind, self.resize_extended)
        else:
            for bind in ["<Left>", "<Right>", "<Up>", "<Down>"]:
                self.unbind(bind)
                self.bind(bind, self.move_region)
                self.bind(bind, self.resize_region, True)
        self.selected_data = {"x": event.x, "y": event.y}

        self.statusbar_updater()

    def deselect_region(self, _):
        if self.selected is None:
            return
        self.selected = None
        self.sel_tag = 0
        self.selected_text.set("")

    def drag(self, event):
        if self.sel_tag == 0:
            return
        delta_x = event.x - self.selected_data["x"]
        delta_y = event.y - self.selected_data["y"]

        self.selected.move(delta_x, delta_y)

        self.selected_data = {"x": event.x, "y": event.y}

        self.statusbar_updater()

    def drag_stop(self, _):
        self.selected_data = {"x": 0, "y": 0}

    def delete_region(self, _):
        if self.selected is None:
            return
        self.selected.delete()
        self.deselect_region(None)

    def move_region(self, event):
        if self.selected is None:
            return
        if event.keysym == "Right" and not bool(0x1 & event.state):
            self.selected.move(1, 0)
        elif event.keysym == "Left" and not bool(0x1 & event.state):
            self.selected.move(-1, 0)
        elif event.keysym == "Up" and not bool(0x1 & event.state):
            self.selected.move(0, -1)
        elif event.keysym == "Down" and not bool(0x1 & event.state):
            self.selected.move(0, 1)

        self.statusbar_updater()

    def resize_region(self, event):
        if self.selected is None:
            return
        if event.keysym == "Right" and bool(0x1 & event.state):
            self.selected.resize_touch(1, 0)
        elif event.keysym == "Left" and bool(0x1 & event.state):
            self.selected.resize_touch(-1, 0)
        elif event.keysym == "Up" and bool(0x1 & event.state):
            self.selected.resize_touch(0, -1)
        elif event.keysym == "Down" and bool(0x1 & event.state):
            self.selected.resize_touch(0, 1)

        self.statusbar_updater()

    def resize_extended(self, event):
        if event.keysym == "Right":
            if bool(0x1 & event.state):
                self.selected.resize_extended(1, 0, True)
            else:
                self.selected.resize_extended(1, 0)
        elif event.keysym == "Left":
            if bool(0x1 & event.state):
                self.selected.resize_extended(-1, 0, True)
            else:
                self.selected.resize_extended(-1, 0)
        elif event.keysym == "Up":
            if bool(0x1 & event.state):
                self.selected.resize_extended(0, -1, True)
            else:
                self.selected.resize_extended(0, -1)
        elif event.keysym == "Down":
            if bool(0x1 & event.state):
                self.selected.resize_extended(0, 1, True)
            else:
                self.selected.resize_extended(0, 1)

        self.statusbar_updater()

    def save(self):
        items = []
        for reg in self.regions:
            item = {"inputs": reg.inputs}
            tx1, ty1, tx2, ty2 = self.bbox(reg.tch_tag)
            ex1, ey1, ex2, ey2 = self.bbox(reg.ext_tag)
            item["frame"] = {
                "x": tx1,
                "y": ty1,
                "width": tx2 - tx1,
                "height": ty2 - ty1,
            }
            item["extendedEdges"] = {
                "top": ty1 - ey1,
                "left": tx1 - ex1,
                "right": ex2 - tx2,
                "bottom": ey2 - ty2,
            }
            items.append(item)
        self.cur_repr["items"] = items
