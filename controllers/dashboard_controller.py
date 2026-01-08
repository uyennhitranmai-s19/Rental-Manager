# -*- coding: utf-8 -*-
"""
Dashboard Controller
Handles business logic for dashboard view
"""
from module.dashboard_service import get_dashboard_stats


class DashboardController:
    def __init__(self, view=None):
        self.view = view
        self.current_user_id = None

    def set_user(self, user_id):
        """Set current logged in user"""
        self.current_user_id = user_id

    def refresh_data(self):
        """Refresh dashboard data - load stats and update view"""
        if self.view:
            try:
                # Load data using service
                stats = get_dashboard_stats()

                # Update cards in view
                self.view.reload_room_card(
                    stats.get('occupied_rooms', 0),
                    stats.get('total_rooms', 0)
                )

                self.view.reload_tenant_card(
                    stats.get('total_tenants', 0)
                )

                self.view.reload_payment_card(
                    stats.get('paid_bills', 0),
                    stats.get('total_bills', 0)
                )

                # Load charts if available
                if hasattr(self.view, 'load_charts'):
                    self.view.load_charts()

            except Exception as e:
                print(f"Error refreshing dashboard: {e}")
                import traceback
                traceback.print_exc()