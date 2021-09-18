# Pegasus Skin Editor
This is a skin editor for the Delta emulator! You can position, delete, and edit buttons
for skins that are usable within [Delta](https://deltaemulator.com/). 

---
## Installing
First you will want poppler for your whatever system you want to use this editor on.

---
### Windows 
I highly recommend getting poppler from [here](https://blog.alivate.com.au/poppler-windows/).
I personally have had the best luck using version 0.67.0, but others have gotten higher versions 
to work from elsewhere.
---
### Mac (using brew)
```bash
brew install poppler
```
---
### Linux
Debian based, use whichever package manager your system comes with
```bash
sudo apt install poppler
```
---
To run, you will probably want to set up a Python virtual environment 
(`python3 -m venv venv`) and then run:
```
pip install -r requirements.txt
```
Then you can run:
```
python3 Editor.py 
```
Or on Windows you can just double click the `Editor.py` file. 