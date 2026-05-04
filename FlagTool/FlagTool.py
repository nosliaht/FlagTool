import configparser, re, tkinter as tk
from tkinter import ttk, messagebox

hex_to_int = lambda h: int(h, 16)
int_to_hex = lambda v: f"{v:X}"
is_hex_string = lambda v: all(c in "0123456789abcdefABCDEF" for c in (v[2:] if v.lower().startswith("0x") else v)) and v != ""

class ConfigLoader:
    _parsers = {}

    @classmethod
    def _get_parser(cls, file_path, encoding="utf-8", optionxform_str=False):
        if file_path not in cls._parsers:
            parser = configparser.ConfigParser()
            if optionxform_str:
                parser.optionxform = str
            parser.read(file_path, encoding=encoding)
            cls._parsers[file_path] = parser
        return cls._parsers[file_path]

    @classmethod
    def get_value(cls, file_path, section, key, fallback_value, parser_type=str, encoding="utf-8", optionxform_str=False):
        parser = cls._get_parser(file_path, encoding, optionxform_str)
        try:
            if parser.has_section(section):
                if parser_type == int:
                    return parser.getint(section, key, fallback=fallback_value)
                elif parser_type == float:
                    return parser.getfloat(section, key, fallback=fallback_value)
                elif parser_type == bool:
                    return parser.getboolean(section, key, fallback=fallback_value)
                return parser.get(section, key, fallback=fallback_value)
        except Exception:
            pass
        return fallback_value

    @classmethod
    def load_colors(cls, file_path="color.ini"):
        colors_map = {
            "background": "#000", "header": "#000", "card": "#000", "highlight": "#000",
            "text": "#000", "button": "#000", "button_text": "#000",
            "button_active": "#000", "button_active_text": "#000",
            "frame_selected": "#000", "frame_normal": "#000",
            "frame_text": "#000", "frame_null": "#000", "border": "#000"
        }
        parser = cls._get_parser(file_path)
        if parser.has_section("colors"):
            for k in colors_map:
                colors_map[k] = parser.get("colors", k, fallback=colors_map[k])
        return colors_map

    @classmethod
    def load_fonts(cls, file_path="font.ini"):
        parser = cls._get_parser(file_path)
        font_configs = {}
        default_name = parser.get("default", "name", fallback="Arial")
        default_size = parser.getint("default", "size", fallback=9)

        for s in parser.sections():
            name = parser.get(s, "name", fallback=default_name)
            size = parser.getint(s, "size", fallback=default_size)
            font_configs[s] = {"name": name, "size": size}
        return font_configs

    @classmethod
    def load_interface_dimensions(cls, file_path="interface.ini"):
        parser = cls._get_parser(file_path)
        dimensions = {}
        for s in ["window", "toolbar", "statusbar", "cell", "button", "label", "entry", "spacing"]:
            if parser.has_section(s):
                for k in parser.items(s):
                    dimensions[s + "_" + k[0]] = parser.getint(s, k[0], fallback=0)
        return dimensions

    @classmethod
    def parse_section_flags(cls, parser, section_name, value_conversion=int):
        if parser.has_section(section_name):
            return [(v, value_conversion(k)) for k, v in parser[section_name].items()]
        return []

    @classmethod
    def parse_class_flags(cls, parser):
        class_flags = []
        for s in parser.sections():
            if s.startswith("class_"):
                class_flags.append((s.split("_", 1)[1], [(v, k) for k, v in parser[s].items()]))
        return class_flags

    @classmethod
    def load_flags(cls, file_path="flags.ini"):
        parser = cls._get_parser(file_path, optionxform_str=True)
        r = cls.parse_section_flags(parser, "item")
        e = cls.parse_section_flags(parser, "enchant")
        so = cls.parse_section_flags(parser, "Spell OpFlag")
        sre = cls.parse_section_flags(parser, "Spell RestrictEquip")
        c = cls.parse_class_flags(parser)
        p = cls.parse_section_flags(parser, "ItemPlus")
        m = cls.parse_section_flags(parser, "mission")
        msf = cls.parse_section_flags(parser, "MonsterSpecialFlag")
        return r, e, so, sre, c, p, m, msf

