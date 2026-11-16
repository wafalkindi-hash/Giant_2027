# -*- coding: utf-8 -*-
"""portal/pages/login.py — صفحة تسجيل الدخول."""
from __future__ import annotations

from nicegui import ui

from config.constants import APP_NAME_AR, APP_VERSION
from portal.auth import (
    check_rate_limit,
    get_current_user,
    login_user,
    requires_setup,
)


@ui.page("/login")
def login_page() -> None:
    """صفحة تسجيل الدخول."""
    # إذا كان مسجّلاً → dashboard
    if get_current_user() is not None:
        ui.navigate.to("/dashboard")
        return

    # إذا كان setup مطلوباً → setup
    if requires_setup():
        ui.navigate.to("/setup")
        return

    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap" rel="stylesheet">')
    ui.query("body").style("background: #020617; font-family: Amiri; direction: rtl;")

    with ui.column().classes("w-full min-h-screen items-center justify-center p-6"):
        with ui.card().classes("w-full max-w-md p-8 bg-slate-900 border border-slate-700"):
            with ui.row().classes("items-center justify-center gap-2 w-full"):
                ui.icon("school").classes("text-5xl text-blue-400")
            ui.label(APP_NAME_AR).classes("text-xl font-bold text-slate-100 text-center mt-3")
            ui.label("البوابة الإدارية").classes("text-sm text-slate-400 text-center")
            ui.label(f"v{APP_VERSION}").classes("text-xs text-slate-500 text-center mb-6")

            username = ui.input("اسم المستخدم") \
                .classes("w-full").props("outlined dark")
            password = ui.input(
                "كلمة المرور",
                password=True,
                password_toggle_button=True,
            ).classes("w-full").props("outlined dark")

            feedback = ui.label("").classes("text-sm text-center mt-2")

            def _on_login() -> None:
                allowed, remaining = check_rate_limit()
                if not allowed:
                    feedback.text = f"⏳ محاولات كثيرة — انتظر {remaining} ثانية"
                    feedback.classes("text-amber-400")
                    return

                ok, msg = login_user(username.value or "", password.value or "")
                feedback.text = msg
                feedback.classes("text-green-400" if ok else "text-red-400")

                if ok:
                    ui.notify("✅ مرحباً", type="positive")
                    ui.timer(1.0, lambda: ui.navigate.to("/dashboard"), once=True)

            ui.button("دخول", on_click=_on_login) \
                .classes("w-full mt-4") \
                .props("color=primary size=lg")

            password.on("keydown.enter", lambda _: _on_login())

            ui.label("🔒 الوصول مقتصر على الإدارة المصرّح لها").classes(
                "text-xs text-slate-500 text-center mt-6"
            )