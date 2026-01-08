from database.db import get_db
import re
from datetime import datetime

def get_all_tenant():
        conn = get_db()
        return conn.execute(
            """
        SELECT tenant_id, full_name, sex, phone, id_number,
               address, birth, note
        FROM tenant
        WHERE is_deleted = 0
        ORDER BY tenant_id DESC
    """
    ).fetchall()

def get_tennant_by_id(tennant_id: int):
        conn = get_db()
        return conn.execute("SELECT * FROM tennant WHERE tennant_id = ?", (tennant_id,)).fetchone()

PHONE_RE = re.compile(r'^\+?\d{7,15}$')

def validate_tenant(data: dict):
            # Required
            if not data.get("full_name") or not str(data["full_name"]).strip():
                raise ValueError("full_name là bắt buộc.")
            sex = data.get("sex")
            if sex is not None:
                try:
                    sex = int(sex)
                except (TypeError, ValueError):
                    raise ValueError("sex phải là số (0,1,2) hoặc None.")
                if sex not in (0, 1, 2):
                    raise ValueError("sex phải có giá trị 0, 1 hoặc 2.")
            return data

def create_tenant(data: dict):
    with get_db() as conn:
        conn.execute(
            """
        INSERT INTO tenant (full_name, sex, phone, id_number, address, birth, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
            (
                data["full_name"],
                data["sex"],
                data["phone"],
                data["id_number"],
                data["address"],
                data["birth"],
                data["note"],
            ),
        )
        conn.commit()

def update_tenant(tenant_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE tenant SET full_name=?, sex=?, phone=?, id_number=?,
                              address=?, birth=?, note=?
            WHERE tenant_id = ?
        """,
            (
                data["full_name"],
                data["sex"],
                data["phone"],
                data["id_number"],
                data["address"],
                data["birth"],
                data["note"],
                tenant_id,
            ),
        )
        conn.commit()


def delete_tenant(tenant_id: int):
    with get_db() as conn:
        active = conn.execute(
            """
        SELECT 1 FROM contract WHERE tenant_id = ? AND contract_status = 'active' AND is_deleted = 0
    """,
            (tenant_id,),
        ).fetchone()
        if active:
            raise ValueError("Không thể xóa khách đang có hợp đồng còn hiệu lực!")
        conn.execute("UPDATE tenant SET is_deleted = 1 WHERE tenant_id = ?", (tenant_id,))
        conn.commit()
