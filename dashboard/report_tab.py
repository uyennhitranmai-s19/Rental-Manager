# ui/tabs/report_tab.py
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from module.report_service import (
    get_room_report,
    get_tenant_report,
    get_contract_report,
    get_bill_report,
)


class ReportTab(ctk.CTkFrame):
    def __init__(self, master, user_id=None):
        super().__init__(master, fg_color="#f8fafc")
        self.user_id = user_id
        self.chart_frames = []
        self._create_ui()
        self.refresh_data()

    def initialize(self):
        self.refresh_data()

    def refresh_data(self):
        for frame in self.chart_frames:
            frame.destroy()
        self.chart_frames.clear()
        self._create_charts()

    def _create_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(30, 40), padx=50)
        ctk.CTkLabel(
            header,
            text="BÁO CÁO & THỐNG KÊ",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#1e293b"
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Tổng quan hoạt động hệ thống",
            font=ctk.CTkFont(size=16),
            text_color="#64748b"
        ).pack(anchor="w", pady=(10, 0))

        self.charts_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_grid.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self.charts_grid.grid_rowconfigure((0, 1), weight=1)
        self.charts_grid.grid_columnconfigure((0, 1), weight=1)

    def _create_charts(self):
        room = get_room_report()
        tenant = get_tenant_report()  # <--- Định nghĩa biến tenant ở đây
        contract = get_contract_report()
        bill = get_bill_report()
        self._create_bar_room(self.charts_grid, 0, 0, room)
        self._create_bar_bill(self.charts_grid, 0, 1, bill)
        self._create_bar_tenant(self.charts_grid, 1, 0, tenant)  # Gọi đúng hàm bar ngang
        self._create_bar_contract(self.charts_grid, 1, 1, contract)

    def _create_chart_container(self, parent, row, col, title):
        container = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=20,
            border_width=1,
            border_color="#e2e8f0"
        )
        container.grid(row=row, column=col, padx=25, pady=30, sticky="nsew")

        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1e293b"
        )
        title_label.pack(pady=(20, 10))

        return container

    def _embed_chart(self, fig, frame):
        fig.tight_layout(pad=4.0)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _no_data_chart(self, ax, message="Chưa có dữ liệu"):
        ax.text(0.5, 0.5, message, transform=ax.transAxes, fontsize=18, color="#94a3b8", ha="center", va="center",
                weight="bold")
        ax.axis('off')

    def _create_bar_room(self, parent, row, col, data):
        container = self._create_chart_container(parent, row, col, "Tình trạng phòng trọ")
        chart_area = ctk.CTkFrame(container, fg_color="white")
        chart_area.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        labels = ["Đang thuê", "Trống", "Bảo trì"]
        values = [data["occupied"], data["available"], data["maintenance"]]
        colors = ["#3b82f6", "#10b981", "#f59e0b"]
        total = sum(values)
        if total == 0:
            self._no_data_chart(ax)
        else:
            bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=3)
            ax.set_ylim(0, max(values) * 1.4 if max(values) > 0 else 10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='#e2e8f0')
            for bar in bars:
                height = int(bar.get_height())
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, height + max(values) * 0.02, str(height), ha='center',
                            va='bottom', fontweight='bold', fontsize=20, color='#1e293b')
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=12)
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
        self._embed_chart(fig, chart_area)

    def _create_bar_bill(self, parent, row, col, data):
        container = self._create_chart_container(parent, row, col, "Tình trạng hóa đơn")
        chart_area = ctk.CTkFrame(container, fg_color="white")
        chart_area.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        paid = data["paid"]
        unpaid = data["unpaid"]
        total = paid + unpaid
        if total == 0:
            self._no_data_chart(ax)
        else:
            categories = ["Đã thanh toán", "Chưa thanh toán"]
            values = [paid, unpaid]
            colors = ["#16a34a", "#ef4444"]
            bars = ax.barh(categories, values, color=colors, height=0.6, edgecolor="white", linewidth=3)
            ax.set_xlim(0, max(values) * 1.4 if max(values) > 0 else 10)
            ax.invert_yaxis()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            for bar in bars:
                width = int(bar.get_width())
                if width > 0:
                    ax.text(width + max(values) * 0.02, bar.get_y() + bar.get_height() / 2, str(width), va='center',
                            fontweight='bold', fontsize=20, color='#1e293b')
            ax.tick_params(axis='y', labelsize=10)
            ax.tick_params(axis='x', labelsize=12)
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
        self._embed_chart(fig, chart_area)

    def _create_bar_tenant(self, parent, row, col, data):
        container = self._create_chart_container(parent, row, col, "Khách thuê")
        content_frame = ctk.CTkFrame(container, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 40))

        chart_frame = ctk.CTkFrame(content_frame, fg_color="white")
        chart_frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(8, 7), dpi=100)
        ax = fig.add_subplot(111)

        active = data["active"]
        new = data["new_this_month"]
        total = active + new

        if total == 0:
            self._no_data_chart(ax)
        else:
            categories = ["Đang ở", "Tháng này"]
            values = [active, new]
            colors = ["#10b981", "#8b5cf6"]
            bars = ax.barh(categories, values, color=colors, height=0.5, edgecolor="white", linewidth=3)
            ax.set_xlim(0, max(values) * 1.4 if max(values) > 0 else 10)
            ax.invert_yaxis()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            ax.grid(axis='x', linestyle='--', alpha=0.4)

            for bar in bars:
                width = int(bar.get_width())
                if width > 0:
                    ax.text(width + max(values) * 0.02, bar.get_y() + bar.get_height() / 2, str(width), va='center',
                            fontweight='bold', fontsize=16)
                    ax.tick_params(axis='y', labelsize=10)
                    ax.tick_params(axis='x', labelsize=12)
                    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
                    ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        if new > 0:
            note_text = f"Khách mới tháng này: {new} người"
            note_label = ctk.CTkLabel(
                content_frame,
                text=note_text,
                font=("Inter", 12),
                text_color="#8b5cf6",
                justify="left"
            )
            note_label.pack(pady=10, padx=20, anchor="w")

    def _create_bar_contract(self, parent, row, col, data):
        container = self._create_chart_container(parent, row, col, "Tình trạng hợp đồng")
        content_frame = ctk.CTkFrame(container, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        chart_frame = ctk.CTkFrame(content_frame, fg_color="white")
        chart_frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        new = data["new_this_month"]
        soon = data["soon_expire"]
        ended = data["ended"]
        total = new + soon + ended

        if total == 0:
            self._no_data_chart(ax)
        else:
            labels = ["Tháng này", "Sắp hết hạn", "Đã kết thúc"]
            values = [new, soon, ended]
            colors = ["#8b5cf6", "#f59e0b", "#94a3b8"]
            bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=3)
            ax.set_ylim(0, max(values) * 1.4 if max(values) > 0 else 10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='#e2e8f0')

            for bar in bars:
                height = int(bar.get_height())
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, height + max(values) * 0.02, str(height), ha='center',
                            va='bottom', fontweight='bold', fontsize=20, color='#1e293b')

            ax.tick_params(axis='x', labelsize=10, rotation=0)
            ax.tick_params(axis='y', labelsize=12)

            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
            fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.35)  # bottom=0.35 đủ cho label ngang
            fig.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)