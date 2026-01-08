# views/contract_tab.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import datetime
import os
import sys
import subprocess

from utils.format import format_currency, parse_currency, format_money
from module.contract_service import (
    get_all_contracts,
    create_contract,
    update_contract,
    delete_contract,
    end_contract,
    get_available_rooms,
    get_tenants_without_active_contract,
    get_contract_by_id,
    export_contract_to_pdf
)

# ===== COLOR SCHEME ===== (giống tenant_tab)
COLORS = {
    'primary':   '#3b82f6',
    'success':   '#10b981',
    'warning':   '#f59e0b',
    'danger':    '#ef4444',
    'purple':    '#8e44ad',    # Kết thúc HĐ
    'info':      '#3498db',    # Xuất PDF
    'secondary': '#6b7280',
    'bg_light':  '#f8fafc',
    'bg_white':  '#ffffff',
    'border':    '#e2e8f0',
    'text_dark': '#1e293b',
    'text_gray': '#64748b'
}


class contractTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])

        # State
        self.current_contract_id = None
        self.is_edit_mode = False

        # Cache cho combobox
        self.rooms_map = {}      # name -> {"id": id, "rent": rent}
        self.tenants_map = {}    # name -> id

        # Variables
        self.room_var = ctk.StringVar()
        self.tenant_var = ctk.StringVar()
        self.rent_var = ctk.StringVar()
        self.deposit_var = ctk.StringVar()
        self.deposit_date_var = ctk.StringVar(value=datetime.date.today().strftime("%d/%m/%Y"))
        self.start_date_var = ctk.StringVar()
        self.end_date_var = ctk.StringVar()
        self.elec_start_var = ctk.StringVar(value="0")
        self.water_start_var = ctk.StringVar(value="0")
        self.note_var = ctk.StringVar()
        self.search_var = ctk.StringVar()

        self._build_ui()
        self.initialize()

    def initialize(self):
        self._load_combobox_data()
        self._load_contracts()
        self.reset_form()

    def _build_ui(self):
        main_container = ctk.CTkFrame(self, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        self._build_header(main_container)
        self._build_form(main_container)
        self._build_action_bar(main_container)
        self._build_table(main_container)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="QUẢN LÝ HỢP ĐỒNG",
            font=("Inter", 28, "bold"),
            text_color=COLORS['text_dark']
        ).pack(anchor='w')

        ctk.CTkLabel(
            header,
            text="Thêm, sửa, kết thúc và xuất hợp đồng thuê phòng",
            font=("Inter", 13),
            text_color=COLORS['text_gray']
        ).pack(anchor='w', pady=(5, 0))

    def _build_form(self, parent):
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

        # Grid: 6 cột (label + field)
        for i in range(6):
            form_inner.grid_columnconfigure(i, weight=1 if i % 2 == 1 else 0)

        # Row 0
        self._create_label(form_inner, "Phòng *", 0, 0)
        self.cb_room = ctk.CTkComboBox(
            form_inner,
            variable=self.room_var,
            width=200,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border'],
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary'],
            command=self._on_room_selected
        )
        self.cb_room.grid(row=0, column=1, padx=(5, 15), pady=8, sticky='w')

        self._create_label(form_inner, "Khách thuê *", 0, 2)
        self.cb_tenant = ctk.CTkComboBox(
            form_inner,
            variable=self.tenant_var,
            width=250,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border'],
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary']
        )
        self.cb_tenant.grid(row=0, column=3, columnspan=3, padx=(5, 15), pady=8, sticky='w')

        # Row 1
        self._create_label(form_inner, "Giá thuê", 1, 0)
        self._create_entry(form_inner, 1, 1, self.rent_var, width=200, state="readonly", fg_color="#f1f5f9")

        self._create_label(form_inner, "Tiền cọc", 1, 2)
        entry_deposit = self._create_entry(form_inner, 1, 3, self.deposit_var, width=180)
        entry_deposit.bind("<KeyRelease>", format_money)

        self._create_label(form_inner, "Ngày cọc", 1, 4)
        DateEntry(
            form_inner,
            textvariable=self.deposit_date_var,
            date_pattern="dd/mm/yyyy",
            width=16,
            height=36,
            font=("Inter", 12),
            border_width=1,
            corner_radius=8
        ).grid(row=1, column=5, padx=(5, 15), pady=8, sticky='w')

        # Row 2
        self._create_label(form_inner, "Ngày bắt đầu", 2, 0)
        DateEntry(
            form_inner,
            textvariable=self.start_date_var,
            date_pattern="dd/mm/yyyy",
            width=16,
            height=36,
            font=("Inter", 12),
            border_width=1,
            corner_radius=8
        ).grid(row=2, column=1, padx=(5, 15), pady=8, sticky='w')

        self._create_label(form_inner, "Ngày kết thúc", 2, 2)
        DateEntry(
            form_inner,
            textvariable=self.end_date_var,
            date_pattern="dd/mm/yyyy",
            width=16,
            height=36,
            font=("Inter", 12),
            border_width=1,
            corner_radius=8
        ).grid(row=2, column=3, padx=(5, 15), pady=8, sticky='w')

        # Row 3
        self._create_label(form_inner, "Điện đầu (kWh)", 3, 0)
        entry_elec = self._create_entry(form_inner, 3, 1, self.elec_start_var, width=180)
        entry_elec.bind("<KeyRelease>", format_money)

        self._create_label(form_inner, "Nước đầu (m³)", 3, 2)
        entry_water = self._create_entry(form_inner, 3, 3, self.water_start_var, width=180)
        entry_water.bind("<KeyRelease>", format_money)

        # Row 4 - Ghi chú
        self._create_label(form_inner, "Ghi chú", 4, 0)
        ctk.CTkEntry(
            form_inner,
            textvariable=self.note_var,
            width=600,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        ).grid(row=4, column=1, columnspan=5, padx=(5, 15), pady=8, sticky='ew')

    def _create_label(self, parent, text, row, col):
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Inter", 13, "bold"),
            text_color=COLORS['text_dark']
        ).grid(row=row, column=col, padx=(10, 5), pady=8, sticky='w')

    def _create_entry(self, parent, row, col, variable, width=150, **kwargs):
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            width=width,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border'],
            **kwargs
        )
        entry.grid(row=row, column=col, padx=(5, 15), pady=8, sticky='w')
        return entry

    def _build_action_bar(self, parent):
        action_bar = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_white'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border']
        )
        action_bar.pack(fill='x', pady=(0, 15))

        inner = ctk.CTkFrame(action_bar, fg_color='transparent')
        inner.pack(fill='x', padx=25, pady=15)

        # Left - Search
        left = ctk.CTkFrame(inner, fg_color='transparent')
        left.pack(side='left', fill='x', expand=True)

        ctk.CTkLabel(left, text="Tìm kiếm:", font=("Inter", 13, "bold"), text_color=COLORS['text_dark']).pack(side='left', padx=(0, 10))
        search_entry = ctk.CTkEntry(
            left,
            textvariable=self.search_var,
            placeholder_text="Tìm theo phòng, khách thuê, ID...",
            width=380,
            height=36,
            font=("Inter", 13),
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        search_entry.pack(side='left')
        search_entry.bind("<KeyRelease>", lambda e: self._apply_search())

        # Right - Buttons
        right = ctk.CTkFrame(inner, fg_color='transparent')
        right.pack(side='right')

        self.btn_reset = ctk.CTkButton(
            right, text="Làm mới", width=100, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['secondary'],
            hover_color='#4b5563', corner_radius=8, command=self.reset_form
        )
        self.btn_reset.pack(side='left', padx=5)

        self.btn_add = ctk.CTkButton(
            right, text="➕ Tạo hợp đồng", width=140, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['success'],
            hover_color='#059669', corner_radius=8, command=self.on_create
        )
        self.btn_add.pack(side='left', padx=5)

        self.btn_update = ctk.CTkButton(
            right, text="✏️ Cập nhật", width=120, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['warning'],
            hover_color='#d97706', corner_radius=8, command=self.on_update
        )

        self.btn_end = ctk.CTkButton(
            right, text="Kết thúc HĐ", width=140, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['purple'],
            hover_color='#7c3aed', corner_radius=8, command=self.on_end_contract
        )

        self.btn_export = ctk.CTkButton(
            right, text="📄 Xuất PDF", width=120, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['info'],
            hover_color='#2563eb', corner_radius=8, command=self.on_export_pdf
        )

        self.btn_delete = ctk.CTkButton(
            right, text="🗑️ Xóa", width=100, height=36,
            font=("Inter", 13, "bold"), fg_color=COLORS['danger'],
            hover_color='#dc2626', corner_radius=8, command=self.on_delete
        )

        self._update_button_visibility()

    def _update_button_visibility(self):
        if self.is_edit_mode:
            self.btn_add.pack_forget()
            self.btn_update.pack(side='left', padx=5)
            self.btn_end.pack(side='left', padx=5)
            self.btn_export.pack(side='left', padx=5)
            self.btn_delete.pack(side='left', padx=5)
        else:
            self.btn_update.pack_forget()
            self.btn_end.pack_forget()
            self.btn_export.pack_forget()
            self.btn_delete.pack_forget()
            self.btn_add.pack(side='left', padx=5)

    def _build_table(self, parent):
        container = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_white'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['border']
        )
        container.pack(fill='both', expand=True)

        frame = ctk.CTkFrame(container, fg_color='transparent')
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        cols = ("id", "room", "tenant", "start", "end", "rent", "status")
        headers = {"id": "ID", "room": "Phòng", "tenant": "Khách thuê",
                   "start": "Bắt đầu", "end": "Kết thúc", "rent": "Giá thuê", "status": "Trạng thái"}
        widths = {"id": 60, "room": 90, "tenant": 180, "start": 110, "end": 110, "rent": 110, "status": 110}
        anchors = {"id": "center", "room": "center", "tenant": "w", "start": "center",
                   "end": "center", "rent": "e", "status": "center"}

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor=anchors[c])

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS['bg_white'], fieldbackground=COLORS['bg_white'],
                        foreground=COLORS['text_dark'], rowheight=36, font=("Inter", 12))
        style.configure("Treeview.Heading", background=COLORS['bg_light'],
                        foreground=COLORS['text_dark'], font=("Inter", 12, "bold"))
        style.map("Treeview", background=[('selected', COLORS['primary'])])

    # ==================== DATA & LOGIC (giữ nguyên như file cũ) ====================

    def _load_combobox_data(self):
        rooms = get_available_rooms()  # [(id, name, rent), ...]
        self.rooms_map = {r[1]: {"id": r[0], "rent": r[2]} for r in rooms}
        self.cb_room.configure(values=list(self.rooms_map.keys()))

        tenants = get_tenants_without_active_contract()  # [(id, name), ...]
        self.tenants_map = {t[1]: t[0] for t in tenants}
        self.cb_tenant.configure(values=list(self.tenants_map.keys()))

    def _load_contracts(self):
        self.contracts_cache = get_all_contracts()
        self._render_table(self.contracts_cache)

    def _render_table(self, contracts):
        self.tree.delete(*self.tree.get_children())
        for r in contracts:
            self.tree.insert("", "end", values=(
                r["contract_id"],
                r["room_name"],
                r["full_name"],
                r["start_ymd"],
                r["end_ymd"],
                format_currency(r["rent"]),
                r["contract_status"].capitalize() if r["contract_status"] else ""
            ))

    def _apply_search(self):
        kw = (self.search_var.get() or "").strip().lower()
        if not kw:
            self._render_table(self.contracts_cache)
            return

        filtered = [
            r for r in self.contracts_cache
            if kw in str(r["contract_id"]).lower()
            or kw in str(r["room_name"] or "").lower()
            or kw in str(r["full_name"] or "").lower()
        ]
        self._render_table(filtered)

    def _on_room_selected(self, choice):
        if choice in self.rooms_map:
            self.rent_var.set(format_currency(self.rooms_map[choice]["rent"]))

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.reset_form()
            return

        values = self.tree.item(sel[0], "values")
        self.current_contract_id = int(values[0])
        self.is_edit_mode = True
        self._update_button_visibility()

        contract = get_contract_by_id(self.current_contract_id)
        if contract:
            self.room_var.set(contract["room_name"])
            self.tenant_var.set(contract["full_name"])
            self.rent_var.set(format_currency(contract["rent"]))
            self.deposit_var.set(format_currency(contract["deposit_amount"]))
            self.deposit_date_var.set(contract["deposit_ymd"])
            self.start_date_var.set(contract["start_ymd"])
            self.end_date_var.set(contract["end_ymd"])
            self.elec_start_var.set(str(contract["electric_meter_start"]))
            self.water_start_var.set(str(contract["water_meter_start"]))
            self.note_var.set(contract["note"] or "")

            self.cb_room.configure(state="disabled")
            self.cb_tenant.configure(state="disabled")

    def reset_form(self):
        self.current_contract_id = None
        self.is_edit_mode = False
        self._update_button_visibility()

        self.room_var.set("")
        self.tenant_var.set("")
        self.rent_var.set("")
        self.deposit_var.set("")
        self.deposit_date_var.set(datetime.date.today().strftime("%d/%m/%Y"))
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.elec_start_var.set("0")
        self.water_start_var.set("0")
        self.note_var.set("")

        self.cb_room.configure(state="normal")
        self.cb_tenant.configure(state="normal")

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def _collect_data(self):
        if not self.room_var.get().strip() or not self.tenant_var.get().strip():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Phòng và Khách thuê!")
            return None

        try:
            rent = parse_currency(self.rent_var.get())
            deposit = parse_currency(self.deposit_var.get() or "0")
            elec = int(self.elec_start_var.get() or "0")
            water = int(self.water_start_var.get() or "0")
        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "Giá tiền, Điện, Nước phải là số!")
            return None

        room_name = self.room_var.get().strip()
        tenant_name = self.tenant_var.get().strip()

        room_id = self.rooms_map.get(room_name, {}).get("id")
        tenant_id = self.tenants_map.get(tenant_name)

        # Khi edit, nếu combobox bị disable thì giữ nguyên id cũ
        if self.is_edit_mode and room_id is None:
            old = get_contract_by_id(self.current_contract_id)
            room_id = old["room_id"]
        if self.is_edit_mode and tenant_id is None:
            old = get_contract_by_id(self.current_contract_id)
            tenant_id = old["tenant_id"]

        if room_id is None and not self.is_edit_mode:
            messagebox.showerror("Lỗi", "Phòng không hợp lệ (có thể đã có người ở).")
            return None

        return {
            "room_id": room_id,
            "tenant_id": tenant_id,
            "rent": rent,
            "deposit_amount": deposit,
            "deposit_ymd": self.deposit_date_var.get(),
            "start_ymd": self.start_date_var.get(),
            "end_ymd": self.end_date_var.get(),
            "electric_meter_start": elec,
            "water_meter_start": water,
            "note": self.note_var.get().strip() or None
        }

    # CRUD
    def on_create(self):
        data = self._collect_data()
        if not data: return
        try:
            create_contract(data)
            messagebox.showinfo("Thành công", "Tạo hợp đồng mới thành công!")
            self._load_combobox_data()
            self._load_contracts()
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", str(e))

    def on_update(self):
        if not self.current_contract_id:
            messagebox.showwarning("Chọn", "Vui lòng chọn hợp đồng cần sửa!")
            return
        data = self._collect_data()
        if not data: return
        try:
            update_contract(self.current_contract_id, data)
            messagebox.showinfo("Thành công", "Cập nhật hợp đồng thành công!")
            self._load_combobox_data()
            self._load_contracts()
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", str(e))

    def on_delete(self):
        if not self.current_contract_id: return
        if messagebox.askyesno("Xác nhận", "Xóa hợp đồng này? (Phòng sẽ trống)"):
            try:
                delete_contract(self.current_contract_id)
                messagebox.showinfo("Thành công", "Đã xóa hợp đồng!")
                self._load_combobox_data()
                self._load_contracts()
                self.reset_form()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

    def on_end_contract(self):
        if not self.current_contract_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hợp đồng để kết thúc!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn kết thúc hợp đồng này?"):
            try:
                end_contract(self.current_contract_id)
                messagebox.showinfo("Thành công", "Đã kết thúc hợp đồng!")
                self._load_combobox_data()
                self._load_contracts()
                self.reset_form()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

    def on_export_pdf(self):
        if not self.current_contract_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hợp đồng để xuất PDF!")
            return
        try:
            pdf_path = export_contract_to_pdf(self.current_contract_id)
            if pdf_path and os.path.exists(pdf_path):
                if os.name == 'nt':
                    os.startfile(pdf_path)
                elif os.name == 'posix':
                    if sys.platform == 'darwin':
                        subprocess.run(['open', pdf_path])
                    else:
                        subprocess.run(['xdg-open', pdf_path])
                messagebox.showinfo("Thành công", f"Xuất hợp đồng thành công:\n{pdf_path}")
            else:
                messagebox.showerror("Lỗi", "Không thể xuất hợp đồng!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xuất file PDF: {str(e)}")