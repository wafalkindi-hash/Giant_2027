# -*- coding: utf-8 -*-
"""portal/pages/students.py — جدول الطلاب."""
from __future__ import annotations

import csv
import io

from nicegui import ui

from portal.deps import get_dm
from portal.layout import page_wrapper


def _export_csv(students: list) -> None:
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(["student_id", "name", "grade", "track", "section",
                     "parent_phone", "paid_fees", "remaining_fees", "behavior_points"])
    for s in students:
        writer.writerow([
            s.get("student_id", ""), s.get("name", ""),
            s.get("grade", ""), s.get("track", ""), s.get("section", ""),
            s.get("parent_phone", ""),
            s.get("paid_fees", 0), s.get("remaining_fees", 0),
            s.get("behavior_points", 100),
        ])
    ui.download(output.getvalue().encode("utf-8"), "students.csv")
    ui.notify("✅ تم تصدير CSV", type="positive")


@ui.page("/students")
def students_page() -> None:
    dm = get_dm()

    with page_wrapper("👥 شؤون الطلاب"):
        with ui.row().classes("w-full items-center gap-3"):
            search = ui.input(placeholder="🔍 ابحث بالاسم أو الرقم أو الهاتف...") \
                .classes("flex-1").props("outlined dark dense")
            ui.button("📥 تصدير CSV", on_click=lambda: _export_csv(_current_students)) \
                .props("color=green outline")

        container = ui.column().classes("w-full")
        _current_students: list = []

        def _render(keyword: str = "") -> None:
            nonlocal _current_students
            container.clear()
            if keyword:
                _current_students = dm.students.search(keyword)
            else:
                _current_students = dm.students.list_all(limit=200)

            with container:
                if not _current_students:
                    ui.label("📭 لا توجد نتائج").classes("text-slate-400 p-4")
                    return

                ui.label(f"عدد النتائج: {len(_current_students)}").classes("text-xs text-slate-500 mb-2")

                with ui.card().classes("portal-card w-full"):
                    with ui.element("table").classes("portal-table"):
                        with ui.element("thead"):
                            with ui.element("tr"):
                                for h in ["الرقم", "الاسم", "الصف", "الشعبة", "الهاتف", "المديونية", "السلوك"]:
                                    with ui.element("th"):
                                        ui.label(h)
                        with ui.element("tbody"):
                            for s in _current_students:
                                with ui.element("tr"):
                                    with ui.element("td"):
                                        ui.label(s.get("student_id", "")).classes("text-xs font-mono")
                                    with ui.element("td"):
                                        ui.label(s.get("name", ""))
                                    with ui.element("td"):
                                        ui.label(f"{s.get('grade', '')} {s.get('track', '')}")
                                    with ui.element("td"):
                                        ui.label(s.get("section", ""))
                                    with ui.element("td"):
                                        ui.label(s.get("parent_phone", "")).classes("text-xs font-mono")
                                    with ui.element("td"):
                                        fees = float(s.get("remaining_fees", 0) or 0)
                                        color = "text-green-400" if fees == 0 else "text-red-400"
                                        ui.label(f"{fees:,.0f}").classes(color)
                                    with ui.element("td"):
                                        points = int(s.get("behavior_points", 100) or 100)
                                        color = "text-green-400" if points >= 85 else "text-amber-400" if points >= 70 else "text-red-400"
                                        ui.label(str(points)).classes(color)

        _render()

        def _on_search() -> None:
            _render(search.value or "")

        search.on("keydown.enter", lambda _: _on_search())
        ui.button("بحث", on_click=_on_search).props("color=primary")
