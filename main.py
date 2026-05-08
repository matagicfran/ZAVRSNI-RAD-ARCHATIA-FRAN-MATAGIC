import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1) # DPI FIX

import tkinter as tk

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

from gui.app import EnhancedGUI


root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
app = EnhancedGUI(root)
root.mainloop()
