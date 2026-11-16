# -*- coding: utf-8 -*-
"""portal/pages/grades.py — تقارير الدرجات."""
from __future__ import annotations

from nicegui import ui

from portal.deps import get_dm
from portal.layout import page_wrapper


@ui.page("/grades")
def grades_page() -> None:
    dm = get_dm()

    with page_wrapper("📝 منصة الدرجات"):
        grades_data = dm.grades_settings.list_all()
        grade_names = sorted(set(g["grade_name"] for g in grades_data))

        with ui.row().classes("w-full items-center gap-3 flex-wrap"):
            grade_select = ui.select(
                options=grade_names or ["—"],
                label="الصف",
                value=grade_names[0] if grade_names else None,
            ).classes("min-w-[180px]").props("outlined dark dense")

            track_select = ui.select(
                options=["—"],
                label="الفرع",
                value="—",
            ).classes("min-w-[140px]").props("outlined dark dense")

            subject_select = ui.select(
                options=["—"],
                label="المادة",
                value="—",
            ).classes("min-w-[180px]").props("outlined dark dense")

            year_input = ui.input("العام الدراسي", value="2026-2027") \
                .classes("min-w-[140px]").props("outlined dark dense")

        def _refresh_tracks() -> None:
            tracks = dm.grades_settings.tracks_for_grade(grade_select.value or "")
            track_select.options = tracks or ["—"]
            track_select.value = tracks[0] if tracks else "—"
            track_select.update()
            _refresh_subjects()

        def _refresh_subjects() -> None:
            grade = grade_select.value or ""
            track = track_select.value or ""
            if track == "—":
                track = ""
            subjects = dm.subjects.list_for_grade(grade, track)
            subject_names = [s["subject_name"] for s in subjects]
            subject_select.options = subject_names or ["—"]
            subject_select.value = subject_names[0] if subject_names else "—"
            subject_select.update()

        grade_select.on("update:model-value", lambda _: _refresh_tracks())
        track_select.on("update:model-value", lambda _: _refresh_subjects())

        if grade_select.value:
            _refresh_tracks()

        container = ui.column().classes("w-full mt-4")

        def _load_grades() -> None:
            container.clear()
            grade = grade_select.value or ""
            track = "" if track_select.value == "—" else (track_select.value or "")
            subject = subject_select.value or ""
            year = year_input.value or "2026-2027"

            if not grade or subject == "—":
                with container:
                    ui.label("⚠️ اختر الصف والمادة").classes("text-amber-400")
                return

            try:
                grid = dm.grades.get_grid(grade, track, None, subject, year)
                stats = dm.grades.get_class_stats(grade, track, None, subject, year)
            except Exception as exc:
                with container:
                    ui.label(f"❌ {exc}").classes("text-red-400")
                return

            with container:
                with ui.row().classes("gap-3 flex-wrap mb-3"):
                    ui.badge(f"الطلاب: {stats['total']}", color="blue")
                    ui.badge(f"ناجح: {stats['passed']}", color="green")
                    ui.badge(f"راسب: {stats['failed']}", color="red")
                    ui.badge(f"متوسط: {stats['avg']:.1f}/{stats['max_possible']:.0f}", color="amber")

                with ui.card().classes("portal-card w-full"):
                    with ui.element("table").classes("portal-table"):
                        with ui.element("thead"):
                            with ui.element("tr"):
                                for h in ["الاسم", "الفصل1", "الفصل2", "المعدل النهائي", "التقدير"]:
                                    with ui.element("th"):
                                        ui.label(h)
                        with ui.element("tbody"):
                            for r in grid:
                                with ui.element("tr"):
                                    with ui.element("td"):
                                        ui.label(r.get("name", ""))
                                    with ui.element("td"):
                                        ui.label(f"{float(r.get('term1_total', 0) or 0):.1f}")
                                    with ui.element("td"):
                                        ui.label(f"{float(r.get('term2_total', 0) or 0):.1f}")
                                    with ui.element("td"):
                                        final = float(r.get("final_average", 0) or 0)
                                        ui.label(f"{final:.1f}").classes("font-bold")
                                    with ui.element("td"):
                                        tier, color = dm.grades.compute_grade_tier(
                                            final, stats["max_possible"] * 2
                                        )
                                        ui.label(tier).classes("text-xs font-bold").style(f"color: {color}")

        ui.button("📊 عرض الدرجات", on_click=_load_grades) \
            .classes("mt-3").props("color=primary")
