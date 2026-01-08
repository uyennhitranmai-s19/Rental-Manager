import customtkinter as ctk
from tkinter import ttk, messagebox
from module.room_service import get_all_rooms, create_room, update_room, delete_room
from utils.format import format_currency, parse_currency, format_money

STATUS_MAP = {
    "Trống": 0,
    "Đang thuê": 1,
    "Đang chuẩn bị": 2
}
STATUS_MAP_REV = {v: k for k, v in STATUS_MAP.items()}

# ===== COLOR SCHEME =====
COLORS = {
    'primary': '#3b82f6',  # Blue - Info
    'success': '#10b981',  # Green - Add/Create
    'warning': '#f59e0b',  # Orange - Update
    'danger': '#ef4444',  # Red - Delete
    'secondary': '#6b7280',  # Gray - Reset/Secondary
    'bg_light': '#f8fafc',  # Light background
    'bg_white': '#ffffff',  # White background
    'border': '#e2e8f0',  # Border color
    'text_dark': '#1e293b',  # Dark text
    'text_gray': '#64748b'  # Gray text
}


class roomTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLORS['bg_light'])
        self.current_room_id = None
        self.rooms_cache = []
        self.is_edit_mode = False
        self._build_ui()
        self._load_data()

    def initialize(self):
        """Called when tab is shown"""
        self._load_data()
        self.reset_form()

    def _build_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        self._build_header(main_container)

        # Form section
        self._build_form(main_container)

        # Action bar (search + buttons)
        self._build_action_bar(main_container)

        # Table section
        self._build_table(main_container)

    def _build_header(self, parent):
        """Create header section"""
        header = ctk.CTkFrame(parent, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="QUẢN LÝ PHÒNG TRỌ",
            font=("Inter", 28, "bold"),
            text_color=COLORS['text_dark']
        ).pack(anchor='w')

        ctk.CTkLabel(
            header,
            text="Thêm, sửa, xóa và quản lý thông tin phòng trọ",
            font=("Inter", 13),
            text_color=COLORS['text_gray']
        ).pack(anchor='w', pady=(5, 0))

    def _build_form(self, parent):
        """Create form section"""
        form_container = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_white'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border']
        )
        form_container.pack(fill='x', pady=(0, 15))

        form_inner = ctk.CTkFrame(form_container, fg_color='transparent')
        form_inner.pack(fill='x', padx=25, pady=20)

        # Configure grid
        for i in range(4):
            form_inner.grid_columnconfigure(i * 2 + 1, weight=1)

        # Row 0
        self._create_label(form_inner, "Tên phòng *", 0, 0)
        self.entry_name = self._create_entry(form_inner, 0, 1, width=180)

        self._create_label(form_inner, "Tầng", 0, 2)
        self.entry_floor = self._create_entry(form_inner, 0, 3, width=120)

        self._create_label(form_inner, "Diện tích (m²)", 0, 4)
        self.entry_area = self._create_entry(form_inner, 0, 5, width=120)

        self._create_label(form_inner, "Trạng thái", 0, 6)
        self.combo_status = ctk.CTkComboBox(
            form_inner,
            values=list(STATUS_MAP.keys()),
            width=140,
            state="readonly",
            font=("Inter", 13),
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary']
        )
        self.combo_status.set("Trống")
        self.combo_status.grid(row=0, column=7, padx=(5, 10), pady=8, sticky='w')

        # Row 1
        self._create_label(form_inner, "Giá thuê", 1, 0)
        self.entry_rent = self._create_entry(form_inner, 1, 1, width=180)
        self.entry_rent.bind("<KeyRelease>", format_money)

        self._create_label(form_inner, "Giá điện", 1, 2)
        self.entry_elec = self._create_entry(form_inner, 1, 3, width=120)
        self.entry_elec.bind("<KeyRelease>", format_money)

        self._create_label(form_inner, "Giá nước", 1, 4)
        self.entry_water = self._create_entry(form_inner, 1, 5, width=120)
        self.entry_water.bind("<KeyRelease>", format_money)

        self._create_label(form_inner, "Ghi chú", 1, 6)
        self.entry_note = self._create_entry(form_inner, 1, 7, width=140)

    def _create_label(self, parent, text, row, col):
        """Helper to create label"""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=("Inter", 13, "bold"),
            text_color=COLORS['text_dark']
        )
        label.grid(row=row, column=col, padx=(10, 5), pady=8, sticky='w')
        return label

    def _create_entry(self, parent, row, col, width=150):
        """Helper to create entry"""
        entry = ctk.CTkEntry(
            parent,
            width=width,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        entry.grid(row=row, column=col, padx=(5, 10), pady=8, sticky='w')
        return entry

    def _build_action_bar(self, parent):
        """Create action bar with search and buttons"""
        action_bar = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_white'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border']
        )
        action_bar.pack(fill='x', pady=(0, 15))

        action_inner = ctk.CTkFrame(action_bar, fg_color='transparent')
        action_inner.pack(fill='x', padx=25, pady=15)

        # Left side - Search
        left_frame = ctk.CTkFrame(action_inner, fg_color='transparent')
        left_frame.pack(side='left', fill='x', expand=True)

        ctk.CTkLabel(
            left_frame,
            text="Tìm kiếm:",
            font=("Inter", 13, "bold"),
            text_color=COLORS['text_dark']
        ).pack(side='left', padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            left_frame,
            placeholder_text="Nhập tên phòng...",
            width=280,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        self.search_entry.pack(side='left', padx=(0, 10))
        # Auto-search on typing
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_search())

        self.search_status = ctk.CTkComboBox(
            left_frame,
            values=["Tất cả"] + list(STATUS_MAP.keys()),
            width=150,
            height=36,
            state="readonly",
            font=("Inter", 13),
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary'],
            command=lambda e: self.apply_search()
        )
        self.search_status.set("Tất cả")
        self.search_status.pack(side='left')

        # Right side - Action buttons
        right_frame = ctk.CTkFrame(action_inner, fg_color='transparent')
        right_frame.pack(side='right')

        # Làm mới button (always visible)
        self.btn_reset = ctk.CTkButton(
            right_frame,
            text="Làm mới",
            width=100,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['secondary'],
            hover_color='#4b5563',
            corner_radius=8,
            command=self.reset_form
        )
        self.btn_reset.pack(side='left', padx=5)

        # Thêm mới button (visible in NEW mode)
        self.btn_add = ctk.CTkButton(
            right_frame,
            text="➕ Thêm mới",
            width=120,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['success'],
            hover_color='#059669',
            corner_radius=8,
            command=self.add_room
        )
        self.btn_add.pack(side='left', padx=5)

        # Cập nhật button (visible in EDIT mode)
        self.btn_update = ctk.CTkButton(
            right_frame,
            text="✏️ Cập nhật",
            width=120,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['warning'],
            hover_color='#d97706',
            corner_radius=8,
            command=self.update_room
        )
        self.btn_update.pack(side='left', padx=5)

        # Xóa button (visible in EDIT mode)
        self.btn_delete = ctk.CTkButton(
            right_frame,
            text="🗑️ Xóa",
            width=100,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color='#dc2626',
            corner_radius=8,
            command=self.delete_room
        )
        self.btn_delete.pack(side='left', padx=5)

        # Set initial mode
        self._update_button_visibility()

    def _update_button_visibility(self):
        """Update button visibility based on mode"""
        if self.is_edit_mode:
            # Edit mode: show update and delete, hide add
            self.btn_add.pack_forget()
            self.btn_update.pack(side='left', padx=5)
            self.btn_delete.pack(side='left', padx=5)
        else:
            # New mode: show add, hide update and delete
            self.btn_update.pack_forget()
            self.btn_delete.pack_forget()
            self.btn_add.pack(side='left', padx=5)

    def _build_table(self, parent):
        """Create table section"""
        table_container = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_white'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border']
        )
        table_container.pack(fill='both', expand=True)

        # Table frame with padding
        table_frame = ctk.CTkFrame(table_container, fg_color='transparent')
        table_frame.pack(fill='both', expand=True, padx=20, pady=20)

        cols = ("id", "name", "floor", "area", "rent", "elec", "water", "status", "note")
        headers = {
            "id": "ID", "name": "Tên phòng", "floor": "Tầng", "area": "Diện tích",
            "rent": "Giá thuê", "elec": "Giá điện", "water": "Giá nước",
            "status": "Trạng thái", "note": "Ghi chú"
        }

        widths = {"id": 50, "name": 130, "floor": 70, "area": 90,
                  "rent": 110, "elec": 100, "water": 100, "status": 120, "note": 180}

        anchors = {"id": "center", "name": "w", "floor": "center", "area": "center",
                   "rent": "e", "elec": "e", "water": "e", "status": "center", "note": "w"}

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor=anchors[col])

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_room)

        # Configure treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=COLORS['bg_white'],
                        foreground=COLORS['text_dark'],
                        fieldbackground=COLORS['bg_white'],
                        borderwidth=0,
                        font=("Inter", 12),
                        rowheight=35)
        style.configure("Treeview.Heading",
                        background=COLORS['bg_light'],
                        foreground=COLORS['text_dark'],
                        borderwidth=1,
                        font=("Inter", 12, "bold"))
        style.map('Treeview', background=[('selected', COLORS['primary'])])

    def on_select_room(self, event):
        """Handle room selection"""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item['values']
        if not values:
            return

        self.current_room_id = values[0]
        self.is_edit_mode = True
        self._update_button_visibility()

        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, values[1])

        self.entry_floor.delete(0, "end")
        self.entry_floor.insert(0, values[2] if values[2] != "-" else "")

        self.entry_area.delete(0, "end")
        self.entry_area.insert(0, values[3] if values[3] != "-" else "")

        self.entry_rent.delete(0, "end")
        self.entry_rent.insert(0, values[4])

        self.entry_elec.delete(0, "end")
        self.entry_elec.insert(0, values[5])

        self.entry_water.delete(0, "end")
        self.entry_water.insert(0, values[6])

        self.combo_status.set(values[7])

        self.entry_note.delete(0, "end")
        if len(values) > 8:
            self.entry_note.insert(0, values[8])

    def _load_data(self):
        """Load data from database"""
        self.rooms_cache = get_all_rooms()
        self.render_table(self.rooms_cache)

    def render_table(self, rooms):
        """Render table with room data"""
        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in rooms:
            status_vn = STATUS_MAP_REV.get(r["status"], str(r["status"]))
            floor_val = r["floor"] if r["floor"] is not None else "-"
            area_val = r["area_m2"] if r["area_m2"] is not None else "-"

            self.tree.insert("", "end", values=(
                r["room_id"],
                r["room_name"],
                floor_val,
                area_val,
                format_currency(r["base_rent"]),
                format_currency(r["electric_unit_price"]),
                format_currency(r["water_unit_price"]),
                status_vn,
                r["note"] or ""
            ))

    def apply_search(self):
        """Apply search filter"""
        query = (self.search_entry.get() or "").strip().lower()
        status_sel = self.search_status.get()
        status_db = None if status_sel == "Tất cả" else STATUS_MAP.get(status_sel)

        filtered = []
        for r in self.rooms_cache:
            if status_db is not None and r["status"] != status_db:
                continue

            if not query:
                filtered.append(r)
                continue

            if query in (r["room_name"] or "").lower():
                filtered.append(r)
                continue

        self.render_table(filtered)

    def _get_form_data(self):
        """Get and validate form data"""
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên phòng!", parent=self)
            self.entry_name.focus_set()
            return None

        try:
            area_str = self.entry_area.get().strip()
            area = float(area_str) if area_str else 0.0
            if area < 0:
                messagebox.showwarning("Lỗi", "Diện tích phải là số dương!", parent=self)
                self.entry_area.focus_set()
                return None

            floor_str = self.entry_floor.get().strip()
            floor = int(floor_str) if floor_str else None
            if floor is not None and floor < 0:
                messagebox.showwarning("Lỗi", "Số tầng phải là số dương!", parent=self)
                self.entry_floor.focus_set()
                return None

            rent = parse_currency(self.entry_rent.get())
            elec = parse_currency(self.entry_elec.get())
            water = parse_currency(self.entry_water.get())

            if rent < 0:
                messagebox.showwarning("Lỗi", "Giá thuê không được âm!", parent=self)
                self.entry_rent.focus_set()
                return None
            if elec < 0:
                messagebox.showwarning("Lỗi", "Giá điện không được âm!", parent=self)
                self.entry_elec.focus_set()
                return None
            if water < 0:
                messagebox.showwarning("Lỗi", "Giá nước không được âm!", parent=self)
                self.entry_water.focus_set()
                return None

        except ValueError as e:
            messagebox.showerror("Lỗi", f"Dữ liệu nhập không hợp lệ!\n{str(e)}", parent=self)
            return None

        return {
            "room_name": name,
            "area_m2": area,
            "floor": floor,
            "base_rent": rent,
            "electric_unit_price": elec,
            "water_unit_price": water,
            "status": STATUS_MAP[self.combo_status.get()],
            "note": self.entry_note.get().strip() or None
        }

    def reset_form(self):
        """Reset form to NEW mode"""
        self.current_room_id = None
        self.is_edit_mode = False
        self._update_button_visibility()

        for e in (self.entry_name, self.entry_area, self.entry_floor,
                  self.entry_rent, self.entry_elec, self.entry_water, self.entry_note):
            e.delete(0, "end")

        self.combo_status.set("Trống")
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def add_room(self):
        """Add new room"""
        data = self._get_form_data()
        if not data:
            return

        if any(r["room_name"].upper() == data["room_name"].upper() for r in self.rooms_cache):
            messagebox.showwarning("Lỗi", f"Phòng '{data['room_name']}' đã tồn tại!", parent=self)
            return

        try:
            create_room(data)
            messagebox.showinfo("Thành công", "Thêm phòng mới thành công!", parent=self)
            self._load_data()
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể thêm phòng:\n{str(e)}", parent=self)

    def update_room(self):
        """Update existing room"""
        if not self.current_room_id:
            return

        data = self._get_form_data()
        if not data:
            return

        for r in self.rooms_cache:
            if (r["room_name"].upper() == data["room_name"].upper() and
                    str(r["room_id"]) != str(self.current_room_id)):
                messagebox.showwarning("Lỗi", "Tên phòng này đã tồn tại!", parent=self)
                return

        try:
            update_room(self.current_room_id, data)
            messagebox.showinfo("Thành công", "Cập nhật thông tin phòng thành công!", parent=self)
            self._load_data()
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{str(e)}", parent=self)

    def delete_room(self):
        """Delete room"""
        if not self.current_room_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn phòng cần xóa!", parent=self)
            return

        room_name = next((r["room_name"] for r in self.rooms_cache
                          if r["room_id"] == self.current_room_id), "")

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa phòng {room_name}?", parent=self):
            return

        try:
            delete_room(self.current_room_id)
            messagebox.showinfo("Thành công", f"Đã xóa phòng {room_name} thành công!", parent=self)
            self._load_data()
            self.reset_form()
        except ValueError as e:
            messagebox.showerror("Không thể xóa", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xóa phòng.\n{str(e)}", parent=self)