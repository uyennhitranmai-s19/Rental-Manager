# -*- coding: utf-8 -*-
from tkinter import messagebox
import customtkinter as ctk
from views.bill_tab import billTab
from views.contract_tab import contractTab
from views.room_tab import roomTab
from views.tenant_tab import tenantTab
from views.report_tab import ReportTab

# Import for charts
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Import services
from module.dashboard_service import get_dashboard_stats
from module.report_service import get_room_report, get_revenue_last_6_months


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, color: str):
        super().__init__(
            parent,
            corner_radius=16,
            fg_color="#ffffff",
            border_width=4,
            border_color=color
        )

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#64748b"
        ).pack(pady=(20, 8))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color=color
        )
        self.value_label.pack(pady=(0, 25))

    def update_value(self, new_value):
        self.value_label.configure(text=str(new_value))


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, login_window=None):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.controller = controller
        self.active_button = None
        self.tabs = {}
        self.nav_buttons = []
        self.login_window = login_window
        self.chart_frames = []

        self.setup_ui()

        if self.controller:
            self.controller.view = self

    def setup_ui(self):
        self.setup_sidebar()
        self.setup_content()
        self.show_dashboard()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=("#f8fafc", "#1e1e1e"),
            border_width=1,
            border_color=("#e2e8f0", "#333333")
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        sidebar_content = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_content.pack(fill="both", expand=True, padx=15, pady=20)

        ctk.CTkLabel(
            sidebar_content,
            text="Quản Lý Thuê Phòng",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1e293b", "#f1f5f9")
        ).pack(pady=(0, 30))

        nav_frame = ctk.CTkFrame(sidebar_content, fg_color="transparent")
        nav_frame.pack(fill="x")

        self.nav_buttons = [
            ("Trang Chủ", self.show_dashboard),
            ("Phòng", self.show_room),
            ("Khách Thuê", self.show_tenant),
            ("Hợp Đồng", self.show_contract),
            ("Hóa Đơn", self.show_bill),
            ("Báo Cáo", self.show_report)
        ]

        for text, command in self.nav_buttons:
            btn = ctk.CTkButton(
                nav_frame,
                text=text,
                command=lambda t=text, c=command: self.on_nav_button_click(t, c),
                anchor="w",
                height=48,
                corner_radius=12,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                hover_color=("#e0e7ff", "#374151"),
                text_color=("#4b5563", "#d1d5db")
            )
            btn.pack(fill="x", pady=6)
            button_attr = text.lower().replace(" ", "_")
            setattr(self, f"{button_attr}_button", btn)

        if hasattr(self, 'trang_chủ_button'):
            self.set_active_button(self.trang_chủ_button)

        ctk.CTkButton(
            sidebar_content,
            text="Đăng Xuất",
            command=self.log_out,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="white"
        ).pack(side="bottom", fill="x", pady=(30, 0))

    def setup_content(self):
        self.content = ctk.CTkFrame(self, fg_color="#f8fafc")
        self.content.pack(side="right", fill="both", expand=True)

        self.dashboard_frame = ctk.CTkScrollableFrame(self.content, fg_color="#f8fafc")
        self.dashboard_frame.pack(fill="both", expand=True)

        main_container = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)

        # Header
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 30))

        ctk.CTkLabel(
            header,
            text="Chào mừng quay trở lại!",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#1e293b"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Tổng quan hệ thống hôm nay",
            font=ctk.CTkFont(size=16),
            text_color="#64748b"
        ).pack(anchor="w", pady=(8, 0))

        # Stats cards
        stats_grid = ctk.CTkFrame(main_container, fg_color="transparent")
        stats_grid.pack(fill="x", pady=(0, 40))
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)

        self.total_rooms_card = StatCard(stats_grid, "Tổng số phòng", "0", "#2563eb")
        self.total_rooms_card.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        self.occupied_rooms_card = StatCard(stats_grid, "Phòng đang thuê", "0", "#16a34a")
        self.occupied_rooms_card.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        self.total_tenants_card = StatCard(stats_grid, "Tổng khách thuê", "0", "#7c3aed")
        self.total_tenants_card.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")

        self.active_contracts_card = StatCard(stats_grid, "Hợp đồng hoạt động", "0", "#f59e0b")
        self.active_contracts_card.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        self.expiring_contracts_card = StatCard(stats_grid, "Sắp hết hạn", "0", "#dc2626")
        self.expiring_contracts_card.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")

        self.unpaid_bills_card = StatCard(stats_grid, "Hóa đơn chưa thu", "0", "#ef4444")
        self.unpaid_bills_card.grid(row=1, column=2, padx=15, pady=15, sticky="nsew")

        # Charts
        self.charts_container = ctk.CTkFrame(main_container, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True)
        self.charts_container.grid_columnconfigure((0, 1), weight=1)
        self.charts_container.grid_rowconfigure(0, weight=1)

    def refresh_dashboard(self):
        self.load_dashboard_data()
        self.load_charts()

    def load_dashboard_data(self):
        """LẤY ĐÚNG SỐ LIỆU CHO CÁC CARD"""
        try:
            stats = get_dashboard_stats()

            self.total_rooms_card.update_value(stats.get('total_rooms', 0))
            self.occupied_rooms_card.update_value(stats.get('occupied_rooms', 0))
            self.total_tenants_card.update_value(stats.get('total_tenants', 0))
            self.active_contracts_card.update_value(stats.get('active_contracts', 0))
            self.expiring_contracts_card.update_value(stats.get('expiring_contracts', 0))
            self.unpaid_bills_card.update_value(stats.get('unpaid_bills', 0))

        except Exception as e:
            print(f"[Dashboard] Lỗi load data: {e}")
            # Giữ giá trị 0 nếu lỗi

    def load_charts(self):
        for frame in self.chart_frames:
            frame.destroy()
        self.chart_frames.clear()

        try:
            room_data = get_room_report()
            revenue_data = get_revenue_last_6_months()

            # ĐÃ ĐỔI THÀNH BAR CHART CHO PHÒNG
            self._create_bar_room_chart(self.charts_container, 0, 0, room_data)
            self._create_revenue_line_chart(self.charts_container, 0, 1, revenue_data)
        except Exception as e:
            print(f"[Dashboard] Lỗi load chart: {e}")

    # === BIỂU ĐỒ PHÒNG
    def _create_bar_room_chart(self, parent, row, col, data):
        container = ctk.CTkFrame(parent, fg_color="white", corner_radius=20, border_width=1, border_color="#e2e8f0")
        container.grid(row=row, column=col, padx=25, pady=25, sticky="nsew")

        title = ctk.CTkLabel(container, text="Tình trạng phòng trọ", font=ctk.CTkFont(size=20, weight="bold"),
                             text_color="#1e293b")
        title.pack(pady=(30, 20))

        chart_frame = ctk.CTkFrame(container, fg_color="white")
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        labels = ["Đang thuê", "Trống", "Bảo trì"]
        values = [data["occupied"], data["available"], data["maintenance"]]
        colors = ["#3b82f6", "#10b981", "#f59e0b"]

        if sum(values) == 0:
            ax.text(0.5, 0.5, "Chưa có dữ liệu phòng", transform=ax.transAxes, fontsize=18, color="#94a3b8",
                    ha="center", va="center", weight="bold")
            ax.axis('off')
        else:
            bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=3)
            ax.set_ylim(0, 10)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='#e2e8f0')
            for bar in bars:
                height = int(bar.get_height())
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.2,
                        str(height),
                        ha='center', va='bottom',
                        fontweight='bold', fontsize=20, color='#1e293b'
                    )

            ax.tick_params(axis='x', labelsize=14)
            ax.tick_params(axis='y', labelsize=12)

            ax.yaxis.set_major_locator(plt.MultipleLocator(1))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%d'))

        self._embed_chart(fig, chart_frame)
        self.chart_frames.append(container)

    # === BIỂU ĐỒ DOANH THU ===
    def _create_revenue_line_chart(self, parent, row, col, data):
        container = ctk.CTkFrame(parent, fg_color="white", corner_radius=20, border_width=1, border_color="#e2e8f0")
        container.grid(row=row, column=col, padx=25, pady=25, sticky="nsew")

        title = ctk.CTkLabel(container, text="Doanh thu 6 tháng gần nhất", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1e293b")
        title.pack(pady=(30, 20))

        chart_frame = ctk.CTkFrame(container, fg_color="white")
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        months = [item['month'] for item in data]
        revenues = [item['revenue'] for item in data]

        if sum(revenues) == 0:
            ax.text(0.5, 0.5, "Chưa có doanh thu", transform=ax.transAxes,
                    fontsize=18, color="#94a3b8", ha="center", va="center", weight="bold")
            ax.axis('off')
        else:
            ax.plot(months, revenues, color="#10b981", linewidth=4, marker='o', markersize=12,
                    markerfacecolor="#10b981", markeredgecolor="white", markeredgewidth=3)
            ax.fill_between(months, revenues, alpha=0.15, color="#10b981")

            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e6:.1f}tr' if x >= 1e6 else f'{x/1e3:.0f}k'))

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            ax.grid(True, axis='y', linestyle='--', alpha=0.4, color='#e2e8f0')

            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
            ax.tick_params(axis='both', colors='#64748b', labelsize=12)

        self._embed_chart(fig, chart_frame)
        self.chart_frames.append(container)

    def _embed_chart(self, fig, frame):
        fig.tight_layout(pad=4.0)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # === Các hàm tab ===
    def lazy_load_tab(self, name, cls, user_id=None):
        if name not in self.tabs:
            if name == "report":
                self.tabs[name] = cls(self.content, user_id)
            else:
                self.tabs[name] = cls(self.content)
        return self.tabs[name]

    def hide_all(self):
        self.dashboard_frame.pack_forget()
        for tab in self.tabs.values():
            tab.pack_forget()

    def on_nav_button_click(self, button_text, command):
        button_attr = button_text.lower().replace(" ", "_")
        button = getattr(self, f"{button_attr}_button")
        self.set_active_button(button)
        command()

    def set_active_button(self, active_btn):
        for text, _ in self.nav_buttons:
            btn = getattr(self, f"{text.lower().replace(' ', '_')}_button")
            btn.configure(fg_color="transparent", text_color=("#4b5563", "#d1d5db"))
        active_btn.configure(fg_color=("#dbeafe", "#374151"), text_color=("#1e40af", "#93c5fd"))

    def show_dashboard(self):
        self.hide_all()
        self.dashboard_frame.pack(fill="both", expand=True)
        self.refresh_dashboard()

    def show_room(self):
        self.hide_all()
        tab = self.lazy_load_tab("room", roomTab)
        if hasattr(tab, 'initialize'):
            tab.initialize()
        tab.pack(fill="both", expand=True, padx=20, pady=20)

    def show_tenant(self):
        self.hide_all()
        tab = self.lazy_load_tab("tenant", tenantTab)
        if hasattr(tab, 'initialize'):
            tab.initialize()
        tab.pack(fill="both", expand=True, padx=20, pady=20)

    def show_bill(self):
        self.hide_all()
        tab = self.lazy_load_tab("bill", billTab)
        if hasattr(tab, 'initialize'):
            tab.initialize()
        tab.pack(fill="both", expand=True, padx=20, pady=20)
        tab.on_clear_form()

    def show_report(self):
        self.hide_all()
        user_id = getattr(self.controller, 'current_user_id', None) if self.controller else None
        tab = self.lazy_load_tab("report", ReportTab, user_id=user_id)
        if hasattr(tab, 'initialize'):
            tab.initialize()
        tab.pack(fill="both", expand=True, padx=20, pady=20)

    def show_contract(self):
        self.hide_all()
        tab = self.lazy_load_tab("contract", contractTab)
        if hasattr(tab, 'initialize'):
            tab.initialize()
        tab.pack(fill="both", expand=True, padx=20, pady=20)

    def log_out(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất không?", parent=self):
            # Gọi hàm show_login từ MainWindow (parent của dashboard)
            self.master.show_login()  # self.master chính là MainWindow