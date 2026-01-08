# views/tenant_tab.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from module.tenant_service import (
    create_tenant,
    get_all_tenant,
    update_tenant,
    delete_tenant,
    validate_tenant
)

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


class tenantTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])

        # State
        self.current_tenant_id = None
        self.tenants_cache = []
        self.is_edit_mode = False

        # Variables
        self.full_name_var = ctk.StringVar()
        self.phone_var = ctk.StringVar()
        self.id_number_var = ctk.StringVar()
        self.address_var = ctk.StringVar()
        self.birth_var = ctk.StringVar()
        self.sex_var = ctk.StringVar(value="Nam")
        self.note_var = ctk.StringVar()
        self.search_var = ctk.StringVar()

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
            text="QUẢN LÝ KHÁCH THUÊ",
            font=("Inter", 28, "bold"),
            text_color=COLORS['text_dark']
        ).pack(anchor='w')

        ctk.CTkLabel(
            header,
            text="Thêm, sửa, xóa và quản lý thông tin khách thuê",
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
        for i in range(3):
            form_inner.grid_columnconfigure(i * 2 + 1, weight=1)

        # Row 0
        self._create_label(form_inner, "Tên khách *", 0, 0)
        self.entry_name = self._create_entry(form_inner, 0, 1, self.full_name_var, width=200)

        self._create_label(form_inner, "SĐT", 0, 2)
        entry_phone = self._create_entry(form_inner, 0, 3, self.phone_var, width=150)
        entry_phone.configure(validate="key",
                              validatecommand=(entry_phone.register(
                                  lambda s: s.isdigit() or s == ""), "%P"))

        self._create_label(form_inner, "Giới tính", 0, 4)
        self.combo_sex = ctk.CTkComboBox(
            form_inner,
            values=["Nam", "Nữ", "Khác"],
            variable=self.sex_var,
            width=120,
            font=("Inter", 13),
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary']
        )
        self.combo_sex.grid(row=0, column=5, padx=(5, 10), pady=8, sticky='w')

        # Row 1
        self._create_label(form_inner, "CCCD/CMND *", 1, 0)
        self.entry_idnum = self._create_entry(form_inner, 1, 1, self.id_number_var, width=200)

        self._create_label(form_inner, "Ngày sinh", 1, 2)
        self.date_birth = DateEntry(
            form_inner,
            textvariable=self.birth_var,
            date_pattern="dd/mm/yyyy",
            width=16,
            font=("Inter", 12)
        )
        self.date_birth.grid(row=1, column=3, padx=(5, 10), pady=8, sticky='w')

        self._create_label(form_inner, "Địa chỉ", 1, 4)
        self.entry_address = self._create_entry(form_inner, 1, 5, self.address_var, width=200)

        # Row 2
        self._create_label(form_inner, "Ghi chú", 2, 0)
        self.entry_note = ctk.CTkEntry(
            form_inner,
            textvariable=self.note_var,
            width=600,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        self.entry_note.grid(row=2, column=1, columnspan=5, padx=(5, 10), pady=8, sticky='ew')

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

    def _create_entry(self, parent, row, col, variable, width=150):
        """Helper to create entry"""
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
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

        search_entry = ctk.CTkEntry(
            left_frame,
            textvariable=self.search_var,
            placeholder_text="Tìm theo tên, SĐT, CCCD...",
            width=350,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        search_entry.pack(side='left')
        # Auto-search on typing
        search_entry.bind("<KeyRelease>", lambda e: self.apply_search())

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

        # Thêm button (visible in NEW mode)
        self.btn_add = ctk.CTkButton(
            right_frame,
            text="➕ Thêm",
            width=100,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['success'],
            hover_color='#059669',
            corner_radius=8,
            command=self.on_create_tenant
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
            command=self.on_update_tenant
        )
        self.btn_update.pack(side='left', padx=5)

        # Xóa button (visible in EDIT mode)
        self.btn_delete = ctk.CTkButton(
            right_frame,
            text="🗑️ Xóa",
            width=120,
            height=36,
            font=("Inter", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color='#dc2626',
            corner_radius=8,
            command=self.on_delete_tenant
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

        cols = ("id", "name", "sex", "phone", "idno", "address", "birth", "note")
        headers = {
            "id": "ID", "name": "Họ tên", "sex": "Giới tính",
            "phone": "SĐT", "idno": "CCCD",
            "address": "Địa chỉ", "birth": "Ngày sinh", "note": "Ghi chú"
        }

        widths = {
            "id": 50, "name": 180, "sex": 90, "phone": 110,
            "idno": 130, "address": 200, "birth": 110, "note": 150
        }

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                             anchor="center" if c in ("id", "sex") else "w")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

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

    def _get_sex_int(self, text):
        """Convert sex text to int"""
        return {"Nam": 0, "Nữ": 1, "Khác": 2}.get(text, 0)

    def _get_sex_str(self, val):
        """Convert sex int to text"""
        return {0: "Nam", 1: "Nữ", 2: "Khác"}.get(val, "Nam")

    def _load_data(self):
        """Load data from database"""
        self.tenants_cache = get_all_tenant()
        self.render_table(self.tenants_cache)

    def render_table(self, tenants):
        """Render table with tenant data"""
        self.tree.delete(*self.tree.get_children())
        for r in tenants:
            self.tree.insert("", "end", values=(
                r["tenant_id"],
                r["full_name"],
                self._get_sex_str(r["sex"]),
                r["phone"] or "",
                r["id_number"],
                r["address"] or "",
                r["birth"] or "",
                r["note"] or ""
            ))

    def apply_search(self):
        """Apply search filter"""
        query = (self.search_var.get() or "").strip().lower()

        def match(r):
            if not query:
                return True
            haystack = " ".join([
                str(r["full_name"] or ""),
                str(r["phone"] or ""),
                str(r["id_number"] or ""),
                str(r["address"] or ""),
                str(r["birth"] or ""),
                str(r["note"] or "")
            ]).lower()
            return query in haystack

        self.render_table([r for r in self.tenants_cache if match(r)])

    def on_select(self, _):
        """Handle tenant selection"""
        sel = self.tree.selection()
        if not sel:
            return

        v = self.tree.item(sel[0], "values")
        self.current_tenant_id = int(v[0])
        self.is_edit_mode = True
        self._update_button_visibility()

        self.full_name_var.set(v[1])
        self.sex_var.set(v[2])
        self.phone_var.set(v[3])
        self.id_number_var.set(v[4])
        self.address_var.set(v[5])
        self.birth_var.set(v[6])
        self.note_var.set(v[7])

    def on_create_tenant(self):
        """Create new tenant"""
        data = self._collect_data()
        if not data:
            return
        if not data["full_name"]:
            messagebox.showwarning("Lỗi", "Vui lòng nhập tên khách hàng!", parent=self)
            return
        phone = self.phone_var.get().strip()
        if phone and (len(phone) < 10 or len(phone) > 11):
            messagebox.showwarning("Lỗi", "Số điện thoại tối thiểu 10 ký tự và tối đa 11 ký tự", parent=self)
            return
        if not data["id_number"]:
            messagebox.showwarning("Lỗi", "Vui lòng nhập CCCD/CMND!", parent=self)
            return
        id_number = self.id_number_var.get().strip()
        if id_number and len(id_number) != 12:
            messagebox.showwarning("Lỗi", "CCCD phải đúng 12 ký tự", parent=self)
            return
        if any(r["id_number"].upper() == data["id_number"].upper() for r in self.tenants_cache):
            messagebox.showwarning("Lỗi", f"Khách hàng đã tồn tại!", parent=self)
            return
        try:
            create_tenant(validate_tenant(data))
            messagebox.showinfo("Thành công", "Thêm khách hàng thành công", parent=self)
            self.reset_form()
            self._load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_update_tenant(self):
        """Update existing tenant"""
        if not self.current_tenant_id:
            messagebox.showwarning("Chưa chọn", "Chọn khách hàng trước", parent=self)
            return
        data = self._collect_data()
        if not data:
            return
        if not data["full_name"]:
            messagebox.showwarning("Lỗi", "Vui lòng nhập tên khách hàng!", parent=self)
            return
        phone = self.phone_var.get().strip()
        if phone and (len(phone) < 10 or len(phone) > 11):
            messagebox.showwarning("Lỗi", "Số điện thoại tối thiểu 10 ký tự và tối đa 11 ký tự", parent=self)
            return
        if not data["id_number"]:
            messagebox.showwarning("Lỗi", "Vui lòng nhập CCCD/CMND!", parent=self)
            return
        id_number = self.id_number_var.get().strip()
        if id_number and len(id_number) != 12:
            messagebox.showwarning("Lỗi", "CCCD phải đúng 12 ký tự", parent=self)
            return
        if any(r["id_number"].upper() == data["id_number"].upper() for r in self.tenants_cache if
               r["tenant_id"] != self.current_tenant_id):
            messagebox.showwarning("Lỗi", f"Khách hàng đã tồn tại!", parent=self)
            return
        try:
            update_tenant(self.current_tenant_id, validate_tenant(data))
            messagebox.showinfo("Thành công", "Đã cập nhật", parent=self)
            self.reset_form()
            self._load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_delete_tenant(self):
        """Delete tenant"""
        if not self.current_tenant_id:
            messagebox.showwarning("Lỗi", "Vui lòng chọn khách hàng cần xóa!", parent=self)
            return

        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa khách hàng này?", parent=self):
            return

        try:
            delete_tenant(self.current_tenant_id)
            messagebox.showinfo("Thành công", "Đã xóa khách hàng thành công!", parent=self)
            self.reset_form()
            self._load_data()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa khách hàng: {str(e)}", parent=self)

    def reset_form(self):
        """Reset form to NEW mode"""
        self.current_tenant_id = None
        self.is_edit_mode = False
        self._update_button_visibility()

        self.full_name_var.set("")
        self.phone_var.set("")
        self.id_number_var.set("")
        self.address_var.set("")
        self.birth_var.set("")
        self.note_var.set("")
        self.sex_var.set("Nam")

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def _collect_data(self):
        """Collect data from form"""
        return {
            "full_name": self.full_name_var.get(),
            "sex": self._get_sex_int(self.sex_var.get()),
            "phone": self.phone_var.get() or None,
            "id_number": self.id_number_var.get(),
            "address": self.address_var.get() or None,
            "birth": self.birth_var.get() or None,
            "note": self.note_var.get() or None
        }