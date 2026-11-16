# -*- coding: utf-8 -*-
"""
portal/deps.py
═══════════════════════════════════════════════════════════════════
إدارة التبعيات — DataManager singleton + KPI cache.

المبادئ:
  • DataManager واحد فقط (thread-safe) — يفتح DB مرة واحدة
  • KPI cache بـ TTL 60 ثانية — يخفف الحمل على SQLite
  • لا execute_query من Portal — قراءة فقط
  • close() نظيف عند إيقاف التطبيق

الاستخدام:
    from portal.deps import get_dm, get_kpis
    dm = get_dm()
    kpis = get_kpis()
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# DataManager singleton
# ═══════════════════════════════════════════════════════════
_dm_lock = threading.Lock()
_dm_instance: Optional[Any] = None


def get_dm():
    """
    يُرجع DataManager singleton (thread-safe).

    أول استدعاء: ينشئ DataManager
    باقي الاستدعاءات: يُرجع نفسه
    """
    global _dm_instance
    if _dm_instance is not None:
        return _dm_instance

    with _dm_lock:
        if _dm_instance is None:
            from core.data_manager import DataManager
            _dm_instance = DataManager()
            logger.info("✅ Portal: DataManager initialized")
        return _dm_instance


def close_dm() -> None:
    """إغلاق نظيف — يُستدعى عند إيقاف التطبيق."""
    global _dm_instance
    with _dm_lock:
        if _dm_instance is not None:
            try:
                _dm_instance.close()
                logger.info("✅ Portal: DataManager closed")
            except Exception as exc:
                logger.warning("Portal close_dm: %s", exc)
            finally:
                _dm_instance = None


# ═══════════════════════════════════════════════════════════
# KPI Cache (TTL 60s)
# ═══════════════════════════════════════════════════════════
_kpi_cache: dict[str, Any] = {}
_kpi_cache_time: float = 0.0
_kpi_lock = threading.Lock()
KPI_TTL_SECONDS = 60.0


def get_kpis(force_refresh: bool = False) -> dict[str, Any]:
    """
    يُرجع KPIs (مع cache 60 ثانية).

    KPIs:
        total_students: عدد الطلاب
        today_attendance: {present, absent, late, excused}
        total_debt: مجموع المديونيات
        total_paid: مجموع المدفوعات
        vault_net: صافي الخزينة
        red_flags_count: عدد الطلاب المعرضين للخطر
        behavior_avg: متوسط نقاط السلوك
        academic_avg: متوسط المعدل الأكاديمي
    """
    global _kpi_cache, _kpi_cache_time

    now = time.time()
    if not force_refresh and _kpi_cache and (now - _kpi_cache_time) < KPI_TTL_SECONDS:
        return _kpi_cache

    with _kpi_lock:
        # double-check بعد القفل
        if not force_refresh and _kpi_cache and (now - _kpi_cache_time) < KPI_TTL_SECONDS:
            return _kpi_cache

        try:
            kpis = _compute_kpis()
            _kpi_cache = kpis
            _kpi_cache_time = time.time()
            logger.debug("KPI cache refreshed")
            return kpis
        except Exception as exc:
            logger.error("get_kpis: %s", exc)
            # في الفشل: أعد آخر cache إن وُجد
            return _kpi_cache or _empty_kpis()


def _empty_kpis() -> dict[str, Any]:
    """KPIs فارغة — في حال فشل الاستعلامات."""
    return {
        "total_students": 0,
        "today_attendance": {"present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0},
        "total_debt": 0.0,
        "total_paid": 0.0,
        "vault_net": 0.0,
        "red_flags_count": 0,
        "behavior_avg": 0.0,
        "academic_avg": 0.0,
    }


def _compute_kpis() -> dict[str, Any]:
    """يحسب KPIs من DB — قراءة فقط."""
    from datetime import datetime

    dm = get_dm()

    # 1. عدد الطلاب
    total_students = dm.students.count_all()

    # 2. حضور اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    attendance_stats = dm.attendance.get_stats_for_date(today)

    # 3. المالية
    vault = dm.get_vault_summary()

    # 4. Red flags
    red_flags = dm.get_predictive_red_flags()

    # 5. متوسط السلوك والأكاديمي
    analytics = dm.extract_ai_analytics_data() or {}
    behavior_avg = float(analytics.get("school_behavior_avg", 0) or 0)
    academic_avg = float(analytics.get("school_academic_avg", 0) or 0)

    return {
        "total_students": total_students,
        "today_attendance": {
            "present": attendance_stats.get("حاضر", 0),
            "absent": attendance_stats.get("غائب", 0),
            "late": attendance_stats.get("متأخر", 0),
            "excused": attendance_stats.get("بعذر", 0),
            "total": attendance_stats.get("total", 0),
        },
        "total_debt": float(vault.get("debt", 0)),
        "total_paid": float(vault.get("paid", 0)),
        "vault_net": float(vault.get("net", 0)),
        "red_flags_count": len(red_flags),
        "behavior_avg": round(behavior_avg, 2),
        "academic_avg": round(academic_avg, 2),
    }


def invalidate_kpi_cache() -> None:
    """يُبطل الـ cache يدوياً — يُستدعى بعد أي تعديل (نادراً)."""
    global _kpi_cache_time
    _kpi_cache_time = 0.0


# ═══════════════════════════════════════════════════════════
# Red Flags (مباشر — بدون cache، لأنه للعرض المفصل)
# ═══════════════════════════════════════════════════════════
def get_red_flags(limit: int = 20) -> list[dict]:
    """يُرجع قائمة الطلاب المعرضين للخطر (للعرض في dashboard)."""
    try:
        dm = get_dm()
        flags = dm.get_predictive_red_flags()
        return flags[:limit]
    except Exception as exc:
        logger.error("get_red_flags: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════
# Recent Activity (مباشر)
# ═══════════════════════════════════════════════════════════
def get_recent_activity(limit: int = 10) -> list[dict]:
    """آخر النشاطات (للـ dashboard)."""
    try:
        dm = get_dm()
        return dm.fetch_query(
            "SELECT timestamp, admin_name, action, details "
            "FROM activity_logs WHERE school_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (dm.school_id, int(limit)),
        )
    except Exception as exc:
        logger.error("get_recent_activity: %s", exc)
        return []


__all__ = [
    "get_dm",
    "close_dm",
    "get_kpis",
    "invalidate_kpi_cache",
    "get_red_flags",
    "get_recent_activity",
    "KPI_TTL_SECONDS",
]