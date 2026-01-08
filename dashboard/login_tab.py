# views/login_tab.py
import customtkinter as ctk
from tkinter import messagebox
from module.login_service import authenticate_user


class loginTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        self.configure(fg_color="#E8F0FE")
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=20,
            border_width=2,
            border_color="#e0e0e0",
        )
        container.pack(fill="both", expand=True, padx=40, pady=60)

        ctk.CTkLabel(
            container,
            text="Đăng nhập hệ thống",
            font=("Inter", 28, "bold"),
            text_color="#131313",
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            container,
            text="Nhập tên tài khoản và mật khẩu quản trị",
            font=("Inter", 14),
            text_color="#64748b",
        ).pack(pady=(0, 40))

        form = ctk.CTkFrame(container, fg_color="transparent")
        form.pack(padx=40, fill="x")

        ctk.CTkLabel(form, text="Tên tài khoản", font=("Inter", 14, "bold")).pack(anchor="w", pady=(0, 8))
        self.entry_loginId = ctk.CTkEntry(
            form,
            placeholder_text="Nhập tên tài khoản",
            height=50,
            corner_radius=12,
            font=("Inter", 16),
            fg_color="#f8fafc",
            border_width=2
        )
        self.entry_loginId.pack(fill="x", pady=(0, 20))
        self.entry_loginId.focus()

        ctk.CTkLabel(form, text="Mật khẩu", font=("Inter", 14, "bold")).pack(anchor="w", pady=(0, 8))
        self.entry_pass = ctk.CTkEntry(
            form,
            placeholder_text="Nhập mật khẩu",
            show="*",
            height=50,
            corner_radius=12,
            font=("Inter", 16),
            fg_color="#f8fafc",
            border_width=2
        )
        self.entry_pass.pack(fill="x", pady=(0, 50))

        ctk.CTkButton(
            form,
            text="Đăng nhập ngay",
            command=self.login,
            height=50,
            corner_radius=12,
            font=("Inter", 16, "bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        ).pack(fill="x")

        ctk.CTkLabel(
            container,
            text="Hệ thống quản lý nhà trọ © 2025 Nhóm 8",
            font=("Inter", 12),
            text_color="#64748b",
        ).pack(side="bottom", pady=30)

        # Enter để chuyển và đăng nhập
        self.entry_loginId.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self.login())

    def login(self):
        user = self.entry_loginId.get().strip()
        pwd = self.entry_pass.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ thông tin!", parent=self)
            return

        result = authenticate_user(user, pwd)
        if result:
            user_data = {
                'login_id': user,
                'user_name': result[0] if result else "Admin"
            }
            if hasattr(self.master, 'on_login_success'):
                self.master.on_login_success(user_data)
        else:
            messagebox.showerror("Đăng nhập thất bại", "Sai tên tài khoản hoặc mật khẩu!", parent=self)
            self.entry_pass.delete(0, "end")
            self.entry_loginId.focus()