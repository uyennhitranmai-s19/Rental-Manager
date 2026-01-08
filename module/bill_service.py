import os
import tempfile
from datetime import datetime
from pathlib import Path

from database.db import get_db
from utils.pdf_utils import create_bill_pdf, create_contract_pdf

def get_all_bills():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT b.*, r.room_name, t.full_name, c.rent as contract_rent, b.paid_status
            FROM bill b
            JOIN contract c ON b.contract_id = c.contract_id
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            WHERE b.is_deleted = 0
            ORDER BY b.bill_id DESC
            """
        ).fetchall()


def get_active_contracts_with_last_bill():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT 
                c.contract_id,
                r.room_id,
                r.room_name,
                t.full_name,
                c.rent,
                r.electric_unit_price,
                r.water_unit_price,
                c.electric_meter_start,
                c.water_meter_start,
                COALESCE(lb.elec_current, c.electric_meter_start, 0) as elec_prev,
                COALESCE(lb.water_current, c.water_meter_start, 0) as water_prev,
                lb.bill_month as last_bill_month
            FROM contract c
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            LEFT JOIN (
                SELECT contract_id, elec_current, water_current, bill_month,
                       ROW_NUMBER() OVER (PARTITION BY contract_id ORDER BY bill_month DESC) as rn
                FROM bill WHERE is_deleted = 0
            ) lb ON c.contract_id = lb.contract_id AND lb.rn = 1
            WHERE c.contract_status = 'active' AND c.is_deleted = 0
            ORDER BY r.room_name
            """
        ).fetchall()


def get_next_bill_month(contract_id: int) -> str:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT bill_month FROM bill 
            WHERE contract_id = ? AND is_deleted = 0
            ORDER BY bill_month DESC LIMIT 1
            """,
            (contract_id,),
        ).fetchone()

        if not row:
            today = datetime.today()
            return today.strftime("%m/%Y")

        last_month_str = row[0]
        month, year = map(int, last_month_str.split("/"))
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return f"{next_month:02d}/{next_year}"


def bill_exists(contract_id: int, bill_month: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM bill WHERE contract_id = ? AND bill_month = ? AND is_deleted = 0
            """,
            (contract_id, bill_month),
        ).fetchone()
        return row is not None


def create_bill(data: dict):
    with get_db() as conn:
        # Get contract details including tenant and room info
        contract_info = conn.execute(
            """
            SELECT 
                c.contract_id, c.room_id, c.tenant_id, c.start_ymd, c.end_ymd,
                t.full_name, r.room_name, r.electric_unit_price, r.water_unit_price
            FROM contract c
            JOIN tenant t ON c.tenant_id = t.tenant_id
            JOIN room r ON c.room_id = r.room_id
            WHERE c.contract_id = ? AND c.is_deleted = 0 AND c.contract_status = 'active'
            """,
            (data["contract_id"],)
        ).fetchone()

        if not contract_info:
            raise ValueError("Active contract not found or invalid")

        # Validate bill month format (MM/YYYY)
        try:
            bill_month = data["bill_month"]
            month, year = map(int, bill_month.split('/'))
            if not (1 <= month <= 12) or year < 2000 or year > 2100:
                raise ValueError("Invalid bill month format. Expected MM/YYYY")
        except (ValueError, AttributeError):
            raise ValueError("Invalid bill month format. Expected MM/YYYY")

        # Check if bill already exists for this contract and month
        if bill_exists(data["contract_id"], bill_month):
            raise ValueError(f"Bill already exists for contract {data['contract_id']} and month {bill_month}")

        # Calculate total amount
        total = (
            data["room_rent_amount"]
            + (data["elec_current"] - data["elec_prev"]) * data["electric_unit_price"]
            + (data["water_current"] - data["water_prev"]) * data["water_unit_price"]
            + data.get("other_fee", 0)
        )

        # Insert the bill with validated data
        conn.execute(
            """
            INSERT INTO bill (
                contract_id, tenant_name, room_id, room_name, bill_month,
                elec_prev, elec_current, water_prev, water_current,
                electric_unit_price, water_unit_price,
                room_rent_amount, other_fee, total_amount, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_info['contract_id'],
                contract_info['full_name'],  # Use tenant name from contract
                contract_info['room_id'],
                contract_info['room_name'],
                bill_month,
                data["elec_prev"],
                data["elec_current"],
                data["water_prev"],
                data["water_current"],
                data["electric_unit_price"],
                data["water_unit_price"],
                data["room_rent_amount"],
                data.get("other_fee", 0),
                total,
                data.get("note", ""),
            ),
        )
        conn.commit()


def update_bill(bill_id: int, data: dict):
    with get_db() as conn:
        # First, get the existing bill to ensure it exists and get contract_id
        existing_bill = conn.execute(
            """
            SELECT contract_id, bill_month, paid_status
            FROM bill
            WHERE bill_id = ?
              AND is_deleted = 0
            """,
            (bill_id,)
        ).fetchone()

        if not existing_bill:
            raise ValueError("Bill not found or has been deleted")

        # If bill is already paid, don't allow updates to amounts
        if existing_bill['paid_status'] == 'paid':
            raise ValueError("Cannot update a paid bill")

        # Validate bill month format (MM/YYYY)
        try:
            bill_month = data["bill_month"]
            month, year = map(int, bill_month.split('/'))
            if not (1 <= month <= 12) or year < 2000 or year > 2100:
                raise ValueError("Invalid bill month format. Expected MM/YYYY")

            # Check if another bill exists with the same contract and month
            if existing_bill['bill_month'] != bill_month:  # Only check if month changed
                conflict = conn.execute(
                    """
                    SELECT 1
                    FROM bill
                    WHERE contract_id = ?
                      AND bill_month = ?
                      AND bill_id != ? AND is_deleted = 0
                    """,
                    (existing_bill['contract_id'], bill_month, bill_id)
                ).fetchone()

                if conflict:
                    raise ValueError(
                        f"Another bill already exists for contract {existing_bill['contract_id']} and month {bill_month}")

        except (ValueError, AttributeError):
            raise ValueError("Invalid bill month format. Expected MM/YYYY")

        # Calculate total amount
        total = (
                data["room_rent_amount"]
                + (data["elec_current"] - data["elec_prev"]) * data["electric_unit_price"]
                + (data["water_current"] - data["water_prev"]) * data["water_unit_price"]
                + data.get("other_fee", 0)
        )

        # SỬA Ở ĐÂY: XÓA DÒNG updated_at = CURRENT_TIMESTAMP
        conn.execute(
            """
            UPDATE bill
            SET bill_month          = ?,
                elec_prev           = ?,
                elec_current        = ?,
                water_prev          = ?,
                water_current       = ?,
                electric_unit_price = ?,
                water_unit_price    = ?,
                room_rent_amount    = ?,
                other_fee           = ?,
                total_amount        = ?,
                note                = ?
            WHERE bill_id = ?
            """,
            (
                bill_month,
                data["elec_prev"],
                data["elec_current"],
                data["water_prev"],
                data["water_current"],
                data["electric_unit_price"],
                data["water_unit_price"],
                data["room_rent_amount"],
                data.get("other_fee", 0),
                total,
                data.get("note", ""),
                bill_id,
            ),
        )
        conn.commit()

def delete_bill(bill_id: int):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT is_deleted, paid_status
            FROM bill
            WHERE bill_id = ?
            """,
            (bill_id,)
        ).fetchone()

        if not row:
            raise ValueError("Hóa đơn không tồn tại")

        if row["is_deleted"] == 1:
            raise ValueError("Hóa đơn đã bị xóa")

        if row["paid_status"] == "unpaid":
            raise ValueError("Hóa đơn chưa được thanh toán, không thể xóa")

        conn.execute(
            "UPDATE bill SET is_deleted = 1 WHERE bill_id = ?",
            (bill_id,)
        )
        conn.commit()



