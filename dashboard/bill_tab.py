import customtkinter as ctk
from tkinter import messagebox, ttk
import time
import os
import sys
import subprocess
import webbrowser
from utils.format import format_currency

# ===== COLOR SCHEME =====
COLORS = {
    'primary': '#3b82f6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'secondary': '#6b7280',
    'info': '#22c55e',
    'purple': '#8b5cf6',
    'bg_light': '#f8fafc',
    'bg_white': '#ffffff',
    'border': '#e2e8f0',
    'text_dark': '#1e293b',
    'text_gray': '#64748b'
}


class billTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])

        # State
        self._selected_bill_id = None
        self._current_contract_id = None
        self.active_contracts_data = {}
        self.is_edit_mode = False

        self._init_vars()
        self._build_ui()
        self._load_data()
        self.on_clear_form()

        self.bind("<Visibility>", self._on_visibility_change)

    def _on_visibility_change(self, event):
        if self.winfo_ismapped():
            self.on_clear_form()

    def initialize(self):
        self._load_data()
        self.on_clear_form()

    def _normalize_month(self, month_str: str) -> str:
        if not month_str:
            raise ValueError("Vui lòng nhập kỳ thanh toán (MM/YYYY)")

        month_str = month_str.strip().replace('-', '/').replace('.', '/')
        parts = month_str.split('/')

        if len(parts) != 2:
            raise ValueError("Định dạng kỳ thanh toán không hợp lệ. Vui lòng nhập theo dạng MM/YYYY")

        try:
            month = int(parts[0])
            year = int(parts[1])
            if not (1 <= month <= 12):
                raise ValueError("Tháng phải từ 01 đến 12")
            if not (2000 <= year <= 2100):
                raise ValueError("Năm phải hợp lệ")
            return f"{month:02d}/{year}"
        except ValueError:
            raise ValueError("Định dạng kỳ thanh toán không hợp lệ. Vui lòng nhập MM/YYYY")

    def _init_vars(self):
        self.search_var = ctk.StringVar()
        self.contract_select_var = ctk.StringVar()

        self.tenant_name_var = ctk.StringVar()
        self.room_name_var = ctk.StringVar()
        self.bill_month_var = ctk.StringVar()
        self.note_var = ctk.StringVar()

        self.elec_prev_var = ctk.StringVar()
        self.elec_curr_var = ctk.StringVar()
        self.elec_price_var = ctk.StringVar()
        self.elec_total_var = ctk.StringVar()

        self.water_prev_var = ctk.StringVar()
        self.water_curr_var = ctk.StringVar()
        self.water_price_var = ctk.StringVar()
        self.water_total_var = ctk.StringVar()

        self.room_rent_var = ctk.StringVar()
        self.other_fee_var = ctk.StringVar(value="0")
        self.total_amount_var = ctk.StringVar(value="0")

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

        ctk.CTkLabel(header, text="QUẢN LÝ HÓA ĐƠN", font=("Inter", 28, "bold"), text_color=COLORS['text_dark']).pack(anchor='w')
        ctk.CTkLabel(header, text="Tạo, cập nhật và quản lý hóa đơn thanh toán", font=("Inter", 13), text_color=COLORS['text_gray']).pack(anchor='w', pady=(5, 0))

    def _build_form(self, parent):
        form_container = ctk.CTkFrame(parent, fg_color=COLORS['bg_white'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        form_container.pack(fill='x', pady=(0, 15))

        form_inner = ctk.CTkFrame(form_container, fg_color='transparent')
        form_inner.pack(fill='x', padx=25, pady=20)

        # Row 0
        self._create_label(form_inner, "Chọn hợp đồng/Phòng:", 0, 0)
        self.cb_contract = ttk.Combobox(form_inner, textvariable=self.contract_select_var, width=35, state="readonly", font=("Inter", 12))
        self.cb_contract.grid(row=0, column=1, columnspan=2, padx=(5, 10), pady=8, sticky='w')
        self.cb_contract.bind("<<ComboboxSelected>>", self.on_contract_select)

        self._create_label(form_inner, "Kỳ thanh toán:", 0, 3)
        self.entry_month = ctk.CTkEntry(form_inner, textvariable=self.bill_month_var, width=120, height=36, font=("Inter", 13), corner_radius=8, border_width=1, border_color=COLORS['border'], state="readonly", fg_color="#e5e7eb")
        self.entry_month.grid(row=0, column=4, padx=(5, 10), pady=8, sticky='w')

        self._create_label(form_inner, "Khách thuê:", 0, 5)
        self.entry_tenant = ctk.CTkEntry(form_inner, textvariable=self.tenant_name_var, state="readonly", fg_color="#e5e7eb", width=180, height=36, font=("Inter", 13))
        self.entry_tenant.grid(row=0, column=6, padx=(5, 10), pady=8, sticky='w')

        # Row 1
        self._create_label(form_inner, "Tiền phòng:", 1, 0)
        self.entry_rent = ctk.CTkEntry(form_inner, textvariable=self.room_rent_var, state="readonly", fg_color="#e5e7eb", width=150, height=36, font=("Inter", 13))
        self.entry_rent.grid(row=1, column=1, padx=(5, 10), pady=8, sticky='w')

        self._create_label(form_inner, "Phụ phí:", 1, 2)
        self.entry_other = self._create_entry(form_inner, 1, 3, self.other_fee_var, width=120)
        self.entry_other.bind("<KeyRelease>", lambda e: [self.on_money_input(e, self.other_fee_var), self.on_recalc(e)])

        self._create_label(form_inner, "Ghi chú:", 1, 4)
        self.entry_note = self._create_entry(form_inner, 1, 5, self.note_var, width=250)
        self.entry_note.grid(columnspan=2, sticky='ew')

        # Electricity section
        elec_frame = ctk.CTkFrame(form_inner, fg_color="#f0fdf4", corner_radius=10, border_width=1, border_color="#bbf7d0")
        elec_frame.grid(row=2, column=0, columnspan=7, pady=10, padx=5, sticky='ew')
        elec_inner = ctk.CTkFrame(elec_frame, fg_color='transparent')
        elec_inner.pack(fill='x', padx=15, pady=12)

        ctk.CTkLabel(elec_inner, text="⚡ ĐIỆN (kWh)", font=("Inter", 13, "bold"), text_color="#15803d").pack(side='left', padx=(0, 20))
        ctk.CTkLabel(elec_inner, text="Cũ:", font=("Inter", 12)).pack(side='left', padx=2)
        ctk.CTkEntry(elec_inner, textvariable=self.elec_prev_var, state="readonly", fg_color="#e5e7eb", width=70, height=32, font=("Inter", 12)).pack(side='left', padx=2)

        ctk.CTkLabel(elec_inner, text="Mới:", font=("Inter", 12)).pack(side='left', padx=(10, 2))
        entry_elec_curr = ctk.CTkEntry(elec_inner, textvariable=self.elec_curr_var, width=70, height=32, font=("Inter", 12))
        entry_elec_curr.pack(side='left', padx=2)
        entry_elec_curr.bind("<KeyRelease>", lambda e: [self.on_money_input(e, self.elec_curr_var), self.on_recalc(e)])

        ctk.CTkLabel(elec_inner, text="Giá:", font=("Inter", 12)).pack(side='left', padx=(10, 2))
        entry_elec_price = ctk.CTkEntry(elec_inner, textvariable=self.elec_price_var, width=80, height=32, font=("Inter", 12))
        entry_elec_price.pack(side='left', padx=2)
        entry_elec_price.bind("<KeyRelease>", lambda e: [self.on_money_input(e, self.elec_price_var), self.on_recalc(e)])

        ctk.CTkLabel(elec_inner, text="=", font=("Inter", 12, "bold")).pack(side='left', padx=5)
        ctk.CTkLabel(elec_inner, textvariable=self.elec_total_var, text_color="#dc2626", font=("Inter", 13, "bold")).pack(side='left', padx=5)

        # Water section
        water_frame = ctk.CTkFrame(form_inner, fg_color="#eff6ff", corner_radius=10, border_width=1, border_color="#bfdbfe")
        water_frame.grid(row=3, column=0, columnspan=7, pady=10, padx=5, sticky='ew')
        water_inner = ctk.CTkFrame(water_frame, fg_color='transparent')
        water_inner.pack(fill='x', padx=15, pady=12)

        ctk.CTkLabel(water_inner, text="💧 NƯỚC (m³)", font=("Inter", 13, "bold"), text_color="#1e40af").pack(side='left', padx=(0, 20))
        ctk.CTkLabel(water_inner, text="Cũ:", font=("Inter", 12)).pack(side='left', padx=2)
        ctk.CTkEntry(water_inner, textvariable=self.water_prev_var, state="readonly", fg_color="#e5e7eb", width=70, height=32, font=("Inter", 12)).pack(side='left', padx=2)

        ctk.CTkLabel(water_inner, text="Mới:", font=("Inter", 12)).pack(side='left', padx=(10, 2))
        entry_water_curr = ctk.CTkEntry(water_inner, textvariable=self.water_curr_var, width=70, height=32, font=("Inter", 12))
        entry_water_curr.pack(side='left', padx=2)
        entry_water_curr.bind("<KeyRelease>", lambda e: [self.on_money_input(e, self.water_curr_var), self.on_recalc(e)])

        ctk.CTkLabel(water_inner, text="Giá:", font=("Inter", 12)).pack(side='left', padx=(10, 2))
        entry_water_price = ctk.CTkEntry(water_inner, textvariable=self.water_price_var, width=80, height=32, font=("Inter", 12))
        entry_water_price.pack(side='left', padx=2)
        entry_water_price.bind("<KeyRelease>", lambda e: [self.on_money_input(e, self.water_price_var), self.on_recalc(e)])

        ctk.CTkLabel(water_inner, text="=", font=("Inter", 12, "bold")).pack(side='left', padx=5)
        ctk.CTkLabel(water_inner, textvariable=self.water_total_var, text_color="#dc2626", font=("Inter", 13, "bold")).pack(side='left', padx=5)

        # Total section
        total_frame = ctk.CTkFrame(form_inner, fg_color="#fef2f2", corner_radius=10, border_width=2, border_color="#fecaca")
        total_frame.grid(row=4, column=0, columnspan=7, pady=10, padx=5, sticky='ew')
        total_inner = ctk.CTkFrame(total_frame, fg_color='transparent')
        total_inner.pack(fill='x', padx=15, pady=15)
        ctk.CTkLabel(total_inner, text="💰 TỔNG CỘNG:", font=("Inter", 15, "bold"), text_color="#991b1b").pack(side='left', padx=(0, 20))
        ctk.CTkLabel(total_inner, textvariable=self.total_amount_var, font=("Inter", 20, "bold"), text_color="#dc2626").pack(side='left')

    def _create_label(self, parent, text, row, col):
        ctk.CTkLabel(parent, text=text, font=("Inter", 13, "bold"), text_color=COLORS['text_dark']).grid(row=row, column=col, padx=(10, 5), pady=8, sticky='w')

    def _create_entry(self, parent, row, col, variable, width=150):
        entry = ctk.CTkEntry(parent, textvariable=variable, width=width, height=36, font=("Inter", 13), corner_radius=8, border_width=1, border_color=COLORS['border'])
        entry.grid(row=row, column=col, padx=(5, 10), pady=8, sticky='w')
        return entry

    def on_money_input(self, event, var):
        """Format số khi nhập (thêm dấu chấm phân cách hàng nghìn)"""
        try:
            raw = var.get().replace(".", "").strip()
            if not raw:
                var.set("")
                return
            value = int(raw)
            formatted = f"{value:,}".replace(",", ".")
            entry = event.widget
            cursor_pos = entry.index("insert")
            var.set(formatted)
            entry.icursor(cursor_pos)
        except ValueError:
            pass

    def _suggest_next_bill_month(self):
        if not self._current_contract_id:
            self.bill_month_var.set("")
            return
        try:
            from module.bill_service import get_next_bill_month
            next_month = get_next_bill_month(self._current_contract_id)
            self.bill_month_var.set(next_month)
        except Exception:
            import datetime
            today = datetime.date.today()
            self.bill_month_var.set(today.strftime("%m/%Y"))

    def on_contract_select(self, event):
        selection = self.contract_select_var.get()
        if not selection or selection not in self.active_contracts_data:
            return

        data = self.active_contracts_data[selection]
        self._current_contract_id = data["contract_id"]

        self.tenant_name_var.set(data["tenant_name"])
        self.room_name_var.set(data["room_name"])
        self.room_rent_var.set(format_currency(data["room_rent_amount"]))
        self.elec_price_var.set(format_currency(data["elec_price"]))
        self.water_price_var.set(format_currency(data["water_price"]))
        self.elec_prev_var.set(str(data["elec_prev"]))
        self.water_prev_var.set(str(data["water_prev"]))
        self.elec_curr_var.set("")
        self.water_curr_var.set("")

        self._suggest_next_bill_month()
        self.on_recalc()

    def on_recalc(self, event=None):
        try:
            e_old = int(float((self.elec_prev_var.get() or "0").replace(".", "")))
            e_new =int( float((self.elec_curr_var.get() or "0").replace(".", "")))
            e_price = int(float((self.elec_price_var.get() or "0").replace(".", "")))

            w_old =int( float((self.water_prev_var.get() or "0").replace(".", "")))
            w_new = int(float((self.water_curr_var.get() or "0").replace(".", "")))
            w_price =int( float((self.water_price_var.get() or "0").replace(".", "")))

            rent =int( float((self.room_rent_var.get() or "0").replace(".", "")))
            other =int( float((self.other_fee_var.get() or "0").replace(".", "")))

            e_used = max(0, e_new - e_old)
            w_used = max(0, w_new - w_old)

            e_total = e_used * e_price
            w_total = w_used * w_price
            total = rent + e_total + w_total + other

            self.elec_total_var.set(format_currency(e_total))
            self.water_total_var.set(format_currency(w_total))
            self.total_amount_var.set(format_currency(total) + " VND")
        except:
            self.elec_total_var.set("0")
            self.water_total_var.set("0")
            self.total_amount_var.set("0 VND")

    def _build_action_bar(self, parent):
        action_bar = ctk.CTkFrame(parent, fg_color=COLORS['bg_white'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        action_bar.pack(fill='x', pady=(0, 15))

        action_inner = ctk.CTkFrame(action_bar, fg_color='transparent')
        action_inner.pack(fill='x', padx=25, pady=15)

        left_frame = ctk.CTkFrame(action_inner, fg_color='transparent')
        left_frame.pack(side='left', fill='x', expand=True)

        ctk.CTkLabel(left_frame, text="Tìm kiếm:", font=("Inter", 13, "bold"), text_color=COLORS['text_dark']).pack(side='left', padx=(0, 10))
        search_entry = ctk.CTkEntry(left_frame, textvariable=self.search_var, placeholder_text="Tìm theo mã HĐ, phòng, khách...", width=350, height=36, font=("Inter", 13), corner_radius=8, border_width=1, border_color=COLORS['border'])
        search_entry.pack(side='left')
        search_entry.bind("<KeyRelease>", lambda e: self.on_search())

        right_frame = ctk.CTkFrame(action_inner, fg_color='transparent')
        right_frame.pack(side='right')

        ctk.CTkButton(right_frame, text="Làm mới", width=100, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['secondary'], hover_color='#4b5563', corner_radius=8, command=self.on_clear_form).pack(side='left', padx=5)

        self.btn_create = ctk.CTkButton(right_frame, text="➕ Tạo HĐ", width=110, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['success'], hover_color='#059669', corner_radius=8, command=self.on_create_bill)
        self.btn_create.pack(side='left', padx=5)

        self.btn_update = ctk.CTkButton(right_frame, text="✏️ Cập nhật", width=120, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['warning'], hover_color='#d97706', corner_radius=8, command=self.on_update_bill)
        self.btn_delete = ctk.CTkButton(right_frame, text="🗑️ Xóa", width=100, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['danger'], hover_color='#dc2626', corner_radius=8, command=self.on_delete_bill)
        self.btn_pay = ctk.CTkButton(right_frame, text="💳 Thanh toán", width=130, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['info'], hover_color='#16a34a', corner_radius=8, command=self.on_mark_paid)
        self.btn_export = ctk.CTkButton(right_frame, text="📄 Xuất PDF", width=120, height=36, font=("Inter", 13, "bold"), fg_color=COLORS['primary'], hover_color='#2563eb', corner_radius=8, command=self._on_export_pdf)

        self._update_button_visibility()

    def _update_button_visibility(self):
        if self.is_edit_mode:
            self.btn_create.pack_forget()
            self.btn_update.pack(side='left', padx=5)
            self.btn_delete.pack(side='left', padx=5)
            self.btn_pay.pack(side='left', padx=5)
            self.btn_export.pack(side='left', padx=5)
        else:
            self.btn_update.pack_forget()
            self.btn_delete.pack_forget()
            self.btn_pay.pack_forget()
            self.btn_export.pack_forget()
            self.btn_create.pack(side='left', padx=5)

    def _build_table(self, parent):
        table_container = ctk.CTkFrame(parent, fg_color=COLORS['bg_white'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        table_container.pack(fill='both', expand=True)

        table_frame = ctk.CTkFrame(table_container, fg_color='transparent')
        table_frame.pack(fill='both', expand=True, padx=20, pady=20)

        cols = ("id", "code", "room", "tenant", "month", "total", "status", "note")
        headers = {"id": "ID", "code": "Mã hóa đơn", "room": "Phòng", "tenant": "Khách thuê", "month": "Kỳ thanh toán", "total": "Tổng tiền", "status": "Trạng thái", "note": "Ghi chú"}
        widths = {"id": 60, "code": 120, "room": 90, "tenant": 180, "month": 110, "total": 130, "status": 120, "note": 200}
        anchors = {"id": "center", "code": "center", "room": "center", "tenant": "w", "month": "center", "total": "e", "status": "center", "note": "w"}

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor=anchors[col])

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS['bg_white'], foreground=COLORS['text_dark'], fieldbackground=COLORS['bg_white'], font=("Inter", 12), rowheight=36)
        style.configure("Treeview.Heading", background=COLORS['bg_light'], foreground=COLORS['text_dark'], font=("Inter", 12, "bold"))
        style.map('Treeview', background=[('selected', COLORS['primary'])])

    def _load_data(self):
        self._load_active_contracts()
        self._load_table_data()

    def _load_active_contracts(self):
        from module.bill_service import get_active_contracts_with_last_bill
        contracts = get_active_contracts_with_last_bill()
        values = []
        self.active_contracts_data = {}

        for c in contracts:
            display_str = f"{c[2]} - {c[3]}"
            values.append(display_str)
            self.active_contracts_data[display_str] = {
                "contract_id": c[0],
                "room_id": c[1],
                "room_name": c[2],
                "tenant_name": c[3],
                "room_rent_amount": c[4],
                "elec_price": c[5],
                "water_price": c[6],
                "elec_prev": c[9],
                "water_prev": c[10]
            }
        self.cb_contract['values'] = values

    def _load_table_data(self):
        from module.bill_service import get_all_bills
        for item in self.tree.get_children():
            self.tree.delete(item)

        bills = get_all_bills()
        keyword = self.search_var.get().strip().lower()

        for row in bills:
            bill = dict(row)

            bill_id = bill['bill_id']
            bill_code = bill.get('bill_code') or f"HD{bill_id:06d}"
            room_name = bill['room_name']
            tenant_name = bill['tenant_name']
            bill_month = bill['bill_month']
            total = bill['total_amount']
            status = bill['paid_status']
            note = bill.get('note') or ""

            status_text = {'paid': 'Đã thanh toán', 'unpaid': 'Chưa thanh toán', 'cancelled': 'Đã hủy'}.get(status, status.capitalize())

            search_text = f"{bill_code} {room_name} {tenant_name} {bill_month} {note}".lower()
            if keyword and keyword not in search_text:
                continue

            self.tree.insert("", "end", values=(
                bill_id,
                bill_code,
                room_name,
                tenant_name,
                bill_month,
                format_currency(total),
                status_text,
                note
            ))

    def on_search(self):
        self._load_table_data()

    def on_select_row(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        item = self.tree.item(sel[0])
        val = item['values']
        self._selected_bill_id = val[0]
        self.is_edit_mode = True
        self._update_button_visibility()

        from module.bill_service import get_bill_by_id
        bill_data = get_bill_by_id(self._selected_bill_id)
        if not bill_data:
            messagebox.showwarning("Lỗi", "Không tìm thấy hóa đơn!", parent=self)
            return

        self.tenant_name_var.set(bill_data.get('tenant_name', ''))
        self.room_name_var.set(bill_data.get('room_name', ''))
        self.bill_month_var.set(bill_data.get('bill_month', ''))
        self.note_var.set(bill_data.get('note', ''))

        self.elec_prev_var.set(str(bill_data.get('elec_prev', 0)))
        self.elec_curr_var.set(str(bill_data.get('elec_current', 0)))
        self.elec_price_var.set(format_currency(bill_data.get('electric_unit_price', 0)))

        self.water_prev_var.set(str(bill_data.get('water_prev', 0)))
        self.water_curr_var.set(str(bill_data.get('water_current', 0)))
        self.water_price_var.set(format_currency(bill_data.get('water_unit_price', 0)))

        self.room_rent_var.set(format_currency(bill_data.get('room_rent_amount', 0)))
        self.other_fee_var.set(format_currency(bill_data.get('other_fee', 0)))

        self.on_recalc()

        self._current_contract_id = bill_data.get('contract_id')
        for display_str, data in self.active_contracts_data.items():
            if data['contract_id'] == self._current_contract_id:
                self.contract_select_var.set(display_str)
                break

    def on_clear_form(self):
        self._selected_bill_id = None
        self._current_contract_id = None
        self.is_edit_mode = False
        self._update_button_visibility()

        self.contract_select_var.set("")
        self.tenant_name_var.set("")
        self.room_name_var.set("")
        self.bill_month_var.set("")
        self.note_var.set("")

        self.elec_prev_var.set("0")
        self.elec_curr_var.set("")
        self.elec_price_var.set("0")
        self.elec_total_var.set("0")

        self.water_prev_var.set("0")
        self.water_curr_var.set("")
        self.water_price_var.set("0")
        self.water_total_var.set("0")

        self.room_rent_var.set("0")
        self.other_fee_var.set("0")
        self.total_amount_var.set("0")

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def on_create_bill(self):
        if not self._current_contract_id:
            messagebox.showwarning("Lỗi", "Vui lòng chọn hợp đồng!", parent=self)
            return

        try:
            month = self._normalize_month(self.bill_month_var.get().strip())
            from module.bill_service import bill_exists
            if bill_exists(self._current_contract_id, month):
                messagebox.showerror("Lỗi", f"Hóa đơn tháng {month} đã tồn tại!", parent=self)
                return

            e_prev = float((self.elec_prev_var.get() or "0").replace(".", ""))
            e_curr = float((self.elec_curr_var.get() or "0").replace(".", ""))
            w_prev = float((self.water_prev_var.get() or "0").replace(".", ""))
            w_curr = float((self.water_curr_var.get() or "0").replace(".", ""))

            if e_curr < e_prev or w_curr < w_prev:
                messagebox.showerror("Lỗi", "Chỉ số mới không được nhỏ hơn chỉ số cũ!", parent=self)
                return

            data = {
                "bill_id": f"B{self._current_contract_id}_{int(time.time())}",
                "contract_id": self._current_contract_id,
                "bill_month": month,
                "tenant_name": self.tenant_name_var.get(),
                "room_id": self.active_contracts_data[self.contract_select_var.get()]["room_id"],
                "room_name": self.room_name_var.get(),
                "elec_prev": e_prev,
                "elec_current": e_curr,
                "water_prev": w_prev,
                "water_current": w_curr,
                "electric_unit_price": float((self.elec_price_var.get() or "0").replace(".", "")),
                "water_unit_price": float((self.water_price_var.get() or "0").replace(".", "")),
                "room_rent_amount": float((self.room_rent_var.get() or "0").replace(".", "")),
                "other_fee": float((self.other_fee_var.get() or "0").replace(".", "")),
                "note": self.note_var.get()
            }

            from module.bill_service import create_bill
            create_bill(data)
            messagebox.showinfo("Thành công", "Đã tạo hóa đơn mới!", parent=self)
            self.on_clear_form()
            self._load_table_data()

        except ValueError as ve:
            messagebox.showerror("Lỗi nhập liệu", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", str(e), parent=self)

    def on_update_bill(self):
        if not self._selected_bill_id:
            messagebox.showwarning("Chọn", "Vui lòng chọn hóa đơn cần sửa!", parent=self)
            return

        try:
            month = self._normalize_month(self.bill_month_var.get().strip())

            data = {
                "bill_month": month,
                "elec_prev": float((self.elec_prev_var.get() or "0").replace(".", "")),
                "elec_current": float((self.elec_curr_var.get() or "0").replace(".", "")),
                "water_prev": float((self.water_prev_var.get() or "0").replace(".", "")),
                "water_current": float((self.water_curr_var.get() or "0").replace(".", "")),
                "electric_unit_price": float((self.elec_price_var.get() or "0").replace(".", "")),
                "water_unit_price": float((self.water_price_var.get() or "0").replace(".", "")),
                "room_rent_amount": float((self.room_rent_var.get() or "0").replace(".", "")),
                "other_fee": float((self.other_fee_var.get() or "0").replace(".", "")),
                "note": self.note_var.get()
            }

            from module.bill_service import update_bill
            update_bill(self._selected_bill_id, data)
            messagebox.showinfo("Thành công", "Cập nhật hóa đơn thành công!", parent=self)
            self.on_clear_form()
            self._load_table_data()

        except ValueError as ve:
            messagebox.showerror("Lỗi nhập liệu", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def on_delete_bill(self):
        if not self._selected_bill_id:
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa hóa đơn này?", parent=self):
            try:
                from module.bill_service import delete_bill
                delete_bill(self._selected_bill_id)
                self.on_clear_form()
                self._load_table_data()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=self)

    def on_mark_paid(self):
        if not self._selected_bill_id:
            messagebox.showwarning("Chọn", "Vui lòng chọn hóa đơn để thanh toán!", parent=self)
            return

        if messagebox.askyesno("Xác nhận", "Xác nhận khách đã thanh toán đủ?", parent=self):
            try:
                from module.bill_service import mark_bill_paid
                mark_bill_paid(self._selected_bill_id)
                messagebox.showinfo("Thành công", "Đã cập nhật trạng thái: Đã thanh toán!", parent=self)
                self._load_table_data()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=self)

    def _on_export_pdf(self):
        if not self._selected_bill_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hóa đơn cần xuất!", parent=self)
            return

        try:
            from module.bill_service import export_bill_to_pdf
            pdf_path = export_bill_to_pdf(self._selected_bill_id)

            if not pdf_path or not os.path.exists(pdf_path):
                messagebox.showerror("Lỗi", "Không tìm thấy file PDF sau khi xuất!", parent=self)
                return

            pdf_path = os.path.abspath(pdf_path)
            filename = os.path.basename(pdf_path)

            messagebox.showinfo("Thành công", f"Đã xuất hóa đơn:\n{filename}\nĐang mở preview...", parent=self)

            opened = False
            try:
                webbrowser.open(f"file://{pdf_path}")
                opened = True
            except:
                pass

            if not opened and os.name == 'nt':
                try:
                    os.startfile(pdf_path)
                    opened = True
                except:
                    pass

            if not opened and sys.platform == 'darwin':
                try:
                    subprocess.run(['open', pdf_path])
                    opened = True
                except:
                    pass

            if not opened and os.name == 'posix':
                try:
                    subprocess.run(['xdg-open', pdf_path])
                    opened = True
                except:
                    pass

            if not opened:
                messagebox.showwarning("Cảnh báo", f"Không mở được tự động. Vui lòng mở thủ công:\n{pdf_path}", parent=self)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xuất/mở hóa đơn:\n{str(e)}", parent=self)