C = ConfigLoader.load_colors()
_FONTS = ConfigLoader.load_fonts()
D = ConfigLoader.load_interface_dimensions()
R, E, SO, SRE, CLS, P, M, MSF = ConfigLoader.load_flags()
DECIMAL_TAB_KEYS = {
    "itens", "ItemPlus", "enchants", "spellOpFlag", "spellRestrictEquip",
    "mission", "monsterSpecialFlag"
}
TAB_DEFINITIONS = [
    ("Item", "itens"),
    ("ItemPlus", "ItemPlus"),
    ("Class", "classes"),
    ("Enchant", "enchants"),
    ("Spell OpFlag", "spellOpFlag"),
    ("Spell RestrictEquip", "spellRestrictEquip"),
    ("Mission", "mission"),
    ("Monster SpecialFlag", "monsterSpecialFlag"),
]

def get_font_config(section, modifier=""):
    s = section if section in _FONTS else "default"
    name = _FONTS[s]["name"]
    size = _FONTS[s]["size"]
    return (name, size, modifier) if modifier else (name, size)

def format_display_text(text):
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)

def get_cell_font_config(text, is_bold=False):
    text = format_display_text(text)
    name, size = get_font_config("cell")
    if len(text) > 24:
        size -= 1
    if len(text) > 34:
        size -= 1
    modifier = "bold" if is_bold else ""
    return (name, max(size, 8), modifier) if modifier else (name, max(size, 8))

