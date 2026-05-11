import tkinter as tk

from gui.styles import COLORS, FONTS, LAYOUT


class SidebarButton(tk.Button):
    def __init__(self, parent, text, icon="", variant="secondary", command=None, **kwargs):
        # Izgled gumba ovisi o tipu gumba
        variants = {
            "primary": (COLORS["accent"], COLORS["panel_bg_alt"], COLORS["accent_hover"]),
            "secondary": (COLORS["surface"], COLORS["text"], COLORS["surface_hover"]),
            "fresh": (COLORS["fresh"], COLORS["fresh_text"], COLORS["fresh_hover"]),
            "danger": (COLORS["danger_bg"], COLORS["danger"], COLORS["danger_hover"]),
        }
        bg, fg, hover_bg = variants.get(variant, variants["secondary"])
        label = f"{icon}  {text}" if icon else text

        super().__init__(
            parent,
            text=label,
            command=command,
            font=FONTS["button"],
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=LAYOUT["button_padx"],
            pady=LAYOUT["button_pady"],
            highlightthickness=1,
            highlightbackground=COLORS["border_soft"],
            **kwargs,
        )

        # Promjena boje kada je mis iznad gumba
        self.bind("<Enter>", lambda _event: self.configure(bg=hover_bg))
        self.bind("<Leave>", lambda _event: self.configure(bg=bg))


class Divider(tk.Frame):
    def __init__(self, parent, **kwargs):
        # Tanka linija za odvajanje sekcija
        super().__init__(parent, height=1, bg=COLORS["border_soft"], **kwargs)


class SectionLabel(tk.Label):
    def __init__(self, parent, text, bg=COLORS["panel_bg"], **kwargs):
        # Mali naslov sekcije
        super().__init__(
            parent,
            text=text.upper(),
            font=FONTS["caption"],
            bg=bg,
            fg=COLORS["text_muted"],
            **kwargs,
        )


class Card(tk.Frame):
    def __init__(self, parent, bg=COLORS["surface"], **kwargs):
        # Osnovni panel koji se koristi za kartice
        super().__init__(
            parent,
            bg=bg,
            highlightbackground=COLORS["border_soft"],
            highlightthickness=1,
            **kwargs,
        )
