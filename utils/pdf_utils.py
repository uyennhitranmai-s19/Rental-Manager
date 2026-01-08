# utils/pdf_utils.py
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

# ========================
# ĐĂNG KÝ FONT INTER TỪ assets/fonts
# ========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
INTER_REGULAR = os.path.join(FONT_DIR, "Inter.ttf")
INTER_BOLD = os.path.join(FONT_DIR, "Inter-Bold.ttf")

def register_inter_fonts():
    if os.path.exists(INTER_REGULAR):
        pdfmetrics.registerFont(TTFont("Inter", INTER_REGULAR))
    if os.path.exists(INTER_BOLD):
        pdfmetrics.registerFont(TTFont("Inter-Bold", INTER_BOLD))

register_inter_fonts()

# ========================
# STYLES
# ========================
styles = {}

styles['MainTitle'] = ParagraphStyle(
    name='MainTitle',
    fontName='Inter-Bold',
    fontSize=16,
    alignment=TA_CENTER,
    spaceAfter=12,
    textColor=colors.HexColor("#0f172a")
)

styles['Info'] = ParagraphStyle(
    name='Info',
    fontName='Inter',
    fontSize=9.5,
    spaceAfter=4
)

styles['SubTitle'] = ParagraphStyle(
    name='SubTitle',
    fontName='Inter-Bold',
    fontSize=11,
    spaceAfter=8,
    textColor=colors.HexColor("#0f172a")
)

styles['Normal'] = ParagraphStyle(
    name='Normal',
    fontName='Inter',
    fontSize=10,
    leading=14,
    spaceAfter=5
)

styles['Italic'] = ParagraphStyle(
    name='Italic',
    fontName='Inter',
    fontSize=10,
    fontStyle='italic',
    alignment=TA_CENTER
)

