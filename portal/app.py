# -*- coding: utf-8 -*-
"""
portal/app.py
═══════════════════════════════════════════════════════════════════
نقطة دخول البوابة — NiceGUI 3.19.0

V1.1 — إصلاح circular import:
  • _setup_theme و _build_header انتقلا إلى portal/layout.py
  • app.py لم يعد يستورد الصفحات في المستوى الأعلى (lazy imports)
  • on_startup / on_shutdown مسجّلة مرة واحدة فقط

التشغيل:
    python -m portal.app
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# أضف جذر المشروع إلى sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nicegui import app as ng_app, ui

from config.constants import APP_NAME_AR, APP_VERSION
from portal import __version__ as portal_version
from portal.auth import get_current_user, requires_setup
from portal.deps import close_dm, get_dm

logger = logging.getLogger("portal")


# ═══════════════════════════════════════════════════════════
# Root Route — Redirect
# ═══════════════════════════════════════════════════════════
@ui.page("/")
def _root() -> None:
    """الصفحة الرئيسية: redirect إلى /setup أو /login أو /dashboard."""
    if requires_setup():
        ui.navigate.to("/setup")
        return
    user = get_current_user()
    if user is None:
        ui.navigate.to("/login")
    else:
        ui.navigate.to("/dashboard")


# ═══════════════════════════════════════════════════════════
# Import pages (lazy — بعد تعريف ui.page("/"))
# ═══════════════════════════════════════════════════════════
def _register_pages() -> None:
    """يستورد الصفحات — lazy، بعد أن يكون app.py جاهزاً."""
    from portal.pages import (  # noqa: F401
        dashboard,
        financial,
        grades,
        login,
        settings,
        setup,
        students,
    )
    logger.info("✅ All 7 pages registered")


# ═══════════════════════════════════════════════════════════
# Lifecycle (تُسجّل مرة واحدة فقط — قبل ui.run())
# ═══════════════════════════════════════════════════════════
@ng_app.on_startup
async def _on_startup() -> None:
    """تهيئة التطبيق."""
    logger.info("🚀 Portal starting...")
    get_dm()  # يُهيّئ DataManager


@ng_app.on_shutdown
async def _on_shutdown() -> None:
    """إغلاق نظيف."""
    logger.info("🛑 Portal shutting down...")
    close_dm()


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
def main() -> None:
    """نقطة الدخول."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    # سجّل الصفحات أولاً
    _register_pages()

    # إعدادات NiceGUI
    port = int(os.getenv("PORTAL_PORT", "8080"))
    host = os.getenv("PORTAL_HOST", "0.0.0.0")
    storage_secret = os.getenv(
        "STORAGE_SECRET", "giant-portal-secret-2026-change-me"
    )

    logger.info(f"🌐 Starting Portal on {host}:{port}")
    logger.info(f"📦 {APP_NAME_AR} v{APP_VERSION}")
    logger.info(f"🏛️ Portal v{portal_version}")

    ui.run(
        title=f"{APP_NAME_AR} — البوابة",
        host=host,
        port=port,
        favicon="🏛️",
        dark=True,
        reload=False,
        show=False,
        storage_secret=storage_secret,
    )


if __name__ == "__main__":
    main()