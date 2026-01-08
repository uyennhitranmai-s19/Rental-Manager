# module/contract_service.py
import os
import tempfile
from datetime import datetime
from pathlib import Path

from database.db import get_db
from utils.pdf_utils import create_contract_pdf


def get_all_contracts():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, r.room_name, t.full_name
            FROM contract c
            JOIN room r ON c.room_id = r.room_id AND r.is_deleted = 0
            JOIN tenant t ON c.tenant_id = t.tenant_id AND t.is_deleted = 0
            WHERE c.is_deleted = 0
            ORDER BY c.contract_id DESC
            """
        ).fetchall()


def get_active_contract_count():
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM contract WHERE contract_status = 'active' AND is_deleted = 0"
        ).fetchone()
        return row[0] if row else 0


def create_contract(data: dict):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO contract (
                room_id, tenant_id, start_ymd, end_ymd,
                rent, deposit_amount, electric_meter_start, water_meter_start,
                deposit_ymd, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["room_id"],
                data["tenant_id"],
                data["start_ymd"],
                data["end_ymd"],
                data["rent"],
                data["deposit_amount"],
                data["electric_meter_start"],
                data["water_meter_start"],
                data["deposit_ymd"],
                data.get("note", ""),
            ),
        )
        conn.execute(
            "UPDATE room SET status = 1 WHERE room_id = ?", (data["room_id"],)
        )
        conn.commit()


def update_contract(contract_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE contract SET
                room_id = ?,
                tenant_id = ?,
                start_ymd = ?,
                end_ymd = ?,
                rent = ?,
                deposit_amount = ?,
                electric_meter_start = ?,
                water_meter_start = ?,
                deposit_ymd = ?,
                note = ?
            WHERE contract_id = ?
            """,
            (
                data["room_id"],
                data["tenant_id"],
                data["start_ymd"],
                data["end_ymd"],
                data["rent"],
                data["deposit_amount"],
                data["electric_meter_start"],
                data["water_meter_start"],
                data["deposit_ymd"],
                data.get("note", ""),
                contract_id,
            ),
        )
        conn.commit()


def delete_contract(contract_id: int):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT contract_status, is_deleted, room_id
            FROM contract
            WHERE contract_id = ?
            """,
            (contract_id,)
        ).fetchone()

        if not row:
            raise ValueError("Hợp đồng không tồn tại")

        if row["is_deleted"] == 1:
            raise ValueError("Hợp đồng đã bị xóa")

        if row["contract_status"] == "active":
            raise ValueError("Hợp đồng đang hoạt động, không thể xóa")

        conn.execute(
            "UPDATE contract SET is_deleted = 1 WHERE contract_id = ?",
            (contract_id,)
        )
        conn.commit()

def end_contract(contract_id: int):
    with get_db() as conn:
        room_id = conn.execute(
            "SELECT room_id FROM contract WHERE contract_id = ?", (contract_id,)
        ).fetchone()

        if room_id:
            conn.execute(
                "UPDATE room SET status = 2 WHERE room_id = ?", (room_id[0],)
            )
        unpaid = conn.execute(
            """
            SELECT 1 FROM bill
            WHERE contract_id = ? AND paid_status = 'unpaid'
            """,
            (contract_id,)
        ).fetchone()

        if unpaid:
            raise ValueError("Hợp đồng có hóa đơn chưa thanh toán, không thể kết thúc")

        conn.execute(
            """
            UPDATE contract 
            SET contract_status = 'ended', 
                end_ymd = date('now')
            WHERE contract_id = ?
            """,
            (contract_id,),
        )
        conn.commit()


def get_contract_by_id(contract_id: int):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT c.*, r.room_name, t.full_name
            FROM contract c
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            WHERE c.contract_id = ? AND c.is_deleted = 0
            """,
            (contract_id,),
        ).fetchone()


def get_available_rooms():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT room_id, room_name, base_rent 
            FROM room 
            WHERE status = 0 AND is_deleted = 0 
            ORDER BY room_id
            """
        ).fetchall()


def get_tenants_without_active_contract():
    with get_db() as conn:
        return conn.execute(
            """
           SELECT t.tenant_id, t.full_name, t.phone
FROM tenant t
WHERE t.is_deleted = 0
AND NOT EXISTS (
    SELECT 1
    FROM contract c
    WHERE c.tenant_id = t.tenant_id
      AND c.contract_status = 'active'
      AND c.is_deleted = 0)
            """
        ).fetchall()


def get_contract_for_export(contract_id: int) -> dict:
    """Get contract data for PDF export"""
    with get_db() as conn:
        contract = conn.execute(
            """
            SELECT c.*, r.room_name, t.address,
                   t.full_name as tenant_name, t.phone, t.id_number
            FROM contract c
            JOIN room r ON c.room_id = r.room_id
            JOIN tenant t ON c.tenant_id = t.tenant_id
            WHERE c.contract_id = ? AND c.is_deleted = 0
            """,
            (contract_id,)
        ).fetchone()

        if not contract:
            raise ValueError("Contract not found or has been deleted")

        # Convert to dict for easier access
        contract_dict = dict(contract)

        # Add additional fields if needed
        contract_dict['contract_code'] = f"HD{contract_id:06d}"
        contract_dict['company_address'] = "Số 1, Đường ABC, Quận 1, TP.HCM"
        contract_dict['payment_due_day'] = "05"  # Default payment due day

        # Format dates
        if 'start_date' in contract_dict and contract_dict['start_date']:
            if isinstance(contract_dict['start_date'], str):
                # If it's already a string, try to parse and reformat
                try:
                    dt = datetime.strptime(contract_dict['start_date'], '%Y-%m-%d')
                    contract_dict['start_date'] = dt.strftime('%d/%m/%Y')
                except:
                    pass
            else:

                contract_dict['start_date'] = contract_dict['start_date'].strftime('%d/%m/%Y')

        if 'end_date' in contract_dict and contract_dict['end_date']:
            if isinstance(contract_dict['end_date'], str):
                try:
                    dt = datetime.strptime(contract_dict['end_date'], '%Y-%m-%d')
                    contract_dict['end_date'] = dt.strftime('%d/%m/%Y')
                except:
                    pass
            else:
                contract_dict['end_date'] = contract_dict['end_date'].strftime('%d/%m/%Y')

        return contract_dict


# Ensure the export directory exists when the module is imported
BASE_DIR = Path(__file__).resolve().parent.parent  # root project
PDF_EXPORT_DIR = BASE_DIR / "exports" / "contract"
PDF_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
def export_contract_to_pdf(contract_id: int, output_dir: str = None) -> str:
    contract_data = get_contract_for_export(contract_id)

    # Use PDF_EXPORT_DIR if output_dir is not provided
    output_dir = Path(output_dir) if output_dir else PDF_EXPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"HopDong_{contract_data['contract_code']}_{contract_data['tenant_name']}.pdf"
    output_path = output_dir / filename
    create_contract_pdf(contract_data, str(output_path))
    return str(output_path)