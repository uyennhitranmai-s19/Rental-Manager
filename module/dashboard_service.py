# -*- coding: utf-8 -*-
from database.db import get_db
from datetime import datetime, timedelta


def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    Returns dict with:
    - total_rooms: total number of rooms
    - occupied_rooms: rooms with status = 1 (occupied)
    - available_rooms: rooms with status = 0 (available)
    - total_tenants: total active tenants
    - active_contracts: contracts with status 'active'
    - expiring_contracts: contracts expiring within 30 days
    - unpaid_bills: bills with status 'unpaid'
    - paid_bills: paid bills this month
    - total_bills: total bills this month
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Room statistics
            cursor.execute(
                """
                SELECT COUNT(*)                                    as total_rooms,
                       SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as occupied_rooms,
                       SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as available_rooms
                FROM room
                WHERE is_deleted = 0
                """
            )
            room_stats = dict(cursor.fetchone() or {})

            # 2. Tenant count - active tenants with active contracts
            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.tenant_id) as count
                FROM tenant t
                    JOIN contract c
                ON t.tenant_id = c.tenant_id
                WHERE c.contract_status = 'active'
                  AND c.is_deleted = 0
                  AND t.is_deleted = 0
                """
            )
            tenant_count = dict(cursor.fetchone() or {}).get('count', 0)

            # 3. Contract statistics
            cursor.execute(
                """
                SELECT COUNT(*) as active_contracts
                FROM contract
                WHERE contract_status = 'active'
                  AND is_deleted = 0
                """
            )
            active_contracts = dict(cursor.fetchone() or {}).get('active_contracts', 0)

            # Contracts expiring within 30 days
            cursor.execute(
                """
                SELECT COUNT(*) as expiring_contracts
                FROM contract
                WHERE contract_status = 'active'
                  AND end_ymd BETWEEN date ('now')
                  AND date ('now'
                    , '+30 days')
                  AND is_deleted = 0
                """
            )
            expiring_contracts = dict(cursor.fetchone() or {}).get('expiring_contracts', 0)

            # 4. Bill statistics
            # Unpaid bills (all time)
            cursor.execute(
                """
                SELECT COUNT(*) as unpaid_bills
                FROM bill
                WHERE paid_status = 'unpaid'
                  AND is_deleted = 0
                """
            )
            unpaid_bills = dict(cursor.fetchone() or {}).get('unpaid_bills', 0)

            # Bills for current month
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute(
                """
                SELECT SUM(CASE WHEN paid_status = 'paid' THEN 1 ELSE 0 END) as paid_bills,
                       COUNT(*)                                              as total_bills
                FROM bill
                WHERE bill_month = ?
                  AND is_deleted = 0
                """,
                (current_month,)
            )
            bill_stats = dict(cursor.fetchone() or {})

            # Build result
            result = {
                'total_rooms': int(room_stats.get('total_rooms', 0) or 0),
                'occupied_rooms': int(room_stats.get('occupied_rooms', 0) or 0),
                'available_rooms': int(room_stats.get('available_rooms', 0) or 0),
                'total_tenants': int(tenant_count),
                'active_contracts': int(active_contracts),
                'expiring_contracts': int(expiring_contracts),
                'unpaid_bills': int(unpaid_bills),
                'paid_bills': int(bill_stats.get('paid_bills', 0) or 0),
                'total_bills': int(bill_stats.get('total_bills', 0) or 0)
            }

            print(f"Dashboard stats: {result}")
            return result

    except Exception as e:
        print(f"[ERROR] in get_dashboard_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'total_rooms': 0,
            'occupied_rooms': 0,
            'available_rooms': 0,
            'total_tenants': 0,
            'active_contracts': 0,
            'expiring_contracts': 0,
            'unpaid_bills': 0,
            'paid_bills': 0,
            'total_bills': 0
        }