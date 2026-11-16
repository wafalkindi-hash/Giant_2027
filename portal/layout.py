# -*- coding: utf-8 -*-
"""
portal/layout.py
═══════════════════════════════════════════════════════════════════
عناصر التخطيط المشتركة بين الصفحات.
فُصلت من app.py لكسر الاستيراد الدائري.
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from typing import Optional

from nicegui import ui

from config.constants import APP_VERSION, Colors
from portal import __version__ as portal_version

logger = logging.getLogger(__name__)


def setup_theme() -> None:
    """RTL + ألوان + خط Amiri + Cairo."""
    ui.add_head_html("""
        <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Amiri', 'Cairo', sans-serif; direction: rtl; }
            .q-page { background: #020617; }
            .portal-card {
                background: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 14px;
                padding: 20px;
                transition: all 0.2s;
            }
            .portal-card:hover {
                border-color: #334155;
                background: #0B1220;
            }
            .kpi-value { font-size: 28px; font-weight: bold; color: #F1F5F9; }
            .kpi-label { font-size: 12px; color: #94A3B8; margin-top: 4px; }
            .kpi-green { color: #10B981; }
            .kpi-red { color: #EF4444; }
            .kpi-blue { color: #3B82F6; }
            .kpi-amber { color: #F59E0B; }
            .portal-table { width: 100%; border-collapse: collapse; }
            .portal-table th {
                background: #1E293B; color: #94A3B8;
                padding: 10px; text-align: right;
                font-size: 13px; font-weight: bold;
            }
            .portal-table td {
                padding: 10px; border-bottom: 1px solid #1E293B;
                font-size: 13px; color: #F1F5F9;
            }
            .portal-table tr:hover td { background: #0B1220; }
            .badge {
                display: inline-block; padding: 2px 8px;
                border-radius: 6px; font-size: 11px; font-weight: bold;
            }
            .badge-success { background: #065F46; color: #6EE7B7; }
            .badge-danger  { background: #7F1D1D; color: #FCA5A5; }
            .badge-warning { background: #78350F; color: #FCD34D; }
        </style>
    """)
    ui.colors(
        primary=Colors.PRIMARY,
        positive=Colors.SUCCESS,
        negative=Colors.DANGER,
        warning=Colors.WARNING,
        info=Colors.INFO,
    )


def build_header(user: Optional[dict]) -> None:
    """شريط التنقل العلوي."""
    if user is None:
        user = {}

    with ui.header().classes("bg-slate-900 border-b border-slate-700 items-center px-4"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-4"):
                ui.icon("school").classes("text-2xl text-blue-400")
                ui.label("العملاق الرقمي — البوابة الإدارية").classes("text-lg font-bold text-slate-100")
                ui.badge(f"v{APP_VERSION}", color="blue").classes("text-xs")
                ui.badge(f"Portal {portal_version}", color="cyan").classes("text-xs")

            with ui.row().classes("items-center gap-3"):
                # Navigation
                with ui.row().classes("items-center gap-1"):
                    _nav_button("dashboard", "🛰️", "القيادة")
                    _nav_button("students", "👥", "الطلاب")
                    _nav_button("grades", "📝", "الدرجات")
                    _nav_button("financial", "💰", "المالية")
                    _nav_button("settings", "⚙️", "الإعدادات")

                ui.separator().props("vertical")

                with ui.row().classes("items-center gap-2"):
                    ui.icon("person").classes("text-slate-400")
                    ui.label(user.get("name", "المدير")).classes("text-sm text-slate-300")
                    ui.badge(user.get("role", "مدير"), color="blue").classes("text-xs")

                ui.button(icon="logout", on_click=_do_logout) \
                    .props("flat round dense color=red") \
                    .tooltip("خروج")


def _nav_button(route: str, icon: str, label: str) -> None:
    """زر تنقل واحد."""
    ui.button(
        f"{icon} {label}",
        on_click=lambda: ui.navigate.to(f"/{route}"),
    ).props("flat dense color=white").classes("text-sm")


def _do_logout() -> None:
    """يُسجّل الخروج ويعود إلى /login."""
    from portal.auth import logout_user
    logout_user()
    ui.navigate.to("/login")


def page_wrapper(title: str):
    """
    Context manager: يُغلّف الصفحة بـ header + content.
    يتحقق من المصادقة أولاً.

    الاستخدام:
        with page_wrapper("عنوان"):
            ...
    """
    from contextlib import contextmanager
    from portal.auth import get_current_user

    @contextmanager
    def wrapper():
        user = get_current_user()
        if user is None:
            ui.navigate.to("/login")
            return
        setup_theme()
        build_header(user)
        with ui.column().classes("w-full p-6 gap-4 max-w-7xl mx-auto"):
            ui.label(title).classes("text-2xl font-bold text-slate-100 mb-2")
            yield

    return wrapper()


__all__ = [
    "setup_theme",
    "build_header",
    "page_wrapper",
]