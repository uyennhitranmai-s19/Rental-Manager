import customtkinter as ctk
from tkinter import messagebox
from views.dashboard_tab import DashboardView
from views.login_tab import loginTab

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rental Manager")
        self.current_user = None

        # Bắt đầu với màn hình login
        self.show_login()

    def show_login(self):
        # Xóa hết nội dung cũ
        for widget in self.winfo_children():
            widget.destroy()

        # Reset về trạng thái login: kích thước nhỏ, không resize, giữa màn hình
        self.reset_to_login_state()

        # Tạo lại login tab
        self.login_tab = loginTab(master=self)
        self.login_tab.pack(fill='both', expand=True, padx=20, pady=20)

        # Đưa cửa sổ lên trên cùng và focus
        self.lift()
        self.focus_force()

    def reset_to_login_state(self):
        self.resizable(False, False)
        self.state('normal')

        width, height = 480, 680
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

        self.withdraw()
        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

    def show_main_app(self):
        # Xóa login cũ
        for widget in self.winfo_children():
            widget.destroy()

        self.title("Rental Manager - Hệ thống quản lý nhà trọ")
        self.resizable(True, True)

        # Ẩn hoàn toàn
        self.withdraw()
        self.attributes('-alpha', 0.0)

        # Set maximized
        self.state('zoomed')

        # Tạo dashboard
        self.dashboard = DashboardView(self)
        self.dashboard.pack(fill="both", expand=True)

        # Force update
        self.update_idletasks()
        self.update()

        # Delay và hiện lại để tránh hiện tượng giật do load chưa xong
        self.after(100, self._finish_show_main)

    def _finish_show_main(self):
        self.attributes('-alpha', 1.0)
        self.deiconify()
        self.lift()
        self.focus_force()

    def deiconify_and_focus(self):
        self.deiconify()
        self.lift()
        self.focus_force()
    def on_login_success(self, user):
        self.current_user = user
        self.show_main_app()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