def get_button_width(text):
    return max(D.get("button_width", 80) // 7, len(format_display_text(text)) + 2)

def get_tab_display_text(key):
    for text, tab_key in TAB_DEFINITIONS:
        if tab_key == key:
            return format_display_text(text)
    return format_display_text(key)

class BaseTab(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, bg=C["background"])
        self.selected_values = set()
        self.cells = {}
        self.total_value = 0
        self.update_callback = callback

    def _update_cell_visual_state(self, value, is_selected):
        frame = self.cells[value]
        label = frame.winfo_children()[0]
        if is_selected:
            frame.config(bg=C["frame_selected"], highlightbackground=C["frame_selected"])
            label.config(bg=C["frame_selected"], fg=C["frame_text"])
        else:
            frame.config(bg=C["frame_normal"], highlightbackground=C["border"])
            label.config(bg=C["frame_normal"], fg=C["text"])

    def create_cell(self, parent, text, value, is_bold=False):
        display_text = format_display_text(text)
        frame = tk.Frame(parent, bg=C["frame_normal"], highlightbackground=C["border"],
                     highlightthickness=D.get("cell_border", 1), cursor="hand2",
                     width=D.get("cell_width", 140), height=D.get("cell_height", 36))
        frame.pack_propagate(False)
        label = tk.Label(
            frame, text=display_text, font=get_cell_font_config(text, is_bold), fg=C["text"],
            bg=C["frame_normal"], anchor="center", justify="center",
            wraplength=max(40, D.get("cell_width", 150) - (D.get("cell_padx", 6) * 2))
        )
        label.pack(expand=True, fill=tk.BOTH, padx=D.get("cell_padx", 6), pady=D.get("cell_pady", 6))

        for widget in [frame, label]:
            widget.bind("<Button-1>", lambda event, val=value: self.toggle_selection(val))
            widget.bind("<Enter>", lambda event, fr=frame, val=value: fr.config(highlightbackground=C["highlight"] if val not in self.selected_values else C["frame_selected"]))
            widget.bind("<Leave>", lambda event, fr=frame, val=value: fr.config(highlightbackground=(C["frame_selected"] if val in self.selected_values else C["border"])))
        self.cells[value] = frame
        return frame

    def create_null_cell(self, parent):
        return tk.Frame(parent, bg=C["frame_null"], highlightthickness=0)

    def toggle_selection(self, value):
        if value in self.selected_values:
            self.selected_values.remove(value)
            self._update_cell_visual_state(value, False)
        else:
            if value == 0:
                for selected_value in list(self.selected_values):
                    self._update_cell_visual_state(selected_value, False)
                self.selected_values.clear()
            elif 0 in self.selected_values:
                self.selected_values.remove(0)
                self._update_cell_visual_state(0, False)
            self.selected_values.add(value)
            self._update_cell_visual_state(value, True)
        self.update_total()

    def update_total(self):
        self.total_value = sum(self.selected_values)
        self.update_callback(self.total_value)

    def mark_all_flags(self):
        selectable_values = {value for value in self.cells if value != 0}
        self.selected_values = selectable_values if selectable_values else set(self.cells.keys())
        for value in self.selected_values:
            self._update_cell_visual_state(value, True)
        if 0 in self.cells and 0 not in self.selected_values:
            self._update_cell_visual_state(0, False)
        self.update_total()

    def clear_all_flags(self):
        self.selected_values.clear()
        self.total_value = 0
        for value in self.cells:
            self._update_cell_visual_state(value, False)
        self.update_total()

    def check_input_flags(self, input_value, validation_func, conversion_func, error_msg_type): # Removed zero_value_display_func
        if not validation_func(input_value):
            messagebox.showwarning("Error", f"Invalid {error_msg_type} value.")
            return
        
        d = conversion_func(input_value)
        
        matched_flags = [v for v in self.cells if (d & v) == v and v != 0]
        should_select_zero = d == 0 and 0 in self.cells

        if not matched_flags and d != 0:
            messagebox.showinfo("Info", "No flag matches.")

        self.selected_values.clear()
        for v in self.cells:
            is_match = ((d & v) == v and v != 0) or (should_select_zero and v == 0)
            if is_match:
                self.selected_values.add(v)
            self._update_cell_visual_state(v, is_match)
        
        self.total_value = d 
        self.update_callback(self.total_value)

    def _create_grid_layout(self, data, grid_frame, cells_per_row, bold_first_column=False, value_conversion=int):
        num_rows = (len(data) + cells_per_row - 1) // cells_per_row
        for i, (name, val) in enumerate(data):
            converted_val = value_conversion(val) if isinstance(val, str) else val
            row = i % num_rows
            col = i // num_rows
            self.create_cell(grid_frame, name, converted_val, is_bold=(bold_first_column and col == 0)).grid(
                row=row, column=col, sticky="nsew",
                padx=D.get("cell_padding", 3), pady=D.get("cell_padding", 3)
            )
        for c in range(cells_per_row):
            grid_frame.grid_columnconfigure(c, weight=1, uniform="c")
        for r in range(num_rows):
            grid_frame.grid_rowconfigure(r, weight=1, uniform="r")

class DecimalFlagsTab(BaseTab):
    def __init__(self, parent, callback, data):
        super().__init__(parent, callback)
        grid_frame = tk.Frame(self, bg=C["background"])
        grid_frame.pack(expand=True)
        self._create_grid_layout(data, grid_frame, 4, value_conversion=int)

    def check_input_flags(self, value):
        super().check_input_flags(value, str.isdigit, int, "decimal")

class ClassFlagsTab(BaseTab):
    def __init__(self, parent, callback):
        super().__init__(parent, callback)
        grid_frame = tk.Frame(self, bg=C["background"])
        grid_frame.pack(expand=True)
        
        main_class_data = CLS[0][1] if CLS else []
        other_classes_data = CLS[1:]
        
        max_rows = max(len(main_class_data), *(len(x[1]) for x in other_classes_data)) if other_classes_data else len(main_class_data)

        for r in range(max_rows):
            if r < len(main_class_data):
                self.create_cell(grid_frame, main_class_data[r][0], hex_to_int(main_class_data[r][1]), is_bold=True).grid(
                    row=r, column=0, sticky="nsew", padx=D.get("cell_padding", 3), pady=D.get("cell_padding", 3)
                )
            else:
                self.create_null_cell(grid_frame).grid(row=r, column=0, sticky="nsew", padx=D.get("cell_padding", 3), pady=D.get("cell_padding", 3))
        
        for col, (_, class_items) in enumerate(other_classes_data, start=1):
            for r in range(max_rows):
                if r < len(class_items):
                    self.create_cell(grid_frame, class_items[r][0], hex_to_int(class_items[r][1])).grid(
                        row=r, column=col, sticky="nsew", padx=D.get("cell_padding", 3), pady=D.get("cell_padding", 3)
                    )
                else:
                    self.create_null_cell(grid_frame).grid(row=r, column=col, sticky="nsew", padx=D.get("cell_padding", 3), pady=D.get("cell_padding", 3))
        
        for c in range(1 + len(other_classes_data)):
            grid_frame.grid_columnconfigure(c, weight=1, uniform="c")
        for r in range(max_rows):
            grid_frame.grid_rowconfigure(r, weight=1, uniform="r")

    def update_total(self):
        total = 0
        for value_int in self.selected_values:
            total |= value_int
        self.total_value = total
        self.update_callback(total)

    def check_input_flags(self, value):
        processed_val = value[2:] if value.lower().startswith("0x") else value
        super().check_input_flags(processed_val, is_hex_string, hex_to_int, "hexadecimal")

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flags Calculator")
        self.geometry(f"{D.get('window_width', 720)}x{D.get('window_height', 550)}")
        self.resizable(False, False)
        self.configure(bg=C["background"])
        self.current_tab_key = "itens"
        self._create_toolbar()
        self.content_frame = tk.Frame(self, bg=C["background"])
        self.content_frame.pack(fill="both", expand=True)
        self.tabs = {
            "itens": DecimalFlagsTab(self.content_frame, self.update_result_display, R),
            "ItemPlus": DecimalFlagsTab(self.content_frame, self.update_result_display, P),
            "classes": ClassFlagsTab(self.content_frame, self.update_result_display),
            "enchants": DecimalFlagsTab(self.content_frame, self.update_result_display, E),
            "spellOpFlag": DecimalFlagsTab(self.content_frame, self.update_result_display, SO),
            "spellRestrictEquip": DecimalFlagsTab(self.content_frame, self.update_result_display, SRE),
            "mission": DecimalFlagsTab(self.content_frame, self.update_result_display, M),
            "monsterSpecialFlag": DecimalFlagsTab(self.content_frame, self.update_result_display, MSF)
        }
        self._create_statusbar()
        self.tabs[self.current_tab_key].pack(fill="both", expand=True)
        self.switch_tab(self.current_tab_key)

    def _create_styled_button(self, parent, text, command, side, padx_val, is_tab_button=False):
        display_text = format_display_text(text)
        btn_config = {
            "font": get_font_config("tab", "bold") if is_tab_button else get_font_config("button", "bold"),
            "bg": C["button"], "fg": C["button_text"],
            "activebackground": C["button_active"], "activeforeground": C["button_active_text"],
            "relief": "flat", "bd": 0, "cursor": "hand2",
            "pady": D.get("button_pady", 6),
            "highlightthickness": 1, "highlightbackground": C["border"]
        }
        btn_config["width"] = get_button_width(text)
        
        btn = tk.Button(parent, text=display_text, command=command, **btn_config)
        btn.pack(side=side, padx=padx_val)
        if not is_tab_button:
            btn.bind("<Enter>", lambda event, b=btn: b.config(
                bg=C["button_active"], fg=C["button_active_text"], highlightbackground=C["highlight"]
            ))
            btn.bind("<Leave>", lambda event, b=btn: b.config(
                bg=C["button"], fg=C["button_text"], highlightbackground=C["border"]
            ))
        return btn

    def _create_toolbar(self):
        toolbar_frame = tk.Frame(self, bg=C["header"], height=D.get("toolbar_height", 42))
        toolbar_frame.pack(side=tk.TOP, fill="x")
        toolbar_frame.pack_propagate(False)
        center_frame = tk.Frame(toolbar_frame, bg=C["header"])
        center_frame.pack(side=tk.LEFT, anchor="w", padx=D.get("toolbar_padx", 8), pady=D.get("toolbar_pady", 6))
        
        tk.Label(
            center_frame, text="Tool", font=get_font_config("header", "bold"),
            fg=C["highlight"], bg=C["header"]
        ).pack(side=tk.LEFT, padx=(0, D.get("label_padx", 6)))
        
        self.tab_selector = tk.Menubutton(
            center_frame, text="", font=get_font_config("tab", "bold"),
            bg=C["button"], fg=C["button_text"], activebackground=C["button_active"],
            activeforeground=C["button_active_text"], relief="flat", bd=0,
            cursor="hand2", pady=D.get("button_pady", 6), width=24,
            highlightthickness=1, highlightbackground=C["border"]
        )
        self.tab_menu = tk.Menu(
            self.tab_selector, tearoff=False, bg=C["button"], fg=C["button_text"],
            activebackground=C["button_active"], activeforeground=C["button_active_text"],
            relief="flat", bd=0, font=get_font_config("tab")
        )
        for text, key in TAB_DEFINITIONS:
            self.tab_menu.add_command(label=format_display_text(text), command=lambda k=key: self.switch_tab(k))
        self.tab_selector.configure(menu=self.tab_menu)
        self.tab_selector.pack(side=tk.LEFT, padx=D.get("button_padx", 2))

    def _should_display_zero(self):
        return (
            hasattr(self, "tabs")
            and self.current_tab_key in self.tabs
            and self.tabs[self.current_tab_key].selected_values == {0}
        )

    def _create_statusbar(self):
        statusbar_frame = tk.Frame(self, bg=C["header"], height=D.get("statusbar_height", 42))
        statusbar_frame.pack(side=tk.BOTTOM, fill="x")
        statusbar_frame.pack_propagate(False)
        center_frame = tk.Frame(statusbar_frame, bg=C["header"])
        center_frame.pack(expand=True, padx=D.get("statusbar_padx", 8), pady=D.get("statusbar_pady", 6))
        
        button_padding = D.get("button_padx", 2)
        
        self._create_styled_button(center_frame, "Check", self.check_current_tab_flags, tk.LEFT, button_padding)
        self.result_entry = tk.Entry(
            center_frame, font=get_font_config("entry"), justify="center", width=D.get("entry_width", 18),
            bg=C["card"], fg=C["text"], insertbackground=C["highlight"], relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["highlight"],
            selectbackground=C["highlight"], selectforeground=C["button_active_text"]
        )
        self.result_entry.pack(side=tk.LEFT, ipady=D.get("button_pady", 6), padx=button_padding)
        self._create_styled_button(center_frame, "Copy", self.copy_result_to_clipboard, tk.LEFT, button_padding)
        self._create_styled_button(center_frame, "Mark All", self.mark_all_current_tab_flags, tk.LEFT, button_padding)
        self._create_styled_button(center_frame, "Clear All", self.clear_all_current_tab_flags, tk.LEFT, button_padding)

    def update_result_display(self, total):
        self.result_entry.delete(0, tk.END)
        if total != 0 or self._should_display_zero():
            formatted_value = str(total) if self.current_tab_key in DECIMAL_TAB_KEYS else int_to_hex(total)
            self.result_entry.insert(0, formatted_value)

    def check_current_tab_flags(self):
        self.tabs[self.current_tab_key].check_input_flags(self.result_entry.get().strip())

    def copy_result_to_clipboard(self):
        current_tab = self.tabs[self.current_tab_key]
        value_to_copy = str(current_tab.total_value) if self.current_tab_key in DECIMAL_TAB_KEYS else int_to_hex(current_tab.total_value)
        self.clipboard_clear()
        self.clipboard_append(value_to_copy)
        messagebox.showinfo("Success", f"Value {value_to_copy} copied!")

    def mark_all_current_tab_flags(self):
        self.tabs[self.current_tab_key].mark_all_flags()

    def clear_all_current_tab_flags(self):
        self.tabs[self.current_tab_key].clear_all_flags()

    def switch_tab(self, key):
        for tab in self.tabs.values():
            tab.pack_forget()
        self.tabs[key].pack(fill="both", expand=True)
        self.current_tab_key = key
        self.tab_selector.config(text=f"{get_tab_display_text(key)}  ▾")
        self.update_result_display(self.tabs[key].total_value)

if __name__ == "__main__":
    Application().mainloop()