def mark_bill_paid(bill_id: int):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE bill SET 
                paid_status = 'paid', 
                paid_amount = total_amount, 
                paid_ymd = date('now')
            WHERE bill_id = ?
            """,
            (bill_id,),
        )
        conn.commit()


def get_bill_by_id(bill_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 
                b.*, 
                r.room_name, 
                r.electric_unit_price,
                r.water_unit_price,
                t.full_name as tenant_name,
                t.phone,
                t.id_number,
                t.address,
                c.rent as room_rent,
                c.contract_id
            FROM bill b
            JOIN contract c ON b.contract_id = c.contract_id
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            WHERE b.bill_id = ? AND b.is_deleted = 0
            """,
            (bill_id,)
        ).fetchone()

    if not row:
        return None

    bill_data = dict(row)

    # SỬA LỖI Ở ĐÂY: dùng đúng tên cột
    bill_data['bill_month'] = bill_data.get('bill_month', '')  # Không phải 'bill_date'

    # Các trường khác giữ nguyên
    bill_data['elec_total'] = (bill_data['elec_current'] - bill_data['elec_prev']) * bill_data['electric_unit_price']
    bill_data['water_total'] = (bill_data['water_current'] - bill_data['water_prev']) * bill_data['water_unit_price']
    bill_data['total_amount'] = bill_data.get('total_amount', 0) or (
        bill_data['room_rent'] + bill_data['elec_total'] + bill_data['water_total'] + (bill_data.get('other_fee') or 0)
    )

    return bill_data

def get_bill_for_export(bill_id: int) -> dict:
    """Get bill data for PDF export"""
    with get_db() as conn:
        bill = conn.execute(
            """
            SELECT b.*, r.room_name, t.full_name as tenant_name, t.phone, 
                   t.address, c.rent as room_rent_amount
            FROM bill b
            JOIN contract c ON b.contract_id = c.contract_id
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            WHERE b.bill_id = ? AND b.is_deleted = 0
            """,
            (bill_id,)
        ).fetchone()
        
        if not bill:
            raise ValueError("Bill not found or has been deleted")
            
        # Convert to dict for easier access
        bill_dict = dict(bill)
        
        # Add additional fields if needed
        bill_dict['bill_code'] = f"HD{bill_id:06d}"
        bill_dict['created_date'] = datetime.now().strftime("%d/%m/%Y")
        
        return bill_dict

# Ensure the export directory exists when the module is imported
BASE_DIR = Path(__file__).resolve().parent.parent  # root project
PDF_EXPORT_DIR = BASE_DIR / "exports" / "bill"
PDF_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_bill_to_pdf(bill_id: int, output_dir: str = None) -> str:

    bill_data = get_bill_for_export(bill_id)

    output_dir = Path(output_dir) if output_dir else PDF_EXPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"HoaDon_{bill_data['bill_code']}_{bill_data['bill_month'].replace('/', '-')}.pdf"
    output_path = output_dir / filename
    
    create_bill_pdf(bill_data, str(output_path))
    return str(output_path)
