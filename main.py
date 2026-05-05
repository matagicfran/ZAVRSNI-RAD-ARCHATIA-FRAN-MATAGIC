import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1) # DPI FIX

import tkinter as tk
from gui.app import EnhancedGUI


root = tk.Tk()
app = EnhancedGUI(root)
root.mainloop()