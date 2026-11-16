# -*- coding: utf-8 -*-
"""portal/pages/financial.py — المالية."""
from __future__ import annotations

import csv
import io

from nicegui import ui

from portal.deps import get_dm
from portal.layout import page_wrapper


def _export_csv(rows: list, filename: str) -> None:
    if not rows:
        ui.notify("لا توجد بيانات", type="warning")
        return
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    ui.download(output.getvalue().encode("utf-8"), filename)
    ui.notify("✅ تم التصدير", type="positive")


@ui.page("/financial")
def financial_page() -> None:
    dm = get_dm()
    summary = dm.financial.get_summary()

    with page_wrapper("💰 الخزينة المركزية"):
        with ui.row().classes("w-full gap-3 flex-wrap"):
            with ui.card().classes("portal-card flex-1 min-w-[200px]"):
                ui.label("إجمالي المدفوع").classes("kpi-label")
                ui.label(f"{summary['paid']:,.0f} ر.ي").classes("kpi-value text-green-400")
            with ui.card().classes("portal-card flex-1 min-w-[200px]"):
                ui.label("إجمالي المديونيات").classes("kpi-label")
                ui.label(f"{summary['debt']:,.0f} ر.ي").classes("kpi-value text-red-400")
            with ui.card().classes("portal-card flex-1 min-w-[200px]"):
                ui.label("إجمالي المصروفات").classes("kpi-label")
                ui.label(f"{summary['expenses']:,.0f} ر.ي").classes("kpi-value text-amber-400")
            with ui.card().classes("portal-card flex-1 min-w-[200px]"):
                ui.label("صافي الخزينة").classes("kpi-label")
                net = summary["net"]
                ui.label(f"{net:,.0f} ر.ي").classes(f"kpi-value {'text-green-400' if net >= 0 else 'text-red-400'}")

        debtors = dm.financial.list_debtors()
        with ui.card().classes("portal-card w-full mt-4"):
            with ui.row().classes("items-center justify-between mb-3"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("warning").classes("text-xl text-amber-400")
                    ui.label(f"📋 المدينون ({len(debtors)})").classes("text-lg font-bold text-slate-100")
                ui.button("📥 CSV", on_click=lambda: _export_csv(debtors, "debtors.csv")) \
                    .props("color=green outline dense")

            if not debtors:
                ui.label("✅ لا توجد مديونيات").classes("text-green-400")
            else:
                with ui.element("table").classes("portal-table"):
                    with ui.element("thead"):
                        with ui.element("tr"):
                            for h in ["الرقم", "الاسم", "الصف", "الهاتف", "المديونية"]:
                                with ui.element("th"):
                                    ui.label(h)
                    with ui.element("tbody"):
                        for d in debtors[:50]:
                            with ui.element("tr"):
                                with ui.element("td"):
                                    ui.label(d.get("student_id", "")).classes("text-xs font-mono")
                                with ui.element("td"):
                                    ui.label(d.get("name", ""))
                                with ui.element("td"):
                                    ui.label(d.get("grade", ""))
                                with ui.element("td"):
                                    ui.label(d.get("parent_phone", "")).classes("text-xs font-mono")
                                with ui.element("td"):
                                    ui.label(f"{float(d.get('remaining_fees', 0)):,.0f}") \
                                        .classes("text-red-400 font-bold")

        receipts = dm.financial.list_receipts(limit=20)
        with ui.card().classes("portal-card w-full mt-4"):
            with ui.row().classes("items-center gap-2 mb-3"):
                ui.icon("receipt").classes("text-xl text-green-400")
                ui.label(f"🧾 آخر السندات ({len(receipts)})").classes("text-lg font-bold text-slate-100")

            if not receipts:
                ui.label("📭 لا توجد سندات").classes("text-slate-400")
            else:
                with ui.element("table").classes("portal-table"):
                    with ui.element("thead"):
                        with ui.element("tr"):
                            for h in ["رقم السند", "الطالب", "المبلغ", "التاريخ", "بواسطة"]:
                                with ui.element("th"):
                                    ui.label(h)
                    with ui.element("tbody"):
                        for r in receipts:
                            with ui.element("tr"):
                                with ui.element("td"):
                                    ui.label(str(r.get("receipt_id", ""))).classes("text-xs font-mono")
                                with ui.element("td"):
                                    ui.label(str(r.get("student_id", "")))
                                with ui.element("td"):
                                    ui.label(f"{float(r.get('amount', 0)):,.0f}") \
                                        .classes("text-green-400 font-bold")
                                with ui.element("td"):
                                    ui.label(str(r.get("date", ""))[:16]).classes("text-xs")
                                with ui.element("td"):
                                    ui.label(str(r.get("admin_name", ""))).classes("text-xs")
