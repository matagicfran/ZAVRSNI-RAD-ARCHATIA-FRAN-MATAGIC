import tkinter as tk

from gui.styles import COLORS, FONTS, LAYOUT
from gui.widgets import Card, Divider, SectionLabel, SidebarButton


class EnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARCHATIA")
        self.root.geometry("1500x880")
        self.root.minsize(1180, 720)
        self.root.configure(bg=COLORS["app_bg"])
        self.setup_ui()

    def setup_ui(self):
        self._build_shell()
        self._build_sidebar()
        self._build_history()
        self._build_main()
        self._set_status("Spremno za odabir slike.")

    def _build_shell(self):
        self.sidebar = tk.Frame(
            self.root,
            bg=COLORS["panel_bg_alt"],
            width=LAYOUT["sidebar_width"],
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.history_panel = tk.Frame(
            self.root,
            bg=COLORS["panel_bg"],
            width=LAYOUT["history_width"],
        )
        self.history_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(1, 0))
        self.history_panel.pack_propagate(False)

        self.main = tk.Frame(self.root, bg=COLORS["app_bg"])
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=COLORS["panel_bg_alt"])
        brand.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(28, 20))

        tk.Label(
            brand,
            text="🏛\nARCHATIA",
            font=FONTS["brand"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            brand,
            text="Analiza arhitektonskog stila",
            font=FONTS["small"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        Divider(self.sidebar).pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 22))

        SectionLabel(self.sidebar, text="Radnje", bg=COLORS["panel_bg_alt"]).pack(
            anchor="w", padx=LAYOUT["panel_pad"], pady=(0, 10)
        )

        self.btn_select = SidebarButton(
            self.sidebar,
            text="Odaberi sliku",
            icon="+",
            variant="primary",
        )
        self.btn_select.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 10))

        self.btn_analyze = SidebarButton(
            self.sidebar,
            text="Analiziraj stil",
            icon=">",
            variant="secondary",
        )
        self.btn_analyze.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(0, 10))

        self.btn_clear = SidebarButton(
            self.sidebar,
            text="Očisti povijest",
            icon="x",
            variant="danger",
        )
        self.btn_clear.pack(fill=tk.X, padx=LAYOUT["panel_pad"])

        status = tk.Frame(self.sidebar, bg=COLORS["panel_bg_alt"])
        status.pack(side=tk.BOTTOM, fill=tk.X, padx=LAYOUT["panel_pad"], pady=24)

        SectionLabel(status, text="Status", bg=COLORS["panel_bg_alt"]).pack(anchor="w")
        self.status_label = tk.Label(
            status,
            text="",
            font=FONTS["body"],
            bg=COLORS["panel_bg_alt"],
            fg=COLORS["text_secondary"],
            justify="left",
            anchor="w",
            wraplength=LAYOUT["sidebar_width"] - (LAYOUT["panel_pad"] * 2),
        )
        self.status_label.pack(fill=tk.X, pady=(8, 0))

    def _build_history(self):
        header = tk.Frame(self.history_panel, bg=COLORS["panel_bg"])
        header.pack(fill=tk.X, padx=LAYOUT["panel_pad"], pady=(26, 18))

        tk.Label(
            header,
            text="📜 Povijest analiza",
            font=FONTS["title"],
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Prethodni rezultati prikazuju se ovdje.",
            font=FONTS["small"],
            bg=COLORS["panel_bg"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        history_wrap = Card(self.history_panel, bg=COLORS["surface"])
        history_wrap.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["panel_pad"],
            pady=(0, LAYOUT["panel_pad"]),
        )

        self.history_box = tk.Text(
            history_wrap,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["body"],
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            padx=16,
            pady=16,
            cursor="arrow",
            insertwidth=0,
            selectbackground=COLORS["accent_dark"],
            selectforeground=COLORS["text"],
        )
        history_scroll = tk.Scrollbar(
            history_wrap,
            orient=tk.VERTICAL,
            command=self.history_box.yview,
            width=LAYOUT["scrollbar_width"],
            bg=COLORS["surface_soft"],
            troughcolor=COLORS["panel_bg"],
            activebackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=0,
        )
        self.history_box.configure(yscrollcommand=history_scroll.set)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._write_readonly(
            self.history_box,
            "Još nema spremljenih analiza.\n\nNakon obrade slike, rezultati će se prikazati u ovom panelu.",
        )

    def _build_main(self):
        content = tk.Frame(self.main, bg=COLORS["app_bg"])
        content.pack(
            fill=tk.BOTH,
            expand=True,
            padx=LAYOUT["outer_pad"],
            pady=LAYOUT["outer_pad"],
        )

        tk.Label(
            content,
            text="Radna površina",
            font=FONTS["title"],
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        tk.Label(
            content,
            text="Odaberite fotografiju građevine i pokrenite analizu stila.",
            font=FONTS["body"],
            bg=COLORS["app_bg"],
            fg=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 18))

        self._build_image_panel(content)
        self._build_results_panel(content)

    def _build_image_panel(self, parent):
        image_card = Card(parent, bg=COLORS["surface"], height=210)
        image_card.pack(fill=tk.X)
        image_card.pack_propagate(False)

        inner = tk.Frame(image_card, bg=COLORS["surface"])
        inner.pack(expand=True)

        self.image_label = tk.Label(
            inner,
            text="📷",
            font=FONTS["empty_icon"],
            bg=COLORS["surface"],
            fg=COLORS["accent"],
        )
        self.image_label.pack()

        tk.Label(
            inner,
            text="Nije odabrana slika",
            font=FONTS["section"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
        ).pack(pady=(8, 2))

        tk.Label(
            inner,
            text="Koristite gumb 'Odaberi sliku' u lijevom izborniku.",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
        ).pack()

    def _build_results_panel(self, parent):
        header = tk.Frame(parent, bg=COLORS["app_bg"])
        header.pack(fill=tk.X, pady=(24, 10))

        tk.Label(
            header,
            text="Rezultati analize",
            font=FONTS["title"],
            bg=COLORS["app_bg"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT)

        results_wrap = Card(parent, bg=COLORS["surface"])
        results_wrap.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(
            results_wrap,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["body"],
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            padx=LAYOUT["card_padx"],
            pady=LAYOUT["card_pady"],
            cursor="arrow",
            insertwidth=0,
            selectbackground=COLORS["accent_dark"],
            selectforeground=COLORS["text"],
        )
        results_scroll = tk.Scrollbar(
            results_wrap,
            orient=tk.VERTICAL,
            command=self.results_text.yview,
            width=LAYOUT["scrollbar_width"],
            bg=COLORS["surface_soft"],
            troughcolor=COLORS["panel_bg"],
            activebackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=0,
        )
        self.results_text.configure(yscrollcommand=results_scroll.set)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.results_text.tag_configure(
            "title",
            font=FONTS["section"],
            foreground=COLORS["accent"],
            spacing3=10,
        )
        self.results_text.tag_configure(
            "normal",
            font=FONTS["body"],
            foreground=COLORS["text_secondary"],
            spacing3=6,
        )
        self.results_text.tag_configure(
            "muted",
            font=FONTS["body"],
            foreground=COLORS["text_muted"],
            spacing3=6,
        )

        self.results_text.configure(state=tk.NORMAL)
        self.results_text.insert(tk.END, "Dobrodošli u ARCHATIA\n", "title")
        self.results_text.insert(
            tk.END,
            "Sustav je spreman za analizu arhitektonskog stila.\n\n",
            "normal",
        )
        for step in (
            "1. Odaberite fotografiju građevine.",
            "2. Pokrenite analizu stila.",
            "3. Pregledajte rezultat i spremljenu povijest.",
        ):
            self.results_text.insert(tk.END, f"{step}\n", "muted")
        self.results_text.configure(state=tk.DISABLED)

    def _set_status(self, message):
        self.status_label.configure(text=message)

    def _write_readonly(self, widget, text):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)