# Contract styles
styles['QuocHieu'] = ParagraphStyle(name='QuocHieu', fontName='Inter-Bold', fontSize=14, alignment=TA_CENTER, spaceAfter=6)
styles['KhauHieu'] = ParagraphStyle(name='KhauHieu', fontName='Inter', fontSize=12, alignment=TA_CENTER, spaceAfter=15)
styles['ContractTitle'] = ParagraphStyle(name='ContractTitle', fontName='Inter-Bold', fontSize=20, alignment=TA_CENTER, spaceAfter=15)
styles['ContractMeta'] = ParagraphStyle(name='ContractMeta', fontName='Inter', fontSize=12, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#334155"))
styles['ContractSubTitle'] = ParagraphStyle(name='ContractSubTitle', fontName='Inter-Bold', fontSize=13, spaceAfter=8)
styles['ContractNormal'] = ParagraphStyle(name='ContractNormal', fontName='Inter', fontSize=11.5, leading=18, spaceAfter=6)

def format_currency(amount):
    if not amount or amount == 0:
        return "0 VNĐ"
    return f"{int(amount):,}".replace(",", ".") + " VNĐ"

# ==============================
# BIÊN LAI THU TIỀN (HÓA ĐƠN)
# ==============================
def create_bill_pdf(bill_data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A5,
        topMargin=1.3*cm,
        bottomMargin=1.5*cm,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm
    )
    elements = []

    # Tiêu đề mới
    elements.append(Paragraph("BIÊN LAI THU TIỀN", styles['MainTitle']))

    # Thông tin biên lai
    elements.append(Paragraph(f"Mã biên lai: <b>{bill_data.get('bill_code', '')}</b>", styles['Info']))
    elements.append(Paragraph(f"Kỳ thanh toán: <b>{bill_data.get('bill_month', '')}</b>", styles['Info']))
    elements.append(Paragraph(f"Ngày lập: <b>{datetime.now().strftime('%d/%m/%Y')}</b>", styles['Info']))
    elements.append(Spacer(1, 10))

    # Thông tin khách
    elements.append(Paragraph("THÔNG TIN NGƯỜI THUÊ", styles['SubTitle']))
    elements.append(Paragraph(f"• Họ tên: {bill_data.get('tenant_name', '')}", styles['Normal']))
    elements.append(Paragraph(f"• Phòng: {bill_data.get('room_name', '')}", styles['Normal']))
    elements.append(Spacer(1, 10))

    # Chi tiết thanh toán - liệt kê rõ cũ/mới/giá/tổng
    elements.append(Paragraph("CHI TIẾT THANH TOÁN", styles['SubTitle']))

    # Tiền phòng
    elements.append(Paragraph(f"Tiền thuê phòng: {format_currency(bill_data.get('room_rent_amount', 0))}", styles['Normal']))

    # Điện chi tiết
    elec_prev = bill_data.get('elec_prev', 0)
    elec_curr = bill_data.get('elec_current', 0)
    elec_used = elec_curr - elec_prev
    elec_price = bill_data.get('electric_unit_price', 0)
    elec_total = elec_used * elec_price

    elements.append(Paragraph(f"Điện cũ: {elec_prev} kWh → mới: {elec_curr} kWh", styles['Normal']))
    elements.append(Paragraph(f"Tiêu thụ: {elec_used} kWh × đơn giá {format_currency(elec_price)}/kWh", styles['Normal']))
    elements.append(Paragraph(f"Thành tiền điện: {format_currency(elec_total)}", styles['Normal']))

    # Nước chi tiết
    water_prev = bill_data.get('water_prev', 0)
    water_curr = bill_data.get('water_current', 0)
    water_used = water_curr - water_prev
    water_price = bill_data.get('water_unit_price', 0)
    water_total = water_used * water_price

    elements.append(Paragraph(f"Nước cũ: {water_prev} m³ → mới: {water_curr} m³", styles['Normal']))
    elements.append(Paragraph(f"Tiêu thụ: {water_used} m³ × đơn giá {format_currency(water_price)}/m³", styles['Normal']))
    elements.append(Paragraph(f"Thành tiền nước: {format_currency(water_total)}", styles['Normal']))

    # Phụ phí
    other = bill_data.get('other_fee', 0)
    if other > 0:
        elements.append(Paragraph(f"Phí khác: {format_currency(other)}", styles['Normal']))

    # Tổng cộng
    total = bill_data.get('total_amount', 0)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"TỔNG CỘNG: {format_currency(total)}", ParagraphStyle(
        name='TotalFinal', fontName='Inter-Bold', fontSize=14, alignment=TA_RIGHT, textColor=colors.HexColor("#dc2626")
    )))

    # Ghi chú
    note = bill_data.get('note', '').strip()
    if note:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Ghi chú: {note}", styles['Normal']))

    elements.append(Spacer(1, 20))

    # Chữ ký - 2 bên trái phải
    # sig_data = [
    #     ["Người lập biên lai", "Người nộp tiền"],
    #     ["(Ký và ghi rõ họ tên)", "(Ký và ghi rõ họ tên)"]
    # ]
    # sig_table = Table(sig_data, colWidths=[doc.width*0.5, doc.width*0.5])
    # sig_table.setStyle(TableStyle([
    #     ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    #     ('FONTNAME', (0,0), (-1,-1), 'Inter'),
    #     ('FONTSIZE', (0,0), (-1,-1), 11),
    #     ('FONTNAME', (0,0), (-1,0), 'Inter-Bold'),
    #     ('ITALIC', (0,1), (-1,1), True),
    #     ('PADDING', (0,0), (-1,-1), 12),
    # ]))
    # elements.append(sig_table)
    elements.append(Paragraph(
        "<b>Phương thức thanh toán:</b> Tiền mặt hoặc chuyển khoản vào ngày 05 hàng tháng<br/><br/>"
        "<b>Ngân hàng:</b> Vietcombank<br/>"
        "<b>Chi nhánh:</b> Đường Kim Cương<br/>"
        "<b>STK:</b> 0000000001<br/>"
        "<b>Chủ TK:</b> NGUYỄN VĂN A",
        styles['Normal']
    ))

    doc.build(elements)
    return output_path

