from database.db import get_db

def get_all_rooms():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT
                r.room_id,
                r.room_name,
                r.floor,
                r.area_m2,
                r.base_rent,
                r.electric_unit_price,
                r.water_unit_price,
                r.status,
                r.note,
                COUNT(c.contract_id) as active_contracts
            FROM room r
            LEFT JOIN contract c ON r.room_id = c.room_id 
                AND c.contract_status = 'active' 
                AND c.is_deleted = 0
            WHERE r.is_deleted = 0
            GROUP BY r.room_id
            ORDER BY r.room_name
            """
        ).fetchall()

def get_room_by_id(room_id: int):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM room 
            WHERE room_id = ? AND is_deleted = 0
            """,
            (room_id,),
        ).fetchone()

# --- CREATE ---
def get_available_rooms():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM room 
            WHERE status = 0 AND is_deleted = 0
            ORDER BY room_name
            """
        ).fetchall()

def create_room(data: dict):
    with get_db() as conn:
        required_keys = (
            "room_name",
            "area_m2",
            "base_rent",
            "electric_unit_price",
            "water_unit_price",
        )
        if not all(key in data for key in required_keys):
            raise ValueError("Missing required fields")

        conn.execute(
            """
            INSERT INTO room (
                room_name, floor, area_m2, base_rent,
                electric_unit_price, water_unit_price, status, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["room_name"],
                data.get("floor", 1),
                data["area_m2"],
                data["base_rent"],
                data["electric_unit_price"],
                data["water_unit_price"],
                data.get("status", 0),  # Default to available
                data.get("note", ""),
            ),
        )
        conn.commit()

def update_room(room_id: int, data: dict):
    with get_db() as conn:
        required_keys = (
            "room_name",
            "area_m2",
            "base_rent",
            "electric_unit_price",
            "water_unit_price",
            "status",
        )
        if not all(key in data for key in required_keys):
            raise ValueError("Missing required fields")

        # Check if the room is being set to occupied
        if data["status"] == 1:  # 1 = occupied
            # Check if there's already an active contract for this room
            active_contract = conn.execute(
                """
                SELECT 1 FROM contract 
                WHERE room_id = ? AND contract_status = 'active' AND is_deleted = 0
                """,
                (room_id,),
            ).fetchone()
            
            if not active_contract:
                raise ValueError(
                    "Phòng chưa có hợp đồng. Vui lòng tạo hợp đồng cho phòng này."
                )
        else:
            active_contract = conn.execute(
                """
                SELECT 1 FROM contract 
                WHERE room_id = ? AND contract_status = 'active' AND is_deleted = 0
                """,
                (room_id,),
            ).fetchone()
            
            if active_contract:
                raise ValueError(
                    "Phòng đang có hợp đồng hiệu lực, không thể chuyển sang trạng thái trống.")

        conn.execute(
            """
            UPDATE room SET 
                room_name = ?,
                floor = ?,
                area_m2 = ?,
                base_rent = ?,
                electric_unit_price = ?,
                water_unit_price = ?,
                status = ?,
                note = ?
            WHERE room_id = ?
            """,
            (
                data["room_name"],
                data.get("floor", 1),
                data["area_m2"],
                data["base_rent"],
                data["electric_unit_price"],
                data["water_unit_price"],
                data["status"],
                data.get("note", ""),
                room_id,
            ),
        )
        conn.commit()

def delete_room(room_id: int):
    with get_db() as conn:
        room_exists = conn.execute(
            "SELECT 1 FROM room WHERE room_id = ? AND is_deleted = 0",
            (room_id,),
        ).fetchone()

        if not room_exists:
            raise ValueError("Phòng không tồn tại")

        active_contract = conn.execute(
            """
            SELECT 1 FROM contract 
            WHERE room_id = ? AND contract_status = 'active' AND is_deleted = 0
            """,
            (room_id,),
        ).fetchone()

        if active_contract:
            raise ValueError(
                "Phòng đang được dùng."
            )
        conn.execute(
            "UPDATE room SET is_deleted = 1 WHERE room_id = ?",
            (room_id,),
        )
        conn.commit()

