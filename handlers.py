import json
import zipfile
from pathlib import Path
from zipfile import ZipFile
from tkinter import messagebox


def png_handler():
    pass


def pdf_handler():
    pass


def dskin_handler(file: Path):
    zfile = ZipFile(file, "r")
    try:
        config = json.loads(zfile.read("info.json"))
    except KeyError:
        answer = messagebox.askyesno("Couldn't find a proper 'info.json' file in this deltaskin. Do you want this"
                                     "application to attempt to fix this archive? (No data will be destroyed/lost)")
        if answer:
            try:
                conf_file = [f for f in zfile.filelist if "info.json" in f.filename][0]
                config = json.loads(zfile.read(conf_file))
                files = [f for f in zfile.filelist if f.filename.find("._") == -1 and not f.is_dir()]
                nzfile = ZipFile(file.parent / f"{file.stem}_fixed{file.suffix}", "w")
                for file in files:
                    nzfile.writestr(Path(file.filename).name, zfile.read(file), compress_type=zipfile.ZIP_DEFLATED)
                nzfile.close()
                zfile = ZipFile(nzfile.filename, "r")
            except IndexError:
                messagebox.showerror("File not found!", "No file named 'info.json' could be found in this deltaskin.")
                zfile.close()
                raise SystemExit("Couldn't repair deltaskin, no 'info.json' file.")
        else:
            raise SystemExit("User aborted, no suitable deltaskin file selected.")
    return config, zfile
