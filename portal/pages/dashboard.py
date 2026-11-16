# -*- coding: utf-8 -*-
"""portal/pages/dashboard.py — لوحة القيادة."""
from __future__ import annotations

from nicegui import ui

from portal.deps import get_kpis, get_recent_activity, get_red_flags
from portal.layout import page_wrapper


def _kpi_card(icon: str, value: str, label: str, color: str) -> None:
    with ui.card().classes("portal-card flex-1 min-w-[180px]"):
        with ui.row().classes("items-center gap-3"):
            ui.icon(icon).classes(f"text-3xl {color}")
            with ui.column().classes("gap-0"):
                ui.label(value).classes(f"kpi-value {color}")
                ui.label(label).classes("kpi-label")


@ui.page("/dashboard")
def dashboard_page() -> None:
    kpis = get_kpis()
    att = kpis["today_attendance"]

    with page_wrapper("🛰️ قُمرة القيادة"):
        with ui.row().classes("w-full gap-3 flex-wrap"):
            _kpi_card("people", str(kpis["total_students"]), "إجمالي الطلاب", "text-blue-400")
            _kpi_card("check_circle", str(att["present"]), "حاضر اليوم", "text-green-400")
            _kpi_card("cancel", str(att["absent"]), "غائب اليوم", "text-red-400")
            _kpi_card("schedule", str(att["late"]), "متأخر اليوم", "text-amber-400")

        with ui.row().classes("w-full gap-3 flex-wrap mt-2"):
            _kpi_card("account_balance", f"{kpis['total_debt']:,.0f}", "إجمالي المديونيات (ر.ي)", "text-red-400")
            _kpi_card("payments", f"{kpis['vault_net']:,.0f}", "صافي الخزينة (ر.ي)", "text-green-400")
            _kpi_card("trending_up", f"{kpis['academic_avg']:.1f}", "متوسط المعدل", "text-blue-400")
            _kpi_card("psychology", f"{kpis['behavior_avg']:.1f}", "متوسط السلوك", "text-purple-400")

        red_flags = get_red_flags(limit=10)
        with ui.card().classes("portal-card w-full mt-4"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("warning").classes("text-xl text-red-400")
                ui.label(f"🚩 الرادار التنبؤي ({len(red_flags)} حالة)").classes("text-lg font-bold text-slate-100")

            if not red_flags:
                ui.label("✅ لا توجد حالات حرجة حالياً").classes("text-sm text-slate-400")
            else:
                with ui.column().classes("w-full gap-2"):
                    for rf in red_flags:
                        with ui.row().classes("items-center justify-between w-full p-2 bg-slate-800 rounded"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("person").classes("text-slate-400")
                                ui.label(rf.get("name", "?")).classes("text-sm text-slate-200")
                                ui.label(f"({rf.get('grade', '')})").classes("text-xs text-slate-500")
                            with ui.row().classes("items-center gap-2"):
                                if rf.get("absence_count", 0) >= 3:
                                    ui.badge(f"غياب: {rf['absence_count']}", color="red").classes("text-xs")
                                if rf.get("behavior_points", 100) < 85:
                                    ui.badge(f"سلوك: {rf['behavior_points']}", color="amber").classes("text-xs")

        activity = get_recent_activity(limit=10)
        with ui.card().classes("portal-card w-full mt-4"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("history").classes("text-xl text-blue-400")
                ui.label("🕵️ آخر الأنشطة").classes("text-lg font-bold text-slate-100")

            if not activity:
                ui.label("📭 لا توجد أنشطة").classes("text-sm text-slate-400")
            else:
                for act in activity:
                    with ui.row().classes("items-center justify-between w-full p-2 border-b border-slate-800"):
                        with ui.column().classes("gap-0"):
                            ui.label(act.get("action", "")).classes("text-sm text-slate-200")
                            ui.label(act.get("details", "")[:80]).classes("text-xs text-slate-500")
                        ui.label(str(act.get("timestamp", ""))[:16]).classes("text-xs text-slate-500")
