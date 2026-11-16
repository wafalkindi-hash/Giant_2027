# -*- coding: utf-8 -*-
"""portal/pages/settings.py — الإعدادات + الترخيص."""
from __future__ import annotations

from nicegui import ui

from portal.auth import get_license_info
from portal.deps import get_dm
from portal.layout import page_wrapper


@ui.page("/settings")
def settings_page() -> None:
    dm = get_dm()
    license_info = get_license_info()

    with page_wrapper("⚙️ الإعدادات"):
        with ui.card().classes("portal-card w-full"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("verified_user").classes("text-xl text-blue-400")
                ui.label("🔐 الترخيص").classes("text-lg font-bold text-slate-100")

            lic_type = license_info.get("type", "premium")
            badge_color = "green" if lic_type == "premium" else "amber" if lic_type == "basic" else "red"

            with ui.row().classes("gap-2 flex-wrap mb-3"):
                ui.badge(f"النوع: {lic_type}", color=badge_color)
                ui.badge(f"HWID: {str(license_info.get('hwid', 'N/A'))[:16]}...", color="blue")
                ui.badge(f"الفترة المجانية حتى: {license_info.get('free_until', '2029-12-31')}", color="cyan")

            ui.separator()
            ui.label(license_info.get("message", "")).classes("text-sm text-slate-300 mt-2")

        with ui.card().classes("portal-card w-full"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("info").classes("text-xl text-cyan-400")
                ui.label("📊 معلومات النظام").classes("text-lg font-bold text-slate-100")

            with ui.column().classes("gap-2 text-sm"):
                with ui.row().classes("justify-between"):
                    ui.label("المدرسة").classes("text-slate-400")
                    ui.label(dm.school_name).classes("text-slate-200")
                with ui.row().classes("justify-between"):
                    ui.label("School ID").classes("text-slate-400")
                    ui.label(dm.school_id).classes("text-slate-200 font-mono text-xs")
                with ui.row().classes("justify-between"):
                    ui.label("الإصدار").classes("text-slate-400")
                    ui.label(f"v{dm.current_version}").classes("text-slate-200")
