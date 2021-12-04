import tkinter as tk


class SaveDialog(tk.Toplevel):
    def __init__(self, config_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Save Dialog")
        self.config_data = config_data
        self.game_type = self.config_data["gameTypeIdentifier"]

        self.ret_dict = None

        self.game_types = [
            "com.rileytestut.delta.game.gbc",
            "com.rileytestut.delta.game.gba",
            "com.rileytestut.delta.game.ds",
            "com.rileytestut.delta.game.nes",
            "com.rileytestut.delta.game.snes",
            "com.rileytestut.delta.game.n64"
        ]

        if self.game_type not in self.game_types:
            self.sel_game_type = self.game_types[0]

        self.bind("<Return>", self.get_vars)
        self.bind("<Escape>", lambda _: self.destroy())

        self._game_type_var = tk.StringVar(self, value=self.game_type)
        self._debug_var = tk.BooleanVar(self, value=self.config_data["debug"])
        self._overwrite_var = tk.BooleanVar(self, value=True)

        self.name = tk.Entry(self, justify="center")
        self.name.insert(tk.END, self.config_data["name"])
        self.name.pack()

        self.identifier = tk.Entry(self, justify="center")
        self.identifier.insert(tk.END, self.config_data["identifier"])
        self.identifier.pack()

        self.game_type = tk.OptionMenu(self, self._game_type_var, *self.game_types)
        self.game_type.pack()

        self.debug = tk.Checkbutton(self, text="Debug", variable=self._debug_var)
        self.debug.pack()

        self.overwrite = tk.Checkbutton(self, text="Overwrite", variable=self._overwrite_var)
        self.overwrite.pack()

        self.submit = tk.Button(self, text="Submit", command=self.get_vars)
        self.submit.pack()

    def get_vars(self, _=None):
        self.ret_dict = {
            "name": self.name.get(),
            "identifier": self.identifier.get(),
            "gameTypeIdentifier": self._game_type_var.get(),
            "debug": self._debug_var.get(),
            "overwrite": self._overwrite_var.get()
        }
        self.destroy()