# ==============================
# HỢP ĐỒNG THUÊ PHÒNG (NGẮT TRANG TỪ ĐIỀU 1)
# ==============================
def create_contract_pdf(contract_data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.8*cm,
        bottomMargin=2.0*cm,
        leftMargin=2.2*cm,
        rightMargin=2.2*cm
    )
    elements = []

    # Quốc hiệu
    elements.append(Paragraph("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", styles['QuocHieu']))
    elements.append(Paragraph("Độc lập - Tự do - Hạnh phúc", styles['KhauHieu']))
    elements.append(Spacer(1, 16))

    # Tiêu đề
    elements.append(Paragraph("HỢP ĐỒNG THUÊ PHÒNG TRỌ", styles['ContractTitle']))
    elements.append(Paragraph(f"Số hợp đồng: <b>{contract_data.get('contract_id', '')}</b>", styles['ContractMeta']))
    elements.append(Paragraph(f"Ngày lập: <b>{datetime.now().strftime('%d/%m/%Y')}</b>", styles['ContractMeta']))
    elements.append(Spacer(1, 10))

    # Thông tin các bên (trang 1)
    elements.append(Paragraph("BÊN A (BÊN CHO THUÊ)", styles['ContractSubTitle']))
    elements.append(Paragraph("• Công ty/Tổ chức: <b>CÔNG TY QUẢN LÝ NHÀ TRỌ GR8</b>", styles['ContractNormal']))
    elements.append(Paragraph("• Đại diện: <b>Ông NGUYỄN VĂN A</b>", styles['ContractNormal']))
    elements.append(Paragraph("• Địa chỉ: 23 Đường ABC, Phường 5, Quận 1, TP.HCM", styles['ContractNormal']))
    elements.append(Paragraph("• Điện thoại: <b>0123 456 789</b>", styles['ContractNormal']))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("BÊN B (BÊN THUÊ)", styles['ContractSubTitle']))
    elements.append(Paragraph(f"• Họ và tên: <b>{contract_data.get('tenant_name', '')}</b>", styles['ContractNormal']))
    elements.append(Paragraph(f"• CMND/CCCD: <b>{contract_data.get('id_number', 'Chưa cung cấp')}</b>", styles['ContractNormal']))
    elements.append(Paragraph(f"• Điện thoại: <b>{contract_data.get('phone', 'Chưa cung cấp')}</b>", styles['ContractNormal']))
    elements.append(Paragraph(f"• Địa chỉ thường trú: <b>{contract_data.get('address', 'Chưa cung cấp')}</b>", styles['ContractNormal']))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("THÔNG TIN PHÒNG THUÊ", styles['ContractSubTitle']))
    room_info = [
        f"• Phòng số: <b>{contract_data.get('room_name', '')}</b>",
        f"• Giá thuê/tháng: <b>{format_currency(contract_data.get('rent', 0))}</b>",
        f"• Tiền cọc: <b>{format_currency(contract_data.get('deposit_amount', 0))}</b>",
        f"• Ngày nhận phòng: <b>{contract_data.get('start_ymd', '')}</b>",
        f"• Ngày kết thúc: <b>{contract_data.get('end_ymd', '')}</b>",
        f"• Điện ban đầu: <b>{contract_data.get('electric_meter_start', 0)}</b> kWh",
        f"• Nước ban đầu: <b>{contract_data.get('water_meter_start', 0)}</b> m³",
        f"• Ghi chú: {contract_data.get('note', 'Không có')}"
    ]
    for line in room_info:
        elements.append(Paragraph(line, styles['ContractNormal']))

    # NGẮT TRANG TRƯỚC ĐIỀU 1
    elements.append(PageBreak())

    # Các điều khoản (bắt đầu trang mới)
    terms = [
        ("ĐIỀU 1: QUYỀN VÀ NGHĨA VỤ BÊN A", [
            "• Giao phòng đúng hạn, sạch sẽ, đầy đủ tiện nghi.",
            "• Thu tiền thuê và cung cấp biên lai.",
            "• Sửa chữa lớn khi hư hỏng không do bên B gây ra."
        ]),
        ("ĐIỀU 2: QUYỀN VÀ NGHĨA VỤ BÊN B", [
            "• Thanh toán tiền thuê, điện nước đúng hạn (trước ngày 05 hàng tháng).",
            "• Giữ gìn tài sản, vệ sinh, không tự ý sửa chữa.",
            "• Tuân thủ nội quy: không ồn ào, không nuôi thú, không hút thuốc."
        ]),
        ("ĐIỀU 3: CHẤM DỨT HỢP ĐỒNG", [
            "• Báo trước 30 ngày nếu muốn kết thúc sớm.",
            "• Bên B kết thúc sớm: mất tiền cọc.",
            "• Bên A kết thúc sớm: hoàn lại cọc và bồi thường."
        ]),
        ("ĐIỀU 4: ĐIỀU KHOẢN CHUNG", [
            "• Hợp đồng có hiệu lực từ ngày ký.",
            "• Lập thành 02 bản có giá trị pháp lý ngang nhau, mỗi bên giữ 01 bản."
        ])
    ]

    for title, lines in terms:
        elements.append(Paragraph(title, styles['ContractSubTitle']))
        for line in lines:
            elements.append(Paragraph(line, styles['ContractNormal']))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 40))

    # Chữ ký 2 bên trái phải
    sig_data = [
        ["BÊN A (Chủ nhà)", "BÊN B (Người thuê)"],
        ["(Ký và ghi rõ họ tên)", "(Ký và ghi rõ họ tên)"],
        ["", ""],
        ["", ""],
        ["NGUYỄN VĂN A", contract_data.get('tenant_name', '')]
    ]
    sig_table = Table(sig_data, colWidths=[doc.width*0.5, doc.width*0.5])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Inter'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('FONTNAME', (0,0), (-1,0), 'Inter-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 10.5),
        ('FONTSIZE', (0,4), (-1,4), 12),
        ('ITALIC', (0,1), (-1,1), True),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    return output_path