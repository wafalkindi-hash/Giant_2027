# -*- coding: utf-8 -*-
"""portal/pages/setup.py — Setup Wizard إجباري."""
from __future__ import annotations

from nicegui import ui

from portal.auth import (
    complete_setup,
    requires_setup,
    validate_password_strength,
)


@ui.page("/setup")
def setup_page() -> None:
    """صفحة Setup Wizard — إجبارية قبل أي دخول."""
    if not requires_setup():
        ui.navigate.to("/login")
        return

    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap" rel="stylesheet">')
    ui.query("body").style("background: #020617; font-family: Amiri; direction: rtl;")

    with ui.column().classes("w-full min-h-screen items-center justify-center p-6"):
        with ui.card().classes("w-full max-w-md p-8 bg-slate-900 border border-slate-700"):
            ui.icon("shield").classes("text-6xl text-amber-400 mx-auto")
            ui.label("إعداد النظام — خطوة أمنية إجبارية").classes(
                "text-2xl font-bold text-slate-100 text-center mt-4"
            )
            ui.label(
                "قبل استخدام البوابة، يجب تعيين كلمة مرور قوية للمدير. "
                "لن تتمكن من الدخول قبل إتمام هذه الخطوة."
            ).classes("text-sm text-slate-400 text-center mt-2 mb-6")

            password = ui.input(
                "كلمة المرور الجديدة",
                password=True,
                password_toggle_button=True,
            ).classes("w-full").props("outlined dark")

            confirm = ui.input(
                "تأكيد كلمة المرور",
                password=True,
                password_toggle_button=True,
            ).classes("w-full").props("outlined dark")

            requirements = ui.column().classes("gap-1 mt-4 text-xs")
            with requirements:
                ui.label("• 12 حرفاً على الأقل").classes("text-slate-400")
                ui.label("• حرف كبير (A-Z) وحرف صغير (a-z)").classes("text-slate-400")
                ui.label("• رقم واحد على الأقل").classes("text-slate-400")
                ui.label("• رمز خاص (!@#$%^&*...)").classes("text-slate-400")

            feedback = ui.label("").classes("text-sm mt-4 text-center")

            def _on_submit() -> None:
                if password.value != confirm.value:
                    feedback.text = "❌ كلمتا المرور غير متطابقتين"
                    feedback.classes("text-red-400")
                    return

                ok_strength, msg = validate_password_strength(password.value or "")
                if not ok_strength:
                    feedback.text = f"❌ {msg}"
                    feedback.classes("text-red-400")
                    return

                ok, msg = complete_setup(password.value)
                feedback.text = msg
                feedback.classes("text-green-400" if ok else "text-red-400")

                if ok:
                    ui.notify("✅ تم إعداد النظام — جاري التحويل...", type="positive")
                    ui.timer(1.5, lambda: ui.navigate.to("/login"), once=True)

            ui.button("إتمام الإعداد", on_click=_on_submit) \
                .classes("w-full mt-6") \
                .props("color=primary size=lg")