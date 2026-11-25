#!/usr/bin/env python3
"""
Sanitizer Studio - Modern Desktop Edition
A sleek 2026 developer utility for Windows.
- High-DPI hardware scaling enabled for razor-sharp typography
- Custom segmented navigation pills (no vintage OS tabs)
- Elevated card-based workspace layout with live counters and mini-action bars
- Smart word-boundary regex, collision detection, and encoding-aware matching
- Interactive replacement breakdown badges and instant leak scanner
- Dark and Light mode theme engine
"""

import os
import sys
import re
import difflib
import threading
import queue
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import List, Tuple, Dict, Any, Optional

# Enable Per-Monitor High DPI Awareness on Windows for crisp fonts and borders
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from sanitizer_core import SanitizerEngine, Clipboard, DEFAULT_CONFIG_PATH

THEMES = {
    "dark": {
        "name": "dark",
        "win_bg": "#090d16",          # Deep obsidian background
        "header_bg": "#0d1424",       # Top navigation header
        "card_bg": "#11192e",         # Elevated card surface
        "card_header": "#16203a",     # Card title bar
        "card_border": "#1e293b",     # Subtle 1px framing
        "text_bg": "#070b14",         # Code editor canvas
        "text_fg": "#f1f5f9",         # Editor text
        "text_border": "#1e293b",     # Editor border
        "text_focus": "#3b82f6",      # Active focus border
        "text_muted": "#94a3b8",      # Subtitles and muted labels
        "gutter_bg": "#090d16",       # Line number gutter background
        "gutter_fg": "#475569",       # Line number gutter digits
        "gutter_border": "#1e293b",   # Line number gutter separator
        "status_bg": "#080c14",       # Bottom bar
        "status_fg": "#94a3b8",
        "nav_bg": "#162038",          # Segmented pill container
        "nav_active_bg": "#2563eb",   # Active navigation pill
        "nav_active_fg": "#ffffff",
        "nav_inactive_fg": "#94a3b8",
        "nav_hover_bg": "#1e2c4f",
        "btn_primary_bg": "#2563eb",  # Vibrant Action Blue
        "btn_primary_hover": "#1d4ed8",
        "btn_primary_fg": "#ffffff",
        "btn_success_bg": "#059669",  # Emerald Paste Action
        "btn_success_hover": "#047857",
        "btn_success_fg": "#ffffff",
        "btn_secondary_bg": "#1e293b",# Card action buttons
        "btn_secondary_hover": "#334155",
        "btn_secondary_fg": "#e2e8f0",
        "btn_danger_bg": "#b91c1c",   # Destructive delete
        "btn_danger_hover": "#991b1b",
        "btn_danger_fg": "#ffffff",
        "tag_replaced_bg": "#543e00",  # Dark amber highlight
        "tag_replaced_fg": "#fef08a",
        "tag_restored_bg": "#064e3b",  # Emerald highlight
        "tag_restored_fg": "#a7f3d0",
        "tag_leak_bg": "#5c1010",      # Warning red highlight
        "tag_leak_fg": "#fecaca",
        "tag_partial_leak_bg": "#5a2d0c",  # Amber/orange partial leak
        "tag_partial_leak_fg": "#fed7aa",
        "diff_del_bg": "#450a0a",          # Deep red for deleted / original text
        "diff_del_fg": "#fca5a5",
        "diff_add_bg": "#064e3b",          # Deep emerald for replaced / new text
        "diff_add_fg": "#6ee7b7",
        "badge_bg": "#16203a",
        "badge_fg": "#cbd5e1",
        "badge_border": "#27354a",
        "tree_bg": "#11192e",
        "tree_fg": "#f1f5f9",
        "tree_header_bg": "#090d16",
        "tree_header_fg": "#94a3b8",
        "tree_collision_bg": "#450a0a",
        "tree_collision_fg": "#fca5a5"
    },
    "light": {
        "name": "light",
        "win_bg": "#f1f5f9",          # Slate 100
        "header_bg": "#ffffff",       # Pure white header
        "card_bg": "#ffffff",         # Elevated card
        "card_header": "#f8fafc",     # Card title bar
        "card_border": "#e2e8f0",     # Subtle 1px framing
        "text_bg": "#f8fafc",         # Code editor canvas
        "text_fg": "#0f172a",         # Editor text
        "text_border": "#cbd5e1",     # Editor border
        "text_focus": "#2563eb",      # Active focus border
        "text_muted": "#64748b",      # Muted text
        "gutter_bg": "#f1f5f9",       # Line number gutter background
        "gutter_fg": "#94a3b8",       # Line number gutter digits
        "gutter_border": "#cbd5e1",   # Line number gutter separator
        "status_bg": "#ffffff",       # Bottom bar
        "status_fg": "#475569",
        "nav_bg": "#e2e8f0",          # Segmented pill container
        "nav_active_bg": "#2563eb",   # Active pill
        "nav_active_fg": "#ffffff",
        "nav_inactive_fg": "#475569",
        "nav_hover_bg": "#cbd5e1",
        "btn_primary_bg": "#2563eb",
        "btn_primary_hover": "#1d4ed8",
        "btn_primary_fg": "#ffffff",
        "btn_success_bg": "#059669",
        "btn_success_hover": "#047857",
        "btn_success_fg": "#ffffff",
        "btn_secondary_bg": "#f1f5f9",
        "btn_secondary_hover": "#e2e8f0",
        "btn_secondary_fg": "#1e293b",
        "btn_danger_bg": "#fee2e2",
        "btn_danger_hover": "#fecaca",
        "btn_danger_fg": "#991b1b",
        "tag_replaced_bg": "#fef08a",
        "tag_replaced_fg": "#713f12",
        "tag_restored_bg": "#bbf7d0",
        "tag_restored_fg": "#14532d",
        "tag_leak_bg": "#fee2e2",
        "tag_leak_fg": "#991b1b",
        "tag_partial_leak_bg": "#ffedd5",  # Light amber
        "tag_partial_leak_fg": "#9a3412",
        "diff_del_bg": "#fee2e2",          # Soft red
        "diff_del_fg": "#991b1b",
        "diff_add_bg": "#dcfce7",          # Soft green
        "diff_add_fg": "#166534",
        "badge_bg": "#f8fafc",
        "badge_fg": "#334155",
        "badge_border": "#e2e8f0",
        "tree_bg": "#ffffff",
        "tree_fg": "#0f172a",
        "tree_header_bg": "#f8fafc",
        "tree_header_fg": "#475569",
        "tree_collision_bg": "#fee2e2",
        "tree_collision_fg": "#991b1b"
    }
}


# =============================================================================
# WIDGET: CODE EDITOR LINE NUMBER GUTTER
# =============================================================================
class LineNumberGutter(tk.Canvas):
    """
    Sleek code-editor line number gutter rendered on a canvas.
    Synchronizes seamlessly with Text widget scrolling and dynamic line counts.
    """
    def __init__(self, parent, text_widget: tk.Text, font: Tuple[str, int] = ("Consolas", 10), theme: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(parent, bd=0, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.font = font
        self.gutter_width = 38
        self.bg_color = "#090d16"
        self.fg_color = "#475569"
        self.border_color = "#1e293b"
        if theme:
            self.bg_color = theme.get("gutter_bg", self.bg_color)
            self.fg_color = theme.get("gutter_fg", self.fg_color)
            self.border_color = theme.get("gutter_border", self.border_color)
        self.configure(width=self.gutter_width, bg=self.bg_color)

        # Forward mousewheel events to text widget
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", lambda e: (self.text_widget.yview_scroll(-2, "units"), self.redraw(), "break"))
        self.bind("<Button-5>", lambda e: (self.text_widget.yview_scroll(2, "units"), self.redraw(), "break"))

    def _on_mousewheel(self, event):
        self.text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.redraw()
        return "break"

    def update_theme(self, theme: Dict[str, str]):
        self.bg_color = theme.get("gutter_bg", "#090d16")
        self.fg_color = theme.get("gutter_fg", "#475569")
        self.border_color = theme.get("gutter_border", "#1e293b")
        self.configure(bg=self.bg_color)
        self.redraw()

    def redraw(self):
        self.delete("all")
        try:
            total_lines = int(self.text_widget.index("end-1c").split(".")[0])
        except Exception:
            total_lines = 1

        digits = max(2, len(str(total_lines)))
        needed_width = digits * 8 + 18
        if needed_width != self.gutter_width:
            self.gutter_width = needed_width
            self.configure(width=self.gutter_width)

        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            line_num, col = i.split(".")
            if col == "0":
                self.create_text(
                    self.gutter_width - 8,
                    dline[1],
                    anchor="ne",
                    text=line_num,
                    font=self.font,
                    fill=self.fg_color
                )
            next_i = self.text_widget.index(f"{i}+1display line")
            if next_i == i:
                break
            i = next_i

        w = self.winfo_width() or self.gutter_width
        h = self.winfo_height() or 2000
        self.create_line(w - 1, 0, w - 1, h, fill=self.border_color)


# =============================================================================
# DIALOG: AUTO-MASK PRESETS (Feature 2B)
# =============================================================================
class AutoMaskPresetsDialog(tk.Toplevel):
    def __init__(self, parent, engine: SanitizerEngine, text: str, on_apply: Any, theme_name: str = "dark"):
        super().__init__(parent)
        self.engine = engine
        self.text = text
        self.on_apply = on_apply
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]

        self.title("✨ Smart Auto-Masking Presets")
        self.geometry("660x600")
        self.minsize(580, 500)
        self.configure(bg=self.theme["win_bg"])
        self.transient(parent)
        self.grab_set()

        try:
            self.geometry("+%d+%d" % (parent.winfo_rootx() + 80, parent.winfo_rooty() + 60))
        except Exception:
            pass

        self.entities = self.engine.detect_preset_entities(text)
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.theme["header_bg"], padx=20, pady=16)
        hdr.pack(fill=tk.X)

        lbl_t = tk.Label(hdr, text="✨ Smart Auto-Masking Presets", font=("Segoe UI", 12, "bold"), bg=self.theme["header_bg"], fg=self.theme["text_fg"])
        lbl_t.pack(anchor="w")
        lbl_d = tk.Label(hdr, text="Automatically detect sensitive patterns and generate unique, clean placeholders.", font=("Segoe UI", 9), bg=self.theme["header_bg"], fg=self.theme["text_muted"])
        lbl_d.pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self, bg=self.theme["win_bg"], padx=20, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        self.cat_vars = {
            "ip": tk.BooleanVar(value=bool(self.entities["ip"])),
            "email": tk.BooleanVar(value=bool(self.entities["email"])),
            "uuid": tk.BooleanVar(value=bool(self.entities["uuid"])),
            "token": tk.BooleanVar(value=bool(self.entities["token"]))
        }

        cat_info = [
            ("ip", "🌐 IPv4 Addresses", self.entities["ip"], "e.g. 192.168.169.59, 10.230.194.191"),
            ("email", "📧 Email Addresses", self.entities["email"], "e.g. jordan.davis40@example.org"),
            ("uuid", "🔑 UUIDs / GUIDs", self.entities["uuid"], "e.g. d5158919-2ac4-4b83-87d0-b3d8344d2001"),
            ("token", "🛡️ API Keys / Hashes", self.entities["token"], "e.g. ghp_e0fa0427..., AKIAPYGNM2...")
        ]

        for cat_key, title, items, example in cat_info:
            card = tk.Frame(body, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1, padx=12, pady=8)
            card.pack(fill=tk.X, pady=4)

            top_row = tk.Frame(card, bg=self.theme["card_bg"])
            top_row.pack(fill=tk.X)

            count = len(items)
            chk = ttk.Checkbutton(top_row, text=f"{title} ({count} found)", variable=self.cat_vars[cat_key], command=self._update_preview)
            chk.pack(side=tk.LEFT)

            if count > 0:
                badge = tk.Label(top_row, text=f"{count} Found", font=("Segoe UI", 8, "bold"), bg="#064e3b" if self.theme_name == "dark" else "#dcfce7", fg="#6ee7b7" if self.theme_name == "dark" else "#166534", padx=6, pady=1)
                badge.pack(side=tk.RIGHT)
            else:
                badge = tk.Label(top_row, text="None found", font=("Segoe UI", 8), bg=self.theme["card_header"], fg=self.theme["text_muted"], padx=6, pady=1)
                badge.pack(side=tk.RIGHT)

            sample_text = ", ".join(items[:4]) + ("..." if len(items) > 4 else "") if items else f"Pattern: {example}"
            lbl_sample = tk.Label(card, text=sample_text, font=("Consolas", 8), bg=self.theme["card_bg"], fg=self.theme["text_muted"], anchor="w")
            lbl_sample.pack(fill=tk.X, pady=(3, 0))

        # Masking Style Radio buttons
        style_frame = tk.Frame(body, bg=self.theme["win_bg"])
        style_frame.pack(fill=tk.X, pady=(8, 4))

        lbl_style = tk.Label(style_frame, text="Masking Format:", font=("Segoe UI", 9, "bold"), bg=self.theme["win_bg"], fg=self.theme["text_fg"])
        lbl_style.pack(side=tk.LEFT, padx=(0, 10))

        self.style_mode_var = tk.StringVar(value="synthetic")
        rb_synth = ttk.Radiobutton(style_frame, text="Realistic Synthetic (e.g. 192.168.169.59, alex.smith@example.org)", variable=self.style_mode_var, value="synthetic", command=self._update_preview)
        rb_synth.pack(side=tk.LEFT, padx=(0, 12))

        rb_sem = ttk.Radiobutton(style_frame, text="Semantic Labels (e.g. IP_1, EMAIL_1)", variable=self.style_mode_var, value="semantic", command=self._update_preview)
        rb_sem.pack(side=tk.LEFT)

        lbl_prev_t = tk.Label(body, text="Generated Rules Preview (Deterministic):", font=("Segoe UI", 9, "bold"), bg=self.theme["win_bg"], fg=self.theme["text_fg"])
        lbl_prev_t.pack(anchor="w", pady=(8, 4))

        self.txt_preview = tk.Text(body, height=5, font=("Consolas", 9), bg=self.theme["text_bg"], fg=self.theme["text_fg"], bd=0, highlightbackground=self.theme["text_border"], highlightthickness=1, padx=8, pady=6)
        self.txt_preview.pack(fill=tk.X)

        self.save_to_disk_var = tk.BooleanVar(value=True)
        chk_save = ttk.Checkbutton(body, text="Save generated rules permanently to active config file (sanitizer_rules.json)", variable=self.save_to_disk_var)
        chk_save.pack(anchor="w", pady=(8, 0))

        ftr = tk.Frame(self, bg=self.theme["header_bg"], padx=20, pady=12)
        ftr.pack(fill=tk.X, side=tk.BOTTOM)

        btn_apply = tk.Button(ftr, text="⚡ Apply & Sanitize Now", command=self._apply, font=("Segoe UI", 9, "bold"), bg=self.theme["btn_success_bg"], fg=self.theme["btn_success_fg"], activebackground=self.theme["btn_success_hover"], activeforeground="#ffffff", relief=tk.FLAT, bd=0, padx=16, pady=6, cursor="hand2")
        btn_apply.pack(side=tk.RIGHT, padx=(8, 0))

        btn_cancel = tk.Button(ftr, text="Cancel", command=self.destroy, font=("Segoe UI", 9), bg=self.theme["btn_secondary_bg"], fg=self.theme["btn_secondary_fg"], activebackground=self.theme["btn_secondary_hover"], relief=tk.FLAT, bd=0, padx=12, pady=6, cursor="hand2")
        btn_cancel.pack(side=tk.RIGHT)

        self._update_preview()

    def _update_preview(self):
        selected_cats = [cat for cat, var in self.cat_vars.items() if var.get()]
        mode = getattr(self, "style_mode_var", None)
        mode_val = mode.get() if mode else "synthetic"
        generated = self.engine.generate_preset_rules(self.text, selected_cats, mode=mode_val)
        self.txt_preview.delete("1.0", tk.END)
        if not generated:
            self.txt_preview.insert(tk.END, "# No new rules to generate with current selection.")
        else:
            lines = [f"{orig}  ➔  {placeholder}" for orig, placeholder in generated.items()]
            self.txt_preview.insert(tk.END, "\n".join(lines))

    def _apply(self):
        selected_cats = [cat for cat, var in self.cat_vars.items() if var.get()]
        mode_val = self.style_mode_var.get()
        generated = self.engine.generate_preset_rules(self.text, selected_cats, mode=mode_val)
        if not generated:
            messagebox.showinfo("Auto-Mask Presets", "No new rules were generated for the selected categories.")
            self.destroy()
            return

        for orig, placeholder in generated.items():
            self.engine.add_rule(orig, placeholder)

        if self.save_to_disk_var.get():
            self.engine.save_config()

        self.on_apply(len(generated))
        self.destroy()


# =============================================================================
# DIALOG: LEAK SCANNER & PARTIAL LEAK INSPECTOR (Feature 2C)
# =============================================================================
# DIALOG: SECURITY LEAK & PARTIAL MATCH INSPECTOR
# =============================================================================
class LeakDetailsDialog(tk.Toplevel):
    def __init__(self, parent, partial_leaks: List[Dict[str, Any]], generic_leaks: List[Dict[str, Any]], on_quick_mask_fix: Any, theme_name: str = "dark"):
        super().__init__(parent)
        self.partial_leaks = list(partial_leaks)
        self.generic_leaks = list(generic_leaks)
        self.on_quick_mask_fix = on_quick_mask_fix
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.active_filter = "ALL"

        self.title("⚠️ Security Leak & Secret Exposure Inspector")
        self.geometry("820x620")
        self.minsize(700, 480)
        self.configure(bg=self.theme["win_bg"])
        self.transient(parent)

        try:
            self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 40))
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # Header
        self.hdr = tk.Frame(self, bg=self.theme["header_bg"], padx=20, pady=12)
        self.hdr.pack(fill=tk.X)

        top_row = tk.Frame(self.hdr, bg=self.theme["header_bg"])
        top_row.pack(fill=tk.X)

        lbl_t = tk.Label(top_row, text="⚠️ Security Leak & Secret Exposure Inspector", font=("Segoe UI", 12, "bold"), bg=self.theme["header_bg"], fg=self.theme["text_fg"])
        lbl_t.pack(side=tk.LEFT)

        # Severity badges container in header
        self.badge_box = tk.Frame(top_row, bg=self.theme["header_bg"])
        self.badge_box.pack(side=tk.RIGHT)

        self.lbl_d = tk.Label(self.hdr, text="", font=("Segoe UI", 9), bg=self.theme["header_bg"], fg=self.theme["text_muted"])
        self.lbl_d.pack(anchor="w", pady=(3, 0))

        # Filter bar
        self.filter_bar = tk.Frame(self, bg=self.theme["card_bg"], padx=16, pady=8, highlightbackground=self.theme["card_border"], highlightthickness=1)
        self.filter_bar.pack(fill=tk.X)

        self.filter_btns: Dict[str, tk.Button] = {}

        # Content container
        container = tk.Frame(self, bg=self.theme["win_bg"], padx=16, pady=8)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg=self.theme["win_bg"], bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme["win_bg"])

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_canvas_configure(e):
            self.canvas.itemconfig(self.canvas_window, width=e.width)
        self.canvas.bind("<Configure>", _on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer
        ftr = tk.Frame(self, bg=self.theme["header_bg"], padx=20, pady=10)
        ftr.pack(fill=tk.X, side=tk.BOTTOM)
        btn_close = tk.Button(ftr, text="Close", command=self.destroy, font=("Segoe UI", 9), bg=self.theme["btn_secondary_bg"], fg=self.theme["btn_secondary_fg"], relief=tk.FLAT, bd=0, padx=14, pady=5, cursor="hand2")
        btn_close.pack(side=tk.RIGHT)

        self._refresh_content()

    def _refresh_content(self):
        # Update counts
        crit_count = sum(1 for l in self.generic_leaks if l.get("severity") == "CRITICAL")
        high_count = sum(1 for l in self.generic_leaks if l.get("severity") == "HIGH") + len(self.partial_leaks)
        med_count = sum(1 for l in self.generic_leaks if l.get("severity") == "MEDIUM")
        total_count = len(self.generic_leaks) + len(self.partial_leaks)

        self.lbl_d.config(text=f"Detected {total_count} issue(s) that may expose sensitive credentials if shared.")

        # Update header severity badges
        for child in self.badge_box.winfo_children():
            child.destroy()

        if crit_count > 0:
            b_crit = tk.Label(self.badge_box, text=f"🔴 {crit_count} Critical", font=("Segoe UI", 8, "bold"), bg="#7f1d1d" if self.theme_name == "dark" else "#fee2e2", fg="#fecaca" if self.theme_name == "dark" else "#991b1b", padx=8, pady=2)
            b_crit.pack(side=tk.LEFT, padx=3)
        if high_count > 0:
            b_high = tk.Label(self.badge_box, text=f"🟠 {high_count} High", font=("Segoe UI", 8, "bold"), bg="#7c2d12" if self.theme_name == "dark" else "#ffedd5", fg="#fed7aa" if self.theme_name == "dark" else "#9a3412", padx=8, pady=2)
            b_high.pack(side=tk.LEFT, padx=3)
        if med_count > 0:
            b_med = tk.Label(self.badge_box, text=f"🟡 {med_count} Medium", font=("Segoe UI", 8, "bold"), bg="#713f12" if self.theme_name == "dark" else "#fef9c3", fg="#fef08a" if self.theme_name == "dark" else "#854d0e", padx=8, pady=2)
            b_med.pack(side=tk.LEFT, padx=3)

        # Update filter bar buttons
        for child in self.filter_bar.winfo_children():
            child.destroy()

        filters = [
            ("ALL", f"All ({total_count})"),
            ("CRITICAL", f"🔴 Critical ({crit_count})"),
            ("HIGH", f"🟠 High ({high_count})"),
            ("MEDIUM", f"🟡 Medium ({med_count})"),
            ("PARTIAL", f"⚠️ Partial Leaks ({len(self.partial_leaks)})")
        ]

        for f_key, f_label in filters:
            is_active = (self.active_filter == f_key)
            bg_c = self.theme["btn_primary_bg"] if is_active else self.theme["card_bg"]
            fg_c = self.theme["btn_primary_fg"] if is_active else self.theme["text_muted"]
            btn = tk.Button(
                self.filter_bar,
                text=f_label,
                command=lambda k=f_key: self._set_filter(k),
                font=("Segoe UI", 8, "bold" if is_active else "normal"),
                bg=bg_c,
                fg=fg_c,
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=3,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Clear scrollable frame
        for child in self.scrollable_frame.winfo_children():
            child.destroy()

        if total_count == 0:
            empty_card = tk.Frame(self.scrollable_frame, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1, padx=20, pady=24)
            empty_card.pack(fill=tk.X, pady=20)
            lbl_clean = tk.Label(empty_card, text="🎉 All security issues have been resolved or dismissed!", font=("Segoe UI", 11, "bold"), bg=self.theme["card_bg"], fg="#a7f3d0" if self.theme_name == "dark" else "#166534")
            lbl_clean.pack()
            lbl_clean_sub = tk.Label(empty_card, text="Your sanitized payload is clean of known unmasked secrets and ready to share.", font=("Segoe UI", 9), bg=self.theme["card_bg"], fg=self.theme["text_muted"])
            lbl_clean_sub.pack(pady=(4, 0))
            return

        # Render Partial Leaks if matching filter
        if self.active_filter in ("ALL", "HIGH", "PARTIAL") and self.partial_leaks:
            lbl_sec1 = tk.Label(self.scrollable_frame, text=f"PARTIAL SECRET LEAKS ({len(self.partial_leaks)})", font=("Segoe UI", 9, "bold"), bg=self.theme["win_bg"], fg="#fed7aa" if self.theme_name == "dark" else "#9a3412")
            lbl_sec1.pack(anchor="w", pady=(6, 4))

            for idx, leak in enumerate(self.partial_leaks):
                self._render_partial_card(leak, idx)

        # Render Generic Leaks if matching filter
        matching_generic = [
            l for l in self.generic_leaks
            if self.active_filter == "ALL" or l.get("severity") == self.active_filter
        ]

        if matching_generic:
            lbl_sec2 = tk.Label(self.scrollable_frame, text=f"UNMASKED CREDENTIALS & TOKENS ({len(matching_generic)})", font=("Segoe UI", 9, "bold"), bg=self.theme["win_bg"], fg="#fca5a5" if self.theme_name == "dark" else "#991b1b")
            lbl_sec2.pack(anchor="w", pady=(10, 4))

            for idx, leak in enumerate(matching_generic):
                self._render_generic_card(leak, idx)

    def _set_filter(self, filter_key: str):
        self.active_filter = filter_key
        self._refresh_content()

    def _render_partial_card(self, leak: Dict[str, Any], idx: int):
        card = tk.Frame(self.scrollable_frame, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1, padx=14, pady=10)
        card.pack(fill=tk.X, pady=4)

        # Top row
        top = tk.Frame(card, bg=self.theme["card_bg"])
        top.pack(fill=tk.X)

        pill = tk.Label(top, text="⚠️ PARTIAL LEAK", font=("Segoe UI", 7, "bold"), bg="#431407" if self.theme_name == "dark" else "#fff7ed", fg="#ffedd5" if self.theme_name == "dark" else "#c2410c", padx=6, pady=1)
        pill.pack(side=tk.LEFT)

        info_lbl = tk.Label(top, text=f" Line {leak.get('line_num', 1)}, Col {leak.get('col', 0)}: Secret '{leak['secret']}' in '{leak['enclosing_token']}'", font=("Segoe UI", 9, "bold"), bg=self.theme["card_bg"], fg=self.theme["text_fg"])
        info_lbl.pack(side=tk.LEFT, padx=6)

        # Action Buttons
        btn_box = tk.Frame(top, bg=self.theme["card_bg"])
        btn_box.pack(side=tk.RIGHT)

        tok = leak.get("enclosing_token", leak.get("secret", ""))

        btn_synth = tk.Button(
            btn_box,
            text="⚡ Synthetic",
            command=lambda t=tok: self._quick_fix(t, "synthetic"),
            font=("Segoe UI", 8, "bold"),
            bg="#065f46" if self.theme_name == "dark" else "#d1fae5",
            fg="#a7f3d0" if self.theme_name == "dark" else "#065f46",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_synth.pack(side=tk.LEFT, padx=2)

        btn_mask = tk.Button(
            btn_box,
            text="🏷️ Placeholder",
            command=lambda t=tok: self._quick_fix(t, "placeholder"),
            font=("Segoe UI", 8),
            bg=self.theme["btn_primary_bg"],
            fg=self.theme["btn_primary_fg"],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_mask.pack(side=tk.LEFT, padx=2)

        btn_ign = tk.Button(
            btn_box,
            text="✕",
            command=lambda i=idx: self._ignore_partial(i),
            font=("Segoe UI", 8),
            bg=self.theme["card_bg"],
            fg=self.theme["text_muted"],
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2"
        )
        btn_ign.pack(side=tk.LEFT, padx=2)

        # Context snippet
        ctx = leak.get("context", "")
        if ctx:
            ctx_lbl = tk.Label(card, text=f"Context: {ctx}", font=("Consolas", 8), bg=self.theme["card_bg"], fg=self.theme["text_muted"], anchor="w")
            ctx_lbl.pack(fill=tk.X, pady=(4, 0))

    def _render_generic_card(self, leak: Dict[str, Any], idx: int):
        card = tk.Frame(self.scrollable_frame, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1, padx=14, pady=10)
        card.pack(fill=tk.X, pady=4)

        severity = leak.get("severity", "HIGH")
        sev_bg = "#7f1d1d" if severity == "CRITICAL" else ("#7c2d12" if severity == "HIGH" else "#713f12")
        sev_fg = "#fecaca" if severity == "CRITICAL" else ("#fed7aa" if severity == "HIGH" else "#fef08a")
        if self.theme_name == "light":
            sev_bg = "#fee2e2" if severity == "CRITICAL" else ("#ffedd5" if severity == "HIGH" else "#fef9c3")
            sev_fg = "#991b1b" if severity == "CRITICAL" else ("#9a3412" if severity == "HIGH" else "#854d0e")

        sev_icon = "🔴" if severity == "CRITICAL" else ("🟠" if severity == "HIGH" else "🟡")

        top = tk.Frame(card, bg=self.theme["card_bg"])
        top.pack(fill=tk.X)

        pill = tk.Label(top, text=f"{sev_icon} {severity}", font=("Segoe UI", 7, "bold"), bg=sev_bg, fg=sev_fg, padx=6, pady=1)
        pill.pack(side=tk.LEFT)

        type_lbl = tk.Label(top, text=f" {leak['type']} (Line {leak.get('line_num', 1)}, Col {leak.get('col', 0)})", font=("Segoe UI", 9, "bold"), bg=self.theme["card_bg"], fg=self.theme["text_fg"])
        type_lbl.pack(side=tk.LEFT, padx=6)

        # Actions
        btn_box = tk.Frame(top, bg=self.theme["card_bg"])
        btn_box.pack(side=tk.RIGHT)

        secret_val = leak.get("secret_value", leak.get("matched", ""))

        btn_synth = tk.Button(
            btn_box,
            text="⚡ Synthetic",
            command=lambda v=secret_val: self._quick_fix(v, "synthetic"),
            font=("Segoe UI", 8, "bold"),
            bg="#065f46" if self.theme_name == "dark" else "#d1fae5",
            fg="#a7f3d0" if self.theme_name == "dark" else "#065f46",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_synth.pack(side=tk.LEFT, padx=2)

        btn_mask = tk.Button(
            btn_box,
            text="🏷️ Placeholder",
            command=lambda v=secret_val: self._quick_fix(v, "placeholder"),
            font=("Segoe UI", 8),
            bg=self.theme["btn_primary_bg"],
            fg=self.theme["btn_primary_fg"],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        btn_mask.pack(side=tk.LEFT, padx=2)

        btn_ign = tk.Button(
            btn_box,
            text="✕",
            command=lambda lk=leak: self._ignore_generic(lk),
            font=("Segoe UI", 8),
            bg=self.theme["card_bg"],
            fg=self.theme["text_muted"],
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2"
        )
        btn_ign.pack(side=tk.LEFT, padx=2)

        # Matched value preview
        matched_str = leak.get("matched", "")
        if len(matched_str) > 75:
            matched_str = matched_str[:72] + "..."

        val_box = tk.Frame(card, bg=self.theme["win_bg"], padx=8, pady=4)
        val_box.pack(fill=tk.X, pady=(5, 0))

        lbl_val = tk.Label(val_box, text=f"Secret: {matched_str}", font=("Consolas", 8), bg=self.theme["win_bg"], fg=self.theme["text_fg"], anchor="w")
        lbl_val.pack(anchor="w")

        # Context snippet
        ctx = leak.get("context", "")
        if ctx:
            ctx_lbl = tk.Label(card, text=f"Context: {ctx}", font=("Consolas", 8), bg=self.theme["card_bg"], fg=self.theme["text_muted"], anchor="w")
            ctx_lbl.pack(fill=tk.X, pady=(3, 0))

    def _ignore_partial(self, idx: int):
        if 0 <= idx < len(self.partial_leaks):
            self.partial_leaks.pop(idx)
            self._refresh_content()

    def _ignore_generic(self, leak: Dict[str, Any]):
        if leak in self.generic_leaks:
            self.generic_leaks.remove(leak)
            self._refresh_content()

    def _quick_fix(self, token: str, mode: str = "synthetic"):
        try:
            self.on_quick_mask_fix(token, mode=mode)
        except TypeError:
            self.on_quick_mask_fix(token)
        self.destroy()


# =============================================================================
# DIALOG: SIDE-BY-SIDE VISUAL DIFF (Feature 4B)
# =============================================================================
class VisualDiffDialog(tk.Toplevel):
    def __init__(
        self,
        parent,
        original_text: str,
        transformed_text: str,
        title: str = "Visual Diff",
        mode: str = "sanitize",
        theme_name: str = "dark",
        spans: Optional[List[Any]] = None
    ):
        super().__init__(parent)
        self.original_text = original_text
        self.transformed_text = transformed_text
        self.mode = mode
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.spans = spans or []

        self.title(title)
        self.geometry("1120x720")
        self.minsize(860, 520)
        self.configure(bg=self.theme["win_bg"])
        self.transient(parent)

        self.diff_items: List[Dict[str, Any]] = []
        self.current_diff_idx = 0

        self._build_ui()
        self._compute_and_render_diff()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.theme["header_bg"], padx=16, pady=10)
        hdr.pack(fill=tk.X)

        title_frame = tk.Frame(hdr, bg=self.theme["header_bg"])
        title_frame.pack(side=tk.LEFT)

        left_label = "BEFORE: Original Input" if self.mode == "sanitize" else "BEFORE: AI Response"
        right_label = "AFTER: Sanitized Payload" if self.mode == "sanitize" else "AFTER: Restored True Payload"

        lbl_t = tk.Label(title_frame, text=f"🔍 Visual Diff: {left_label}  ➔  {right_label}", font=("Segoe UI", 11, "bold"), bg=self.theme["header_bg"], fg=self.theme["text_fg"])
        lbl_t.pack(anchor="w")

        self.lbl_stats = tk.Label(title_frame, text="Analyzing differences...", font=("Segoe UI", 8), bg=self.theme["header_bg"], fg=self.theme["text_muted"])
        self.lbl_stats.pack(anchor="w")

        nav_frame = tk.Frame(hdr, bg=self.theme["header_bg"])
        nav_frame.pack(side=tk.RIGHT)

        self.lbl_nav_pos = tk.Label(nav_frame, text="0 / 0", font=("Consolas", 9, "bold"), bg=self.theme["header_bg"], fg=self.theme["text_fg"])
        self.lbl_nav_pos.pack(side=tk.LEFT, padx=(0, 10))

        btn_prev = tk.Button(nav_frame, text="▲ Prev Change", command=self._prev_change, font=("Segoe UI", 8, "bold"), bg=self.theme["btn_secondary_bg"], fg=self.theme["btn_secondary_fg"], relief=tk.FLAT, bd=0, padx=8, pady=4, cursor="hand2")
        btn_prev.pack(side=tk.LEFT, padx=3)

        btn_next = tk.Button(nav_frame, text="▼ Next Change", command=self._next_change, font=("Segoe UI", 8, "bold"), bg=self.theme["btn_secondary_bg"], fg=self.theme["btn_secondary_fg"], relief=tk.FLAT, bd=0, padx=8, pady=4, cursor="hand2")
        btn_next.pack(side=tk.LEFT, padx=3)

        btn_close = tk.Button(nav_frame, text="✕ Close", command=self.destroy, font=("Segoe UI", 8, "bold"), bg=self.theme["btn_danger_bg"], fg=self.theme["btn_danger_fg"], relief=tk.FLAT, bd=0, padx=10, pady=4, cursor="hand2")
        btn_close.pack(side=tk.LEFT, padx=(12, 0))

        pane_container = tk.Frame(self, bg=self.theme["win_bg"], padx=10, pady=8)
        pane_container.pack(fill=tk.BOTH, expand=True)

        left_card = tk.Frame(pane_container, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1)
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        left_hdr = tk.Frame(left_card, bg=self.theme["card_header"], padx=10, pady=6)
        left_hdr.pack(fill=tk.X)
        tk.Label(left_hdr, text=left_label, font=("Segoe UI", 9, "bold"), bg=self.theme["card_header"], fg=self.theme["text_fg"]).pack(side=tk.LEFT)
        badge_del = tk.Label(left_hdr, text="■ Red = Replaced", font=("Segoe UI", 8, "bold"), bg=self.theme["diff_del_bg"], fg=self.theme["diff_del_fg"], padx=6, pady=1)
        badge_del.pack(side=tk.RIGHT)

        self.txt_left = tk.Text(left_card, wrap=tk.NONE, font=("Consolas", 10), bg=self.theme["text_bg"], fg=self.theme["text_fg"], bd=0, padx=8, pady=8)
        self.txt_left.pack(fill=tk.BOTH, expand=True)

        right_card = tk.Frame(pane_container, bg=self.theme["card_bg"], highlightbackground=self.theme["card_border"], highlightthickness=1)
        right_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        right_hdr = tk.Frame(right_card, bg=self.theme["card_header"], padx=10, pady=6)
        right_hdr.pack(fill=tk.X)
        tk.Label(right_hdr, text=right_label, font=("Segoe UI", 9, "bold"), bg=self.theme["card_header"], fg=self.theme["text_fg"]).pack(side=tk.LEFT)
        badge_add = tk.Label(right_hdr, text="■ Green = Transformed", font=("Segoe UI", 8, "bold"), bg=self.theme["diff_add_bg"], fg=self.theme["diff_add_fg"], padx=6, pady=1)
        badge_add.pack(side=tk.RIGHT)

        self.txt_right = tk.Text(right_card, wrap=tk.NONE, font=("Consolas", 10), bg=self.theme["text_bg"], fg=self.theme["text_fg"], bd=0, padx=8, pady=8)
        self.txt_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll = ttk.Scrollbar(right_card, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _sync_scroll(*args):
            self.txt_left.yview(*args)
            self.txt_right.yview(*args)

        v_scroll.config(command=_sync_scroll)
        self.txt_left.config(yscrollcommand=v_scroll.set)
        self.txt_right.config(yscrollcommand=v_scroll.set)

        def _on_mousewheel(event):
            delta = int(-1 * (event.delta / 120))
            self.txt_left.yview_scroll(delta, "units")
            self.txt_right.yview_scroll(delta, "units")
            return "break"

        self.txt_left.bind("<MouseWheel>", _on_mousewheel)
        self.txt_right.bind("<MouseWheel>", _on_mousewheel)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Up>", lambda e: self._prev_change())
        self.bind("<Down>", lambda e: self._next_change())

    def _compute_and_render_diff(self):
        self.txt_left.delete("1.0", tk.END)
        self.txt_right.delete("1.0", tk.END)

        self.txt_left.insert(tk.END, self.original_text)
        self.txt_right.insert(tk.END, self.transformed_text)

        self.txt_left.tag_config("diff_del", background=self.theme["diff_del_bg"], foreground=self.theme["diff_del_fg"])
        self.txt_right.tag_config("diff_add", background=self.theme["diff_add_bg"], foreground=self.theme["diff_add_fg"])
        self.txt_left.tag_config("diff_focus", background="#854d0e", foreground="#ffffff")
        self.txt_right.tag_config("diff_focus", background="#854d0e", foreground="#ffffff")

        self.diff_items = []

        if self.spans:
            orig_search_pos = 0
            for t_start, t_end, matched_orig, repl_val, orig_k, orig_v in self.spans:
                o_idx = self.original_text.find(matched_orig, orig_search_pos)
                if o_idx == -1:
                    o_idx = self.original_text.find(matched_orig)

                if o_idx != -1:
                    o_start = o_idx
                    o_end = o_idx + len(matched_orig)
                    orig_search_pos = o_end
                else:
                    o_start = 0
                    o_end = 0

                self.diff_items.append({
                    "orig_span": (o_start, o_end),
                    "trans_span": (t_start, t_end),
                    "matched": matched_orig,
                    "replacement": repl_val
                })
        else:
            toks1 = re.findall(r"\w+|\W+", self.original_text)
            toks2 = re.findall(r"\w+|\W+", self.transformed_text)
            sm = difflib.SequenceMatcher(None, toks1, toks2)

            pos1 = 0
            tok1_spans = []
            for t in toks1:
                tok1_spans.append((pos1, pos1 + len(t)))
                pos1 += len(t)

            pos2 = 0
            tok2_spans = []
            for t in toks2:
                tok2_spans.append((pos2, pos2 + len(t)))
                pos2 += len(t)

            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "equal":
                    o_s = tok1_spans[i1][0] if i1 < len(tok1_spans) else len(self.original_text)
                    o_e = tok1_spans[i2 - 1][1] if 0 < i2 <= len(tok1_spans) else o_s
                    t_s = tok2_spans[j1][0] if j1 < len(tok2_spans) else len(self.transformed_text)
                    t_e = tok2_spans[j2 - 1][1] if 0 < j2 <= len(tok2_spans) else t_s

                    self.diff_items.append({
                        "orig_span": (o_s, o_e),
                        "trans_span": (t_s, t_e),
                        "matched": self.original_text[o_s:o_e],
                        "replacement": self.transformed_text[t_s:t_e]
                    })

        for item in self.diff_items:
            o_s, o_e = item["orig_span"]
            t_s, t_e = item["trans_span"]
            if o_e > o_s:
                self.txt_left.tag_add("diff_del", f"1.0 + {o_s} chars", f"1.0 + {o_e} chars")
            if t_e > t_s:
                self.txt_right.tag_add("diff_add", f"1.0 + {t_s} chars", f"1.0 + {t_e} chars")

        total = len(self.diff_items)
        orig_lines = len(self.original_text.splitlines())
        self.lbl_stats.config(text=f"{total} replacement change(s) across {orig_lines} lines.")

        if total > 0:
            self.current_diff_idx = 0
            self._highlight_diff_at(0)
        else:
            self.lbl_nav_pos.config(text="0 / 0")

    def _highlight_diff_at(self, idx: int):
        if not self.diff_items or idx < 0 or idx >= len(self.diff_items):
            return

        self.current_diff_idx = idx
        self.lbl_nav_pos.config(text=f"{idx + 1} / {len(self.diff_items)}")

        self.txt_left.tag_remove("diff_focus", "1.0", tk.END)
        self.txt_right.tag_remove("diff_focus", "1.0", tk.END)

        item = self.diff_items[idx]
        o_s, o_e = item["orig_span"]
        t_s, t_e = item["trans_span"]

        left_pos = f"1.0 + {o_s} chars"
        right_pos = f"1.0 + {t_s} chars"

        if o_e > o_s:
            self.txt_left.tag_add("diff_focus", left_pos, f"1.0 + {o_e} chars")
        if t_e > t_s:
            self.txt_right.tag_add("diff_focus", right_pos, f"1.0 + {t_e} chars")

        self.txt_left.see(left_pos)
        self.txt_right.see(right_pos)

    def _prev_change(self):
        if not self.diff_items:
            return
        new_idx = (self.current_diff_idx - 1) % len(self.diff_items)
        self._highlight_diff_at(new_idx)

    def _next_change(self):
        if not self.diff_items:
            return
        new_idx = (self.current_diff_idx + 1) % len(self.diff_items)
        self._highlight_diff_at(new_idx)


class SanitizerStudioApp:
    def __init__(self, root: tk.Tk, initial_tab: str = "sanitize"):
        self.root = root
        self.root.title("Sanitizer Studio")
        self.root.geometry("1140x820")
        self.root.minsize(900, 640)

        # Default to sleek modern dark theme
        self.current_theme = "dark"
        self.theme = THEMES[self.current_theme]
        self.active_tab_name = initial_tab
        self.registered_buttons: List[Tuple[tk.Button, str]] = []
        self.registered_cards: List[tk.Frame] = []
        self.registered_card_headers: List[tk.Frame] = []
        self.gutters: List[LineNumberGutter] = []

        self.engine = SanitizerEngine(DEFAULT_CONFIG_PATH)
        Clipboard.register_root(self.root)

        # Tab 1 variables
        self.san_case_insensitive = tk.BooleanVar(value=False)
        self.san_word_boundaries = tk.BooleanVar(value=True)
        self.san_encoding_aware = tk.BooleanVar(value=True)
        self.san_layout_mode = "split"
        self.san_spans: List[Tuple[int, int, str, str, str, str]] = []

        # Tab 2 variables
        self.unsan_case_insensitive = tk.BooleanVar(value=False)
        self.unsan_word_boundaries = tk.BooleanVar(value=True)
        self.unsan_encoding_aware = tk.BooleanVar(value=True)
        self.unsan_layout_mode = "split"
        self.unsan_spans: List[Tuple[int, int, str, str, str, str]] = []

        # Tab 3 variables
        self.rules_search_var = tk.StringVar(value="")
        self.show_collisions_only_var = tk.BooleanVar(value=False)

        # Clipboard Auto-Wipe Timer state
        self._clip_wipe_job = None
        self.clip_wipe_remaining = 0
        self.clip_wipe_expected = ""

        # Thread-safe async task queue
        self.async_queue = queue.Queue()
        self._check_async_queue()

        self._configure_ttk_styles()
        self._create_widgets()
        self.apply_theme_colors()
        self.switch_tab(initial_tab)
        self.refresh_rules_table()
        self._update_status_bar()

    def _configure_ttk_styles(self):
        self.style = ttk.Style()
        for t in ("clam", "default"):
            try:
                self.style.theme_use(t)
                break
            except Exception:
                pass

    def _check_async_queue(self):
        try:
            while True:
                task = self.async_queue.get_nowait()
                action = task[0]
                if action == "sanitize":
                    _, sanitized, count, spans, breakdown, leaks, partial_leaks, preflights = task
                    self._on_sanitize_complete(sanitized, count, spans, breakdown, leaks, partial_leaks, preflights)
                elif action == "unsanitize":
                    _, restored, count, spans, breakdown = task
                    self._on_unsanitize_complete(restored, count, spans, breakdown)
        except queue.Empty:
            pass
        except Exception:
            pass
        finally:
            try:
                self.root.after(40, self._check_async_queue)
            except Exception:
                pass

    def make_btn(
        self,
        parent: Any,
        text: str,
        command: Any,
        kind: str = "secondary",
        padx: int = 14,
        pady: int = 6,
        font: Tuple[str, int, str] = ("Segoe UI", 9, "bold")
    ) -> tk.Button:
        """Creates a modern flat button with custom hover animation."""
        theme = THEMES[self.current_theme]
        bg = theme.get(f"btn_{kind}_bg", theme["btn_secondary_bg"])
        fg = theme.get(f"btn_{kind}_fg", theme["btn_secondary_fg"])

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            relief=tk.FLAT,
            bd=0,
            bg=bg,
            fg=fg,
            activebackground=theme.get(f"btn_{kind}_hover", bg),
            activeforeground=fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2"
        )

        def on_enter(e):
            t = THEMES[self.current_theme]
            btn.config(bg=t.get(f"btn_{kind}_hover", t.get(f"btn_{kind}_bg")))

        def on_leave(e):
            t = THEMES[self.current_theme]
            btn.config(bg=t.get(f"btn_{kind}_bg"))

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        self.registered_buttons.append((btn, kind))
        return btn

    def _create_widgets(self):
        # ---------------- Modern Header Bar ----------------
        self.header_frame = tk.Frame(self.root, padx=16, pady=10)
        self.header_frame.pack(fill=tk.X)

        # Brand Title
        brand_box = tk.Frame(self.header_frame, bg=self.header_frame.cget("bg"))
        brand_box.pack(side=tk.LEFT)

        lbl_icon = tk.Label(brand_box, text="🛡️", font=("Segoe UI", 14), bg=self.header_frame.cget("bg"))
        lbl_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_title = tk.Label(brand_box, text="Sanitizer Studio", font=("Segoe UI", 12, "bold"))
        self.lbl_title.pack(side=tk.LEFT)

        self.badge_version = tk.Label(brand_box, text="v3.0", font=("Segoe UI", 8, "bold"), padx=6, pady=1)
        self.badge_version.pack(side=tk.LEFT, padx=(8, 14))

        # Center: Segmented Navigation Pill Control
        self.nav_capsule = tk.Frame(self.header_frame, padx=3, pady=3)
        self.nav_capsule.pack(side=tk.LEFT, padx=(10, 0))

        self.nav_buttons = {}
        for tab_id, label in [("sanitize", "🛡️ Sanitize"), ("unsanitize", "🔄 Unsanitize"), ("rules", "📋 Manage Rules")]:
            btn = tk.Button(
                self.nav_capsule,
                text=label,
                relief=tk.FLAT,
                bd=0,
                padx=14,
                pady=5,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                command=lambda tid=tab_id: self.switch_tab(tid)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.nav_buttons[tab_id] = btn

        # Right Actions
        self.btn_theme_toggle = self.make_btn(self.header_frame, "☀️ Light Mode", self.toggle_theme, kind="secondary", padx=10, pady=4)
        self.btn_theme_toggle.pack(side=tk.RIGHT, padx=(6, 0))

        btn_reload = self.make_btn(self.header_frame, "Reload Rules", self.reload_config, kind="secondary", padx=10, pady=4)
        btn_reload.pack(side=tk.RIGHT, padx=(4, 0))

        btn_browse = self.make_btn(self.header_frame, "Switch Config...", self.browse_config, kind="secondary", padx=10, pady=4)
        btn_browse.pack(side=tk.RIGHT, padx=(4, 0))

        # Config Path Pill
        self.lbl_config = tk.Label(self.header_frame, text=f"📄 {os.path.basename(self.engine.config_path)}", font=("Consolas", 9), padx=8, pady=3)
        self.lbl_config.pack(side=tk.RIGHT, padx=(0, 8))

        # ---------------- Workspace Pages Container ----------------
        self.pages_container = tk.Frame(self.root, padx=16, pady=8)
        self.pages_container.pack(fill=tk.BOTH, expand=True)

        self.page_sanitize = tk.Frame(self.pages_container)
        self.page_unsanitize = tk.Frame(self.pages_container)
        self.page_rules = tk.Frame(self.pages_container)

        self._build_sanitize_tab()
        self._build_unsanitize_tab()
        self._build_rules_tab()

        # ---------------- Modern Sleek Status Bar ----------------
        self.status_bar_frame = tk.Frame(self.root, padx=16, pady=6)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_bar = tk.Label(
            self.status_bar_frame,
            text="🟢 Engine Ready",
            anchor=tk.W,
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(side=tk.LEFT)

        self.status_right = tk.Label(
            self.status_bar_frame,
            text="",
            font=("Segoe UI", 8),
            anchor=tk.E
        )
        self.status_right.pack(side=tk.RIGHT)

        # Dynamic Collision Warning Button
        self.btn_collision_warn = tk.Button(
            self.status_bar_frame,
            text="",
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.show_collision_details
        )

        # Clipboard Auto-Wipe Indicator Frame
        self.clip_wipe_frame = tk.Frame(self.status_bar_frame)
        self.lbl_clip_countdown = tk.Label(
            self.clip_wipe_frame,
            text="⏱️ Sensitive Clipboard: 60s",
            font=("Segoe UI", 8, "bold"),
            bg="#451a03",
            fg="#fef3c7",
            padx=8,
            pady=2
        )
        self.lbl_clip_countdown.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_clip_keep = tk.Button(
            self.clip_wipe_frame,
            text="Keep",
            command=self.cancel_clipboard_wipe,
            font=("Segoe UI", 8),
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            bg="#292524",
            fg="#e7e5e4"
        )
        self.btn_clip_keep.pack(side=tk.LEFT, padx=2)

        self.btn_clip_wipe_now = tk.Button(
            self.clip_wipe_frame,
            text="Clear Now",
            command=self.wipe_clipboard_now,
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            bg="#7f1d1d",
            fg="#fee2e2"
        )
        self.btn_clip_wipe_now.pack(side=tk.LEFT, padx=(2, 0))

    def switch_tab(self, tab_id: str):
        """Switches active workspace frame with modern segmented pill animation."""
        self.active_tab_name = tab_id

        # Hide all pages
        self.page_sanitize.pack_forget()
        self.page_unsanitize.pack_forget()
        self.page_rules.pack_forget()

        # Show target page
        if tab_id == "unsanitize":
            self.page_unsanitize.pack(fill=tk.BOTH, expand=True)
        elif tab_id == "rules":
            self.page_rules.pack(fill=tk.BOTH, expand=True)
        else:
            self.page_sanitize.pack(fill=tk.BOTH, expand=True)

        # Update pill states
        theme = THEMES[self.current_theme]
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.config(bg=theme["nav_active_bg"], fg=theme["nav_active_fg"])
            else:
                btn.config(bg=theme["nav_bg"], fg=theme["nav_inactive_fg"])

    # =========================================================================
    # TAB 1: SANITIZE WORKSPACE
    # =========================================================================
    def _build_sanitize_tab(self):
        parent = self.page_sanitize

        # Options Toolbar Bar
        self.san_ctrl_frame = tk.Frame(parent, pady=4)
        self.san_ctrl_frame.pack(fill=tk.X, pady=(0, 6))

        chk_wb = ttk.Checkbutton(self.san_ctrl_frame, text="Word boundaries (\\b)", variable=self.san_word_boundaries)
        chk_wb.pack(side=tk.LEFT, padx=(0, 10))

        chk_case = ttk.Checkbutton(self.san_ctrl_frame, text="Case-insensitive", variable=self.san_case_insensitive)
        chk_case.pack(side=tk.LEFT, padx=(0, 10))

        chk_enc = ttk.Checkbutton(self.san_ctrl_frame, text="Encoding-aware (%20, \\\\)", variable=self.san_encoding_aware)
        chk_enc.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_san_layout = self.make_btn(self.san_ctrl_frame, "⬒ Stacked View", self.toggle_sanitize_layout, kind="secondary", padx=10, pady=4)
        self.btn_san_layout.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_san_presets = self.make_btn(self.san_ctrl_frame, "✨ Auto-Mask Presets", self.open_presets_dialog, kind="secondary", padx=10, pady=4)
        self.btn_san_presets.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_san_diff = self.make_btn(self.san_ctrl_frame, "🔍 Visual Diff", self.open_sanitize_diff, kind="secondary", padx=10, pady=4)
        self.btn_san_diff.pack(side=tk.LEFT)

        # Right Action Buttons: Paste & Sanitize and Sanitize
        btn_san_main = self.make_btn(self.san_ctrl_frame, "⚡ Sanitize (Ctrl+Enter)", self.sanitize_action, kind="primary", padx=16, pady=5)
        btn_san_main.pack(side=tk.RIGHT, padx=(4, 0))

        btn_paste_san = self.make_btn(self.san_ctrl_frame, "📋 Paste & Sanitize", self.paste_and_sanitize, kind="success", padx=16, pady=5)
        btn_paste_san.pack(side=tk.RIGHT, padx=(6, 0))

        # Dynamic Container for Editor Cards
        self.san_box_container = tk.Frame(parent)
        self.san_box_container.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # --- Input Card ---
        self.san_in_card = tk.Frame(self.san_box_container, padx=1, pady=1)
        self.registered_cards.append(self.san_in_card)

        # Card Header
        in_header = tk.Frame(self.san_in_card, padx=12, pady=7)
        in_header.pack(fill=tk.X)
        self.registered_card_headers.append(in_header)

        lbl_title_in = tk.Label(in_header, text="INPUT PAYLOAD", font=("Segoe UI", 9, "bold"))
        lbl_title_in.pack(side=tk.LEFT)
        self.san_in_counter = tk.Label(in_header, text="0 chars | 0 lines", font=("Consolas", 8))
        self.san_in_counter.pack(side=tk.LEFT, padx=(10, 0))

        btn_clr = self.make_btn(in_header, "✕ Clear", self.clear_sanitize, kind="secondary", padx=8, pady=2, font=("Segoe UI", 8, "bold"))
        btn_clr.pack(side=tk.RIGHT)
        btn_open = self.make_btn(in_header, "📂 Open File...", self.open_file_to_sanitize, kind="secondary", padx=8, pady=2, font=("Segoe UI", 8, "bold"))
        btn_open.pack(side=tk.RIGHT, padx=(0, 4))

        # Card Body
        in_body = tk.Frame(self.san_in_card)
        in_body.pack(fill=tk.BOTH, expand=True)

        self.san_input = tk.Text(
            in_body,
            wrap=tk.WORD,
            undo=True,
            font=("Consolas", 10),
            padx=10,
            pady=8,
            bd=0,
            highlightthickness=1
        )
        self.san_in_gutter = LineNumberGutter(in_body, self.san_input, font=("Consolas", 10), theme=self.theme)
        self.gutters.append(self.san_in_gutter)

        in_scroll = ttk.Scrollbar(in_body, orient=tk.VERTICAL, command=lambda *a: (self.san_input.yview(*a), self.san_in_gutter.redraw()))

        def _on_san_in_scroll(*args):
            in_scroll.set(*args)
            self.san_in_gutter.redraw()

        self.san_input.configure(yscrollcommand=_on_san_in_scroll)
        self.san_in_gutter.pack(side=tk.LEFT, fill=tk.Y)
        self.san_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        in_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.san_input.bind("<KeyRelease>", lambda e: (self._update_text_counter(self.san_input, self.san_in_counter), self.san_in_gutter.redraw()))
        self.san_input.bind("<Configure>", lambda e: self.san_in_gutter.redraw())
        self.san_input.bind("<Control-Return>", lambda e: (self.sanitize_action(), "break"))
        self._bind_quick_mask_menu(self.san_input, mode="sanitize")

        # --- Output Card ---
        self.san_out_card = tk.Frame(self.san_box_container, padx=1, pady=1)
        self.registered_cards.append(self.san_out_card)

        out_header = tk.Frame(self.san_out_card, padx=12, pady=7)
        out_header.pack(fill=tk.X)
        self.registered_card_headers.append(out_header)

        lbl_title_out = tk.Label(out_header, text="SANITIZED OUTPUT", font=("Segoe UI", 9, "bold"))
        lbl_title_out.pack(side=tk.LEFT)
        self.san_out_badge = tk.Label(out_header, text="AI-Safe", font=("Segoe UI", 8, "bold"), padx=6, pady=1)
        self.san_out_badge.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_san_leak_warn = tk.Button(
            out_header,
            text="",
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.show_leak_details_dialog
        )

        btn_copy = self.make_btn(out_header, "📋 Copy Output", self.copy_sanitized, kind="primary", padx=12, pady=2, font=("Segoe UI", 8, "bold"))
        btn_copy.pack(side=tk.RIGHT, padx=(4, 0))
        btn_save_file = self.make_btn(out_header, "💾 Save File...", self.save_sanitized_to_file, kind="secondary", padx=10, pady=2, font=("Segoe UI", 8, "bold"))
        btn_save_file.pack(side=tk.RIGHT)

        out_body = tk.Frame(self.san_out_card)
        out_body.pack(fill=tk.BOTH, expand=True)

        self.san_output = tk.Text(
            out_body,
            wrap=tk.WORD,
            font=("Consolas", 10),
            padx=10,
            pady=8,
            bd=0,
            highlightthickness=1
        )
        self.san_out_gutter = LineNumberGutter(out_body, self.san_output, font=("Consolas", 10), theme=self.theme)
        self.gutters.append(self.san_out_gutter)

        out_scroll = ttk.Scrollbar(out_body, orient=tk.VERTICAL, command=lambda *a: (self.san_output.yview(*a), self.san_out_gutter.redraw()))

        def _on_san_out_scroll(*args):
            out_scroll.set(*args)
            self.san_out_gutter.redraw()

        self.san_output.configure(yscrollcommand=_on_san_out_scroll)
        self.san_out_gutter.pack(side=tk.LEFT, fill=tk.Y)
        self.san_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.san_output.bind("<KeyRelease>", lambda e: self.san_out_gutter.redraw())
        self.san_output.bind("<Configure>", lambda e: self.san_out_gutter.redraw())
        self._bind_quick_mask_menu(self.san_output, mode="sanitize")

        # Breakdown summary container
        self.san_breakdown_frame = tk.Frame(parent, pady=2)
        self.san_breakdown_frame.pack(fill=tk.X, pady=(2, 4))

        self._render_sanitize_layout()

    def _update_text_counter(self, text_widget: tk.Text, label_widget: tk.Label):
        content = text_widget.get("1.0", tk.END).strip("\r\n")
        chars = len(content)
        lines = len(content.splitlines()) if content else 0
        label_widget.config(text=f"{chars} chars | {lines} lines")

    def toggle_sanitize_layout(self):
        self.san_layout_mode = "split" if self.san_layout_mode == "stacked" else "stacked"
        self.btn_san_layout.config(text="⬒ Stacked View" if self.san_layout_mode == "split" else "◫ Side-by-Side View")
        self._render_sanitize_layout()

    def _render_sanitize_layout(self):
        self.san_in_card.pack_forget()
        self.san_out_card.pack_forget()

        if self.san_layout_mode == "stacked":
            self.san_in_card.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
            self.san_out_card.pack(fill=tk.BOTH, expand=True)
        else:
            self.san_in_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
            self.san_out_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if hasattr(self, "san_in_gutter"):
            self.san_in_gutter.redraw()
            self.san_out_gutter.redraw()

    def paste_and_sanitize(self):
        text = Clipboard.get()
        if not text:
            self.set_status("Clipboard is empty.")
            return
        self.san_input.delete("1.0", tk.END)
        self.san_input.insert(tk.END, text)
        self._update_text_counter(self.san_input, self.san_in_counter)
        self.san_in_gutter.redraw()
        self.sanitize_action()

    def sanitize_action(self):
        raw_text = self.san_input.get("1.0", tk.END)
        if not raw_text.strip():
            self.san_output.delete("1.0", tk.END)
            self._render_breakdown_badges(self.san_breakdown_frame, {})
            self.btn_san_leak_warn.pack_forget()
            self.san_out_badge.config(text="AI-Safe", bg="#064e3b" if self.current_theme == "dark" else "#dcfce7", fg="#a7f3d0" if self.current_theme == "dark" else "#166534")
            self.set_status("Input is empty.")
            return

        self.set_status("⏳ Sanitizing payload in background thread...")

        ci = self.san_case_insensitive.get()
        wb = self.san_word_boundaries.get()
        ea = self.san_encoding_aware.get()

        def _worker():
            sanitized, count, spans, breakdown = self.engine.sanitize(
                raw_text,
                case_insensitive=ci,
                word_boundaries=wb,
                encoding_aware=ea
            )
            leaks = self.engine.detect_potential_leaks(sanitized, self.engine.rules)
            partial_leaks = self.engine.detect_partial_secret_leaks(sanitized, self.engine.rules)
            preflights = self.engine.check_preflight_collisions(raw_text)

            self.async_queue.put(("sanitize", sanitized, count, spans, breakdown, leaks, partial_leaks, preflights))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_sanitize_complete(self, sanitized, count, spans, breakdown, leaks, partial_leaks, preflights):
        self.san_spans = spans
        self.last_leaks = leaks
        self.last_partial_leaks = partial_leaks

        self.san_output.delete("1.0", tk.END)
        self.san_output.insert(tk.END, sanitized)
        self.san_out_gutter.redraw()

        theme = THEMES[self.current_theme]
        self.san_output.tag_config("replaced", background=theme["tag_replaced_bg"], foreground=theme["tag_replaced_fg"])
        self.san_output.tag_config("leak", background=theme["tag_leak_bg"], foreground=theme["tag_leak_fg"])
        self.san_output.tag_config("partial_leak", background=theme["tag_partial_leak_bg"], foreground=theme["tag_partial_leak_fg"])

        for start, end, orig, repl, _, _ in spans:
            s_pos = f"1.0 + {start} chars"
            e_pos = f"1.0 + {end} chars"
            self.san_output.tag_add("replaced", s_pos, e_pos)

        # 1. Generic leaks scan (JWT, AWS keys, etc.)
        if leaks:
            for leak in leaks:
                s_pos = f"1.0 + {leak['start']} chars"
                e_pos = f"1.0 + {leak['end']} chars"
                self.san_output.tag_add("leak", s_pos, e_pos)

        # 2. Feature 2C: Partial-Secret Leaks scan
        if partial_leaks:
            for pl in partial_leaks:
                pos = "1.0"
                while True:
                    found = self.san_output.search(pl["matched_text"], pos, tk.END)
                    if not found:
                        break
                    end_found = f"{found} + {len(pl['matched_text'])} chars"
                    self.san_output.tag_add("partial_leak", found, end_found)
                    pos = end_found

        # Update warning banner & AI-Safe badge
        if preflights:
            pref_names = ", ".join(repr(p) for p, _ in preflights[:3])
            self.set_status(f"⚠️ Pre-flight notice: Raw input already contained placeholder(s): {pref_names}! Watch for unsanitize collision.")

        total_leaks = len(partial_leaks) + len(leaks)
        if total_leaks > 0:
            # Hide the static badge and show only the single interactive warning button
            self.san_out_badge.pack_forget()

            if partial_leaks and not leaks:
                warn_text = f"⚠️ {len(partial_leaks)} Partial Leak(s) Detected - Click to View"
                warn_bg = "#7c2d12"
                warn_fg = "#ffedd5"
                warn_hover = "#9a3412"
            else:
                warn_text = f"⚠️ {total_leaks} Potential Leak(s) Detected - Click to View"
                warn_bg = "#7f1d1d"
                warn_fg = "#fee2e2"
                warn_hover = "#991b1b"

            self.btn_san_leak_warn.config(
                text=warn_text,
                bg=warn_bg,
                fg=warn_fg,
                activebackground=warn_hover
            )
            self.btn_san_leak_warn.pack(side=tk.LEFT, padx=(8, 0))
            self.set_status(f"⚠️ Sanitized {count} field(s). Warning: {total_leaks} potential unmasked secret(s) detected in output!")
        else:
            self.btn_san_leak_warn.pack_forget()
            self.san_out_badge.config(
                text="AI-Safe",
                bg="#064e3b" if self.current_theme == "dark" else "#dcfce7",
                fg="#a7f3d0" if self.current_theme == "dark" else "#166534"
            )
            self.san_out_badge.pack(side=tk.LEFT, padx=(8, 0))
            self.set_status(f"✨ Sanitized {count} field(s) successfully. Output verified safe.")

        self._render_breakdown_badges(self.san_breakdown_frame, breakdown, target_text_widget=self.san_output, spans=spans)

    def scan_leaks_action(self):
        text = self.san_output.get("1.0", tk.END).strip()
        if not text:
            text = self.san_input.get("1.0", tk.END).strip()
        if not text:
            self.set_status("Nothing to scan.")
            return

        leaks = self.engine.detect_potential_leaks(text, self.engine.rules)
        partial_leaks = self.engine.detect_partial_secret_leaks(text, self.engine.rules)
        self.last_leaks = leaks
        self.last_partial_leaks = partial_leaks

        if not leaks and not partial_leaks:
            messagebox.showinfo("Leak Scanner", "No unmasked tokens (JWT, AWS keys, passwords) or partial secret leaks detected!")
            self.set_status("Scanner: Clean. No unmasked secrets detected.")
        else:
            self.show_leak_details_dialog()

    def copy_sanitized(self):
        text = self.san_output.get("1.0", tk.END).strip("\r\n")
        if not text:
            self.set_status("Output is empty; nothing copied.")
            return
        Clipboard.set(text)
        self.set_status("📋 Copied sanitized output to clipboard! Ready to paste into AI chat.")

    def clear_sanitize(self):
        self.san_input.delete("1.0", tk.END)
        self.san_output.delete("1.0", tk.END)
        self._update_text_counter(self.san_input, self.san_in_counter)
        self.san_in_gutter.redraw()
        self.san_out_gutter.redraw()
        self._render_breakdown_badges(self.san_breakdown_frame, {})
        self.btn_san_leak_warn.pack_forget()
        self.san_out_badge.config(text="AI-Safe", bg="#064e3b" if self.current_theme == "dark" else "#dcfce7", fg="#a7f3d0" if self.current_theme == "dark" else "#166534")
        self.san_out_badge.pack(side=tk.LEFT, padx=(8, 0))
        self.set_status("Ready")

    def open_file_to_sanitize(self):
        file_path = filedialog.askopenfilename(
            title="Open File to Sanitize",
            filetypes=[
                ("Supported Files", "*.log;*.txt;*.sql;*.json;*.env;*.csv;*.xml;*.yml;*.yaml"),
                ("Log Files", "*.log"),
                ("Text Files", "*.txt"),
                ("SQL Files", "*.sql"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.san_input.delete("1.0", tk.END)
                self.san_input.insert(tk.END, content)
                self._update_text_counter(self.san_input, self.san_in_counter)
                self.san_in_gutter.redraw()
                self.set_status(f"Loaded {os.path.basename(file_path)} ({len(content)} chars). Starting sanitization...")
                self.sanitize_action()
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to read file:\n{e}")

    def save_sanitized_to_file(self):
        content = self.san_output.get("1.0", tk.END).strip("\r\n")
        if not content:
            messagebox.showinfo("Save File", "Output is empty; nothing to save.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Sanitized Output File",
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Log File", "*.log"), ("All Files", "*.*")]
        )
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.set_status(f"💾 Saved sanitized file to {os.path.basename(save_path)} successfully.")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def open_presets_dialog(self):
        raw_text = self.san_input.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showinfo("Auto-Mask Presets", "Please enter or paste your payload into the Input box first.")
            return

        AutoMaskPresetsDialog(self.root, self.engine, raw_text, self._on_presets_applied, theme_name=self.current_theme)

    def _on_presets_applied(self, count: int):
        self.refresh_rules_table()
        self.sanitize_action()
        self.set_status(f"✨ Auto-Mask Applied: Generated and saved {count} new preset rule(s)!")

    def open_sanitize_diff(self):
        orig = self.san_input.get("1.0", tk.END).strip("\r\n")
        trans = self.san_output.get("1.0", tk.END).strip("\r\n")
        if not orig:
            messagebox.showinfo("Visual Diff", "Input payload is empty. Nothing to diff.")
            return
        if not trans:
            self.sanitize_action()
            trans = self.san_output.get("1.0", tk.END).strip("\r\n")

        VisualDiffDialog(
            parent=self.root,
            original_text=orig,
            transformed_text=trans,
            title="Visual Diff — Sanitized Payload Comparison",
            mode="sanitize",
            theme_name=self.current_theme,
            spans=self.san_spans
        )

    def open_unsanitize_diff(self):
        orig = self.unsan_input.get("1.0", tk.END).strip("\r\n")
        trans = self.unsan_output.get("1.0", tk.END).strip("\r\n")
        if not orig:
            messagebox.showinfo("Visual Diff", "Input commands are empty. Nothing to diff.")
            return
        if not trans:
            self.unsanitize_action()
            trans = self.unsan_output.get("1.0", tk.END).strip("\r\n")

        VisualDiffDialog(
            parent=self.root,
            original_text=orig,
            transformed_text=trans,
            title="Visual Diff — Unsanitized Real Payload Comparison",
            mode="unsanitize",
            theme_name=self.current_theme,
            spans=self.unsan_spans
        )

    def show_leak_details_dialog(self):
        partial_leaks = getattr(self, "last_partial_leaks", [])
        leaks = getattr(self, "last_leaks", [])
        if not partial_leaks and not leaks:
            messagebox.showinfo("Security Scanner", "No partial secret leaks or potential token exposures detected.")
            return

        LeakDetailsDialog(
            parent=self.root,
            partial_leaks=partial_leaks,
            generic_leaks=leaks,
            on_quick_mask_fix=self._on_leak_quick_mask,
            theme_name=self.current_theme
        )

    def _on_leak_quick_mask(self, secret_token: str, mode: str = "synthetic"):
        if mode == "synthetic":
            cat = "token"
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", secret_token):
                cat = "ip"
            elif "@" in secret_token and "." in secret_token:
                cat = "email"
            elif re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", secret_token):
                cat = "uuid"
            suggested = self.engine.generate_synthetic_value(secret_token, cat)
        else:
            clean = re.sub(r"[^A-Za-z0-9_]+", "_", secret_token.strip()).upper()[:16]
            suggested = f"<{clean or 'SECRET'}>"

        self.engine.add_rule(secret_token, suggested)
        self.engine.save_config()
        self.refresh_rules_table()
        self.sanitize_action()
        self.set_status(f"Quick fixed leak: Added rule '{secret_token[:24]}...' ➔ '{suggested}' and re-sanitized.")

    # =========================================================================
    # TAB 2: UNSANITIZE WORKSPACE
    # =========================================================================
    def _build_unsanitize_tab(self):
        parent = self.page_unsanitize

        self.unsan_ctrl_frame = tk.Frame(parent, pady=4)
        self.unsan_ctrl_frame.pack(fill=tk.X, pady=(0, 6))

        chk_wb = ttk.Checkbutton(self.unsan_ctrl_frame, text="Word boundaries (\\b)", variable=self.unsan_word_boundaries)
        chk_wb.pack(side=tk.LEFT, padx=(0, 10))

        chk_case = ttk.Checkbutton(self.unsan_ctrl_frame, text="Case-insensitive", variable=self.unsan_case_insensitive)
        chk_case.pack(side=tk.LEFT, padx=(0, 10))

        chk_enc = ttk.Checkbutton(self.unsan_ctrl_frame, text="Encoding-aware (%20, \\\\)", variable=self.unsan_encoding_aware)
        chk_enc.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_unsan_layout = self.make_btn(self.unsan_ctrl_frame, "⬒ Stacked View", self.toggle_unsanitize_layout, kind="secondary", padx=10, pady=4)
        self.btn_unsan_layout.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_unsan_diff = self.make_btn(self.unsan_ctrl_frame, "🔍 Visual Diff", self.open_unsanitize_diff, kind="secondary", padx=10, pady=4)
        self.btn_unsan_diff.pack(side=tk.LEFT)

        # Right Action Buttons: Paste & Unsanitize and Restore True Data
        btn_unsan_main = self.make_btn(self.unsan_ctrl_frame, "⚡ Restore True Data (Ctrl+Enter)", self.unsanitize_action, kind="primary", padx=16, pady=5)
        btn_unsan_main.pack(side=tk.RIGHT, padx=(4, 0))

        btn_paste_unsan = self.make_btn(self.unsan_ctrl_frame, "📋 Paste & Unsanitize", self.paste_and_unsanitize, kind="success", padx=16, pady=5)
        btn_paste_unsan.pack(side=tk.RIGHT, padx=(6, 0))

        self.unsan_box_container = tk.Frame(parent)
        self.unsan_box_container.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Input Card
        self.unsan_in_card = tk.Frame(self.unsan_box_container, padx=1, pady=1)
        self.registered_cards.append(self.unsan_in_card)

        in_header = tk.Frame(self.unsan_in_card, padx=12, pady=7)
        in_header.pack(fill=tk.X)
        self.registered_card_headers.append(in_header)

        lbl_title_in = tk.Label(in_header, text="INPUT AI RESPONSE / COMMANDS", font=("Segoe UI", 9, "bold"))
        lbl_title_in.pack(side=tk.LEFT)
        self.unsan_in_counter = tk.Label(in_header, text="0 chars | 0 lines", font=("Consolas", 8))
        self.unsan_in_counter.pack(side=tk.LEFT, padx=(10, 0))

        btn_clr = self.make_btn(in_header, "✕ Clear", self.clear_unsanitize, kind="secondary", padx=8, pady=2, font=("Segoe UI", 8, "bold"))
        btn_clr.pack(side=tk.RIGHT)
        btn_open = self.make_btn(in_header, "📂 Open File...", self.open_file_to_unsanitize, kind="secondary", padx=8, pady=2, font=("Segoe UI", 8, "bold"))
        btn_open.pack(side=tk.RIGHT, padx=(0, 4))

        in_body = tk.Frame(self.unsan_in_card)
        in_body.pack(fill=tk.BOTH, expand=True)

        self.unsan_input = tk.Text(
            in_body,
            wrap=tk.WORD,
            undo=True,
            font=("Consolas", 10),
            padx=10,
            pady=8,
            bd=0,
            highlightthickness=1
        )
        self.unsan_in_gutter = LineNumberGutter(in_body, self.unsan_input, font=("Consolas", 10), theme=self.theme)
        self.gutters.append(self.unsan_in_gutter)

        in_scroll = ttk.Scrollbar(in_body, orient=tk.VERTICAL, command=lambda *a: (self.unsan_input.yview(*a), self.unsan_in_gutter.redraw()))

        def _on_unsan_in_scroll(*args):
            in_scroll.set(*args)
            self.unsan_in_gutter.redraw()

        self.unsan_input.configure(yscrollcommand=_on_unsan_in_scroll)
        self.unsan_in_gutter.pack(side=tk.LEFT, fill=tk.Y)
        self.unsan_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        in_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.unsan_input.bind("<KeyRelease>", lambda e: (self._update_text_counter(self.unsan_input, self.unsan_in_counter), self.unsan_in_gutter.redraw()))
        self.unsan_input.bind("<Configure>", lambda e: self.unsan_in_gutter.redraw())
        self.unsan_input.bind("<Control-Return>", lambda e: (self.unsanitize_action(), "break"))

        # Output Card
        self.unsan_out_card = tk.Frame(self.unsan_box_container, padx=1, pady=1)
        self.registered_cards.append(self.unsan_out_card)

        out_header = tk.Frame(self.unsan_out_card, padx=12, pady=7)
        out_header.pack(fill=tk.X)
        self.registered_card_headers.append(out_header)

        lbl_title_out = tk.Label(out_header, text="RESTORED TERMINAL COMMANDS", font=("Segoe UI", 9, "bold"))
        lbl_title_out.pack(side=tk.LEFT)
        self.unsan_out_badge = tk.Label(out_header, text="Ready to Execute", font=("Segoe UI", 8, "bold"), padx=6, pady=1)
        self.unsan_out_badge.pack(side=tk.LEFT, padx=(8, 0))

        btn_copy = self.make_btn(out_header, "📋 Copy Restored", self.copy_unsanitized, kind="success", padx=12, pady=2, font=("Segoe UI", 8, "bold"))
        btn_copy.pack(side=tk.RIGHT, padx=(4, 0))
        btn_save_file = self.make_btn(out_header, "💾 Save File...", self.save_unsanitized_to_file, kind="secondary", padx=10, pady=2, font=("Segoe UI", 8, "bold"))
        btn_save_file.pack(side=tk.RIGHT)

        out_body = tk.Frame(self.unsan_out_card)
        out_body.pack(fill=tk.BOTH, expand=True)

        self.unsan_output = tk.Text(
            out_body,
            wrap=tk.WORD,
            font=("Consolas", 10),
            padx=10,
            pady=8,
            bd=0,
            highlightthickness=1
        )
        self.unsan_out_gutter = LineNumberGutter(out_body, self.unsan_output, font=("Consolas", 10), theme=self.theme)
        self.gutters.append(self.unsan_out_gutter)

        out_scroll = ttk.Scrollbar(out_body, orient=tk.VERTICAL, command=lambda *a: (self.unsan_output.yview(*a), self.unsan_out_gutter.redraw()))

        def _on_unsan_out_scroll(*args):
            out_scroll.set(*args)
            self.unsan_out_gutter.redraw()

        self.unsan_output.configure(yscrollcommand=_on_unsan_out_scroll)
        self.unsan_out_gutter.pack(side=tk.LEFT, fill=tk.Y)
        self.unsan_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.unsan_output.bind("<KeyRelease>", lambda e: self.unsan_out_gutter.redraw())
        self.unsan_output.bind("<Configure>", lambda e: self.unsan_out_gutter.redraw())

        self.unsan_breakdown_frame = tk.Frame(parent, pady=2)
        self.unsan_breakdown_frame.pack(fill=tk.X, pady=(2, 4))

        self._render_unsanitize_layout()

    def toggle_unsanitize_layout(self):
        self.unsan_layout_mode = "split" if self.unsan_layout_mode == "stacked" else "stacked"
        self.btn_unsan_layout.config(text="⬒ Stacked View" if self.unsan_layout_mode == "split" else "◫ Side-by-Side View")
        self._render_unsanitize_layout()

    def _render_unsanitize_layout(self):
        self.unsan_in_card.pack_forget()
        self.unsan_out_card.pack_forget()

        if self.unsan_layout_mode == "stacked":
            self.unsan_in_card.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
            self.unsan_out_card.pack(fill=tk.BOTH, expand=True)
        else:
            self.unsan_in_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
            self.unsan_out_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if hasattr(self, "unsan_in_gutter"):
            self.unsan_in_gutter.redraw()
            self.unsan_out_gutter.redraw()

    def paste_and_unsanitize(self):
        text = Clipboard.get()
        if not text:
            self.set_status("Clipboard is empty.")
            return
        self.unsan_input.delete("1.0", tk.END)
        self.unsan_input.insert(tk.END, text)
        self._update_text_counter(self.unsan_input, self.unsan_in_counter)
        self.unsan_in_gutter.redraw()
        self.unsanitize_action()

    def unsanitize_action(self):
        raw_text = self.unsan_input.get("1.0", tk.END)
        if not raw_text.strip():
            self.unsan_output.delete("1.0", tk.END)
            self._render_breakdown_badges(self.unsan_breakdown_frame, {})
            self.set_status("Input is empty.")
            return

        self.set_status("⏳ Restoring true data in background thread...")

        ci = self.unsan_case_insensitive.get()
        wb = self.unsan_word_boundaries.get()
        ea = self.unsan_encoding_aware.get()

        def _bg_unsan():
            restored, count, spans, breakdown = self.engine.unsanitize(
                raw_text,
                case_insensitive=ci,
                word_boundaries=wb,
                encoding_aware=ea
            )
            self.async_queue.put(("unsanitize", restored, count, spans, breakdown))

        threading.Thread(target=_bg_unsan, daemon=True).start()

    def _on_unsanitize_complete(self, restored, count, spans, breakdown):
        self.unsan_spans = spans
        self.unsan_output.delete("1.0", tk.END)
        self.unsan_output.insert(tk.END, restored)
        self.unsan_out_gutter.redraw()

        theme = THEMES[self.current_theme]
        self.unsan_output.tag_config("restored", background=theme["tag_restored_bg"], foreground=theme["tag_restored_fg"])

        for start, end, orig, repl, _, _ in spans:
            s_pos = f"1.0 + {start} chars"
            e_pos = f"1.0 + {end} chars"
            self.unsan_output.tag_add("restored", s_pos, e_pos)

        self.set_status(f"✨ Restored {count} field(s) back to original values.")
        self._render_breakdown_badges(self.unsan_breakdown_frame, breakdown, target_text_widget=self.unsan_output, spans=spans)

    def copy_unsanitized(self):
        text = self.unsan_output.get("1.0", tk.END).strip("\r\n")
        if not text:
            self.set_status("Output is empty; nothing copied.")
            return
        Clipboard.set(text)
        self.set_status("📋 Copied restored data to clipboard! Auto-wipe timer started (60s).")
        self.start_clipboard_autowipe(seconds=60, expected_text=text)

    def open_file_to_unsanitize(self):
        file_path = filedialog.askopenfilename(
            title="Open Sanitized File to Restore",
            filetypes=[("All Supported Files", "*.*"), ("Text Files", "*.txt"), ("Log Files", "*.log")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.unsan_input.delete("1.0", tk.END)
                self.unsan_input.insert(tk.END, content)
                self._update_text_counter(self.unsan_input, self.unsan_in_counter)
                self.unsan_in_gutter.redraw()
                self.set_status(f"Loaded {os.path.basename(file_path)}. Restoring...")
                self.unsanitize_action()
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to read file:\n{e}")

    def save_unsanitized_to_file(self):
        content = self.unsan_output.get("1.0", tk.END).strip("\r\n")
        if not content:
            messagebox.showinfo("Save File", "Output is empty; nothing to save.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Restored Output File",
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Log File", "*.log"), ("All Files", "*.*")]
        )
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.set_status(f"💾 Saved restored file to {os.path.basename(save_path)}.")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def start_clipboard_autowipe(self, seconds: int = 60, expected_text: str = ""):
        self.clip_wipe_remaining = seconds
        self.clip_wipe_expected = expected_text

        if hasattr(self, "_clip_wipe_job") and self._clip_wipe_job:
            try:
                self.root.after_cancel(self._clip_wipe_job)
            except Exception:
                pass
            self._clip_wipe_job = None

        self.clip_wipe_frame.pack(side=tk.RIGHT, padx=(0, 14))
        self._tick_clipboard_autowipe()

    def _tick_clipboard_autowipe(self):
        if self.clip_wipe_remaining <= 0:
            curr = Clipboard.get().strip("\r\n")
            if curr == self.clip_wipe_expected.strip("\r\n"):
                Clipboard.set("")
                self.set_status("🛡️ Security auto-wipe: Restored credentials cleared from Windows clipboard.")
            self.cancel_clipboard_wipe(hide_only=True)
            return

        self.lbl_clip_countdown.config(text=f"⏱️ Sensitive Clipboard Auto-Clears: {self.clip_wipe_remaining}s")
        self.clip_wipe_remaining -= 1
        self._clip_wipe_job = self.root.after(1000, self._tick_clipboard_autowipe)

    def cancel_clipboard_wipe(self, hide_only: bool = False):
        if hasattr(self, "_clip_wipe_job") and self._clip_wipe_job:
            try:
                self.root.after_cancel(self._clip_wipe_job)
            except Exception:
                pass
            self._clip_wipe_job = None
        self.clip_wipe_frame.pack_forget()
        if not hide_only:
            self.set_status("Clipboard auto-wipe canceled. Data retained in clipboard.")

    def wipe_clipboard_now(self):
        Clipboard.set("")
        self.cancel_clipboard_wipe(hide_only=True)
        self.set_status("🛡️ Clipboard cleared immediately.")

    def clear_unsanitize(self):
        self.unsan_input.delete("1.0", tk.END)
        self.unsan_output.delete("1.0", tk.END)
        self._update_text_counter(self.unsan_input, self.unsan_in_counter)
        self.unsan_in_gutter.redraw()
        self.unsan_out_gutter.redraw()
        self._render_breakdown_badges(self.unsan_breakdown_frame, {})
        self.set_status("Ready")

    # =========================================================================
    # TAB 3: MANAGE RULES WORKSPACE
    # =========================================================================
    def _build_rules_tab(self):
        parent = self.page_rules

        # Filter bar
        filter_bar = tk.Frame(parent, pady=4)
        filter_bar.pack(fill=tk.X, pady=(0, 6))

        lbl_s = tk.Label(filter_bar, text="🔍", font=("Segoe UI", 11), bg=filter_bar.cget("bg"))
        lbl_s.pack(side=tk.LEFT, padx=(0, 4))

        self.ent_filter = ttk.Entry(filter_bar, textvariable=self.rules_search_var, width=32)
        self.ent_filter.pack(side=tk.LEFT)
        self.rules_search_var.trace_add("write", lambda *args: self.refresh_rules_table())

        btn_clr_filter = self.make_btn(filter_bar, "Clear", lambda: self.rules_search_var.set(""), kind="secondary", padx=8, pady=3)
        btn_clr_filter.pack(side=tk.LEFT, padx=(6, 16))

        self.chk_collisions_only = ttk.Checkbutton(
            filter_bar,
            text="⚠️ Show collisions only (0)",
            variable=self.show_collisions_only_var,
            command=self.refresh_rules_table
        )
        self.chk_collisions_only.pack(side=tk.LEFT)

        # Rules Table Card
        self.tbl_card = tk.Frame(parent, padx=1, pady=1)
        self.tbl_card.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        self.registered_cards.append(self.tbl_card)

        columns = ("secret", "placeholder", "status")
        self.rules_tree = ttk.Treeview(self.tbl_card, columns=columns, show="headings", selectmode="browse")
        self.rules_tree.heading("secret", text="Original Sensitive Value (Secret)")
        self.rules_tree.heading("placeholder", text="Anonymized Placeholder Alias")
        self.rules_tree.heading("status", text="Reverse Mapping Status")
        self.rules_tree.column("secret", width=300, anchor="w")
        self.rules_tree.column("placeholder", width=300, anchor="w")
        self.rules_tree.column("status", width=380, anchor="w")

        tbl_scroll = ttk.Scrollbar(self.tbl_card, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=tbl_scroll.set)
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tbl_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.rules_tree.bind("<<TreeviewSelect>>", self._on_rule_selected)

        # Form Card
        self.form_card = tk.Frame(parent, padx=1, pady=1)
        self.form_card.pack(fill=tk.X, pady=(0, 6))
        self.registered_cards.append(self.form_card)

        self.form_inner = tk.Frame(self.form_card, padx=14, pady=12)
        self.form_inner.pack(fill=tk.X)
        self.registered_card_headers.append(self.form_inner)

        lbl_s_title = tk.Label(self.form_inner, text="Secret Value:", font=("Segoe UI", 9, "bold"))
        lbl_s_title.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.ent_secret = ttk.Entry(self.form_inner, width=32, font=("Consolas", 10))
        self.ent_secret.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=2)

        lbl_p_title = tk.Label(self.form_inner, text="Placeholder Alias:", font=("Segoe UI", 9, "bold"))
        lbl_p_title.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)
        self.ent_placeholder = ttk.Entry(self.form_inner, width=32, font=("Consolas", 10))
        self.ent_placeholder.grid(row=0, column=3, sticky="ew", padx=(0, 14), pady=2)

        self.form_inner.columnconfigure(1, weight=1)
        self.form_inner.columnconfigure(3, weight=1)

        btn_save_rule = self.make_btn(self.form_inner, "Save Rule", self.save_rule_entry, kind="primary", padx=14, pady=4)
        btn_save_rule.grid(row=0, column=4, padx=(0, 4), pady=2)

        btn_clear_form = self.make_btn(self.form_inner, "Reset", self._reset_rule_form, kind="secondary", padx=10, pady=4)
        btn_clear_form.grid(row=0, column=5, padx=(0, 4), pady=2)

        self.lbl_form_collision_note = tk.Label(self.form_inner, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_form_collision_note.grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))

        # Bottom Actions
        act_bar = tk.Frame(parent, pady=2)
        act_bar.pack(fill=tk.X, pady=(2, 4))

        btn_del = self.make_btn(act_bar, "🗑️ Delete Selected Rule", self.delete_selected_rule, kind="danger", padx=12, pady=5)
        btn_del.pack(side=tk.LEFT, padx=(0, 6))

        btn_export = self.make_btn(act_bar, "Export As...", self.export_rules_as, kind="secondary", padx=10, pady=5)
        btn_export.pack(side=tk.LEFT, padx=6)

    def refresh_rules_table(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        filter_text = self.rules_search_var.get().strip().lower()
        collisions_only = self.show_collisions_only_var.get()

        for secret, placeholder in self.engine.rules.items():
            is_collision = placeholder in self.engine.collisions

            if collisions_only and not is_collision:
                continue

            if filter_text:
                if filter_text not in secret.lower() and filter_text not in placeholder.lower():
                    continue

            if is_collision:
                other_secrets = [s for s in self.engine.collisions[placeholder] if s != secret]
                status_text = f"⚠️ Collision with: {', '.join(repr(s) for s in other_secrets)}"
                tag = ("collision",)
            else:
                status_text = "✓ Unique (1:1 Safe)"
                tag = ()

            self.rules_tree.insert("", tk.END, values=(secret, placeholder, status_text), tags=tag)

        collision_count = len(self.engine.collisions)
        self.chk_collisions_only.config(text=f"⚠️ Show collisions only ({collision_count})")
        self._update_status_bar()

    def _on_rule_selected(self, event):
        selected = self.rules_tree.selection()
        if not selected:
            return
        item = self.rules_tree.item(selected[0])
        secret, placeholder = item["values"][0], item["values"][1]
        self.ent_secret.delete(0, tk.END)
        self.ent_secret.insert(0, str(secret))
        self.ent_placeholder.delete(0, tk.END)
        self.ent_placeholder.insert(0, str(placeholder))

        if placeholder in self.engine.collisions:
            other_secrets = [s for s in self.engine.collisions[placeholder] if s != str(secret)]
            self.lbl_form_collision_note.config(
                text=f"⚠️ Collision Detected! Placeholder '{placeholder}' is also assigned to {', '.join(repr(s) for s in other_secrets)}.\n"
                     f"   To fix: Change the placeholder to a unique alias (e.g. '{placeholder}_1')."
            )
        else:
            self.lbl_form_collision_note.config(text="")

    def _reset_rule_form(self):
        self.ent_secret.delete(0, tk.END)
        self.ent_placeholder.delete(0, tk.END)
        self.lbl_form_collision_note.config(text="")

    def save_rule_entry(self):
        secret = self.ent_secret.get().strip()
        placeholder = self.ent_placeholder.get().strip()
        if not secret or not placeholder:
            messagebox.showwarning("Incomplete Rule", "Both secret value and placeholder are required.")
            return

        self.engine.add_rule(secret, placeholder)
        self.engine.save_config()
        self.refresh_rules_table()
        self._reset_rule_form()
        self.set_status(f"Rule for '{secret}' saved and written to disk.")

    def delete_selected_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Select Rule", "Please select a rule from the table to delete.")
            return

        item = self.rules_tree.item(selected[0])
        secret, placeholder = item["values"][0], item["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete rule for '{secret}' -> '{placeholder}'?"):
            self.engine.remove_rule(str(secret))
            self.engine.save_config()
            self.refresh_rules_table()
            self._reset_rule_form()
            self.set_status(f"Rule for '{secret}' deleted.")

    def save_rules_to_disk(self):
        if self.engine.save_config():
            messagebox.showinfo("Saved", f"All {len(self.engine.rules)} rules successfully saved to:\n{self.engine.config_path}")
            self.set_status(f"Saved {len(self.engine.rules)} rules to {os.path.basename(self.engine.config_path)}.")
        else:
            messagebox.showerror("Save Error", "Could not write rules to file.")

    def export_rules_as(self):
        save_path = filedialog.asksaveasfilename(
            title="Export Rules As JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if save_path:
            if self.engine.save_config(save_path):
                self.lbl_config.config(text=f"📄 {os.path.basename(self.engine.config_path)}")
                messagebox.showinfo("Exported", f"Rules exported successfully to:\n{save_path}")
            else:
                messagebox.showerror("Export Error", "Failed to export rules.")

    # =========================================================================
    # QUICK MASK & BREAKDOWN BADGES
    # =========================================================================
    def _bind_quick_mask_menu(self, text_widget: tk.Text, mode: str = "sanitize"):
        menu = tk.Menu(text_widget, tearoff=0)

        def on_right_click(event):
            try:
                selected_text = ""
                if text_widget.tag_ranges("sel"):
                    selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST).strip()

                menu.delete(0, tk.END)
                if selected_text:
                    menu.add_command(
                        label=f"🛡️ Quick Mask '{selected_text[:20]}...' as Placeholder",
                        command=lambda: self._quick_mask_prompt(selected_text)
                    )
                    menu.add_separator()

                menu.add_command(label="Copy", command=lambda: text_widget.event_generate("<<Copy>>"))
                menu.add_command(label="Cut", command=lambda: text_widget.event_generate("<<Cut>>"))
                menu.add_command(label="Paste", command=lambda: text_widget.event_generate("<<Paste>>"))
                menu.add_separator()
                menu.add_command(label="Select All", command=lambda: text_widget.tag_add("sel", "1.0", "end"))

                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        text_widget.bind("<Button-3>", on_right_click)

    def _quick_mask_prompt(self, secret: str):
        suggested = f"<{secret.upper().replace(' ', '_')[:16]}>"
        placeholder = simpledialog.askstring(
            "Quick Mask Rule",
            f"Enter placeholder alias for:\n'{secret}'",
            initialvalue=suggested,
            parent=self.root
        )
        if placeholder and placeholder.strip():
            self.engine.add_rule(secret, placeholder.strip())
            self.engine.save_config()
            self.refresh_rules_table()
            self.sanitize_action()
            self.set_status(f"Quick Masked: Added '{secret}' ➔ '{placeholder.strip()}' and re-sanitized!")

    def _render_breakdown_badges(
        self,
        container: tk.Frame,
        breakdown: Dict[str, int],
        target_text_widget: Optional[tk.Text] = None,
        spans: Optional[List[Any]] = None
    ):
        for widget in container.winfo_children():
            widget.destroy()

        if not breakdown:
            return

        theme = THEMES[self.current_theme]

        lbl_title = tk.Label(
            container,
            text="Replaced Breakdown (Click badge to jump to matches):",
            font=("Segoe UI", 9, "bold"),
            bg=container.cget("bg"),
            fg=theme["text_muted"]
        )
        lbl_title.pack(side=tk.LEFT, padx=(0, 8))

        for label, count in breakdown.items():
            btn_badge = tk.Button(
                container,
                text=f"{count}x  {label}",
                font=("Consolas", 8, "bold"),
                bg=theme["badge_bg"],
                fg=theme["badge_fg"],
                activebackground=theme["tag_replaced_bg"],
                activeforeground=theme["tag_replaced_fg"],
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda lbl=label: self._jump_to_breakdown_match(lbl, target_text_widget, spans)
            )
            btn_badge.pack(side=tk.LEFT, padx=3)

    def _jump_to_breakdown_match(self, rule_label: str, text_widget: Optional[tk.Text], spans: Optional[List[Any]]):
        if not text_widget or not spans:
            return

        text_widget.tag_remove("sel", "1.0", tk.END)
        first_start = None

        for start, end, orig, repl, orig_k, orig_v in spans:
            if f"{orig_k} ➔ {orig_v}" == rule_label:
                s_pos = f"1.0 + {start} chars"
                e_pos = f"1.0 + {end} chars"
                text_widget.tag_add("sel", s_pos, e_pos)
                if first_start is None:
                    first_start = s_pos

        if first_start:
            text_widget.see(first_start)
            self.set_status(f"Highlighted all occurrences of '{rule_label}' in output.")

    # =========================================================================
    # THEME ENGINE
    # =========================================================================
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme = THEMES[self.current_theme]
        self.btn_theme_toggle.config(text="🌙 Dark Mode" if self.current_theme == "light" else "☀️ Light Mode")
        self.apply_theme_colors()

    def apply_theme_colors(self):
        theme = THEMES[self.current_theme]

        self.root.configure(bg=theme["win_bg"])
        self.header_frame.configure(bg=theme["header_bg"])
        self.lbl_title.configure(bg=theme["header_bg"], fg=theme["text_fg"])
        self.badge_version.configure(bg=theme["card_bg"], fg=theme["text_muted"])
        self.lbl_config.configure(bg=theme["card_bg"], fg=theme["text_muted"])
        self.nav_capsule.configure(bg=theme["nav_bg"])

        self.pages_container.configure(bg=theme["win_bg"])
        self.page_sanitize.configure(bg=theme["win_bg"])
        self.page_unsanitize.configure(bg=theme["win_bg"])
        self.page_rules.configure(bg=theme["win_bg"])

        # Toolbars
        self.san_ctrl_frame.configure(bg=theme["win_bg"])
        self.unsan_ctrl_frame.configure(bg=theme["win_bg"])
        self.san_box_container.configure(bg=theme["win_bg"])
        self.unsan_box_container.configure(bg=theme["win_bg"])

        # Cards and Card Headers
        for card in self.registered_cards:
            card.configure(bg=theme["card_border"])
        for ch in self.registered_card_headers:
            ch.configure(bg=theme["card_header"])

        # Status Bar
        self.status_bar_frame.configure(bg=theme["status_bg"])
        self.status_bar.configure(bg=theme["status_bg"], fg=theme["status_fg"])
        self.status_right.configure(bg=theme["status_bg"], fg=theme["text_muted"])
        self.clip_wipe_frame.configure(bg=theme["status_bg"])

        # Counter and Badges
        self.san_in_counter.configure(bg=theme["card_header"], fg=theme["text_muted"])
        self.san_out_badge.configure(bg=theme["card_bg"], fg="#38bdf8")
        self.unsan_in_counter.configure(bg=theme["card_header"], fg=theme["text_muted"])
        self.unsan_out_badge.configure(bg=theme["card_bg"], fg="#10b981")

        self.form_inner.configure(bg=theme["card_bg"])
        self.lbl_form_collision_note.configure(bg=theme["card_bg"], fg="#ef4444")

        # TTK Elements
        self.style.configure("TCheckbutton", background=theme["win_bg"], foreground=theme["text_fg"], font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", theme["win_bg"])])

        self.style.configure(
            "Treeview",
            background=theme["tree_bg"],
            foreground=theme["tree_fg"],
            fieldbackground=theme["tree_bg"],
            borderwidth=0,
            font=("Consolas", 10),
            rowheight=28
        )
        self.style.configure(
            "Treeview.Heading",
            background=theme["tree_header_bg"],
            foreground=theme["tree_header_fg"],
            borderwidth=0,
            font=("Segoe UI", 9, "bold")
        )
        self.style.map("Treeview.Heading", background=[("active", theme["card_header"])])

        # Text Boxes
        for tw in (self.san_input, self.san_output, self.unsan_input, self.unsan_output):
            tw.configure(
                bg=theme["text_bg"],
                fg=theme["text_fg"],
                insertbackground=theme["text_fg"],
                highlightthickness=1,
                highlightbackground=theme["text_border"],
                highlightcolor=theme["text_focus"]
            )

        for g in getattr(self, "gutters", []):
            g.update_theme(theme)

        self.san_output.tag_config("replaced", background=theme["tag_replaced_bg"], foreground=theme["tag_replaced_fg"])
        self.san_output.tag_config("leak", background=theme["tag_leak_bg"], foreground=theme["tag_leak_fg"])
        self.unsan_output.tag_config("restored", background=theme["tag_restored_bg"], foreground=theme["tag_restored_fg"])
        self.rules_tree.tag_configure("collision", background=theme["tree_collision_bg"], foreground=theme["tree_collision_fg"])

        # Update Navigation Pills
        self.switch_tab(self.active_tab_name)

        # Update Registered Buttons
        for btn, kind in self.registered_buttons:
            bg = theme.get(f"btn_{kind}_bg", theme["btn_secondary_bg"])
            fg = theme.get(f"btn_{kind}_fg", theme["btn_secondary_fg"])
            hover_bg = theme.get(f"btn_{kind}_hover", bg)
            btn.config(bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg)

        # Re-render Breakdown Badges
        if hasattr(self, "san_spans") and self.san_spans:
            raw_breakdown = {}
            for _, _, _, _, ok, ov in self.san_spans:
                lbl = f"{ok} ➔ {ov}"
                raw_breakdown[lbl] = raw_breakdown.get(lbl, 0) + 1
            self._render_breakdown_badges(self.san_breakdown_frame, raw_breakdown, self.san_output, self.san_spans)

        if hasattr(self, "unsan_spans") and self.unsan_spans:
            raw_breakdown = {}
            for _, _, _, _, ok, ov in self.unsan_spans:
                lbl = f"{ok} ➔ {ov}"
                raw_breakdown[lbl] = raw_breakdown.get(lbl, 0) + 1
            self._render_breakdown_badges(self.unsan_breakdown_frame, raw_breakdown, self.unsan_output, self.unsan_spans)

    # =========================================================================
    # GLOBAL CONFIG & COLLISION HANDLING
    # =========================================================================
    def show_collision_details(self):
        if not self.engine.collisions:
            messagebox.showinfo("No Collisions", "No placeholder collisions detected! All reverse mappings are 1:1 safe.")
            return

        details = []
        for p, secrets in self.engine.collisions.items():
            sec_list = "\n".join([f"     - '{s}'" + (" (default restored)" if i == 0 else " (skipped on restore)") for i, s in enumerate(secrets)])
            details.append(f"  • Placeholder '{p}' is shared by:\n{sec_list}")

        msg = (
            f"Detected {len(self.engine.collisions)} Placeholder Collision(s):\n\n"
            + "\n\n".join(details)
            + "\n\nWhy this matters:\n"
            "When unsanitizing an AI command containing these placeholders, the tool cannot know "
            "which original secret was intended, so it defaults to the first one.\n\n"
            "Would you like to switch to the 'Manage Rules' tab to view and fix them?"
        )

        if messagebox.askyesno("Colliding Placeholders Details", msg):
            self.switch_tab("rules")
            self.show_collisions_only_var.set(True)
            self.refresh_rules_table()

    def browse_config(self):
        selected = filedialog.askopenfilename(
            title="Select Replacement JSON Config",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=os.path.dirname(self.engine.config_path)
        )
        if selected:
            self.engine.load_config(selected)
            self.lbl_config.config(text=f"📄 {os.path.basename(self.engine.config_path)}")
            self.refresh_rules_table()
            self.set_status(f"Loaded config from {os.path.basename(selected)}.")

    def reload_config(self):
        if self.engine.load_config():
            self.refresh_rules_table()
            self.set_status(f"Reloaded {len(self.engine.rules)} rules from {os.path.basename(self.engine.config_path)}.")
        else:
            self.set_status("Failed to reload configuration.")

    def _update_status_bar(self):
        rule_count = len(self.engine.rules)
        collision_count = len(self.engine.collisions)
        self.status_right.config(text=f"{rule_count} Rules Active")
        if collision_count > 0:
            self.btn_collision_warn.config(
                text=f"⚠️ {collision_count} Collision(s) Detected - Click to View",
                bg="#7f1d1d",
                fg="#fecaca",
                activebackground="#991b1b"
            )
            self.btn_collision_warn.pack(side=tk.RIGHT, padx=(0, 10))
        else:
            self.btn_collision_warn.pack_forget()
        self.set_status(f"🟢 Engine Ready ({rule_count} rules loaded from {os.path.basename(self.engine.config_path)})")

    def set_status(self, msg: str):
        self.status_bar.config(text=msg)


def main():
    parser = argparse.ArgumentParser(description="Sanitizer Studio")
    parser.add_argument("--tab", choices=["sanitize", "unsanitize", "rules"], default="sanitize", help="Initial tab to display.")
    args = parser.parse_args()

    root = tk.Tk()
    app = SanitizerStudioApp(root, initial_tab=args.tab)
    root.mainloop()


if __name__ == "__main__":
    main()
