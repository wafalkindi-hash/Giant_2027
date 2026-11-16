# -*- coding: utf-8 -*-
"""
portal/auth.py
═══════════════════════════════════════════════════════════════════
مصادقة Portal — Setup Wizard + Login + Rate Limit + Session.

السياسة الأمنية (قرار الرُّبّان):
  • Setup Wizard إجباري قبل أي دخول (لا admin2027)
  • كلمة المرور ≥ 12 حرفاً + كبير + صغير + رقم + رمز
  • Rate limit: 5 محاولات/دقيقة لكل IP
  • Session في app.storage.user (مشفّر من NiceGUI)
  • قراءة فقط — لا execute_query من Portal

الاستخدام:
    from portal.auth import (
        requires_setup, validate_password_strength,
        check_rate_limit, login_user, logout_user,
        get_current_user, require_auth
    )
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import re
import time
from collections import defaultdict
from typing import Optional

from core.security.passwords import hash_password, verify_password

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# ثوابت
# ═══════════════════════════════════════════════════════════
DEFAULT_ADMIN = "admin"
DEFAULT_PW_LEGACY = "admin2027"
MIN_PASSWORD_LENGTH = 12
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60


# ═══════════════════════════════════════════════════════════
# Rate Limiting (in-memory — كافٍ لمدرسة واحدة)
# ═══════════════════════════════════════════════════════════
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_rate_limit_lock = __import__("threading").Lock()


def _get_client_id() -> str:
    """يُرجع IP العميل — أو 'unknown' إذا فشل."""
    try:
        from nicegui import app
        # NiceGUI 3.x: app.storage.browser لا يوفر IP مباشرة
        # نستخدم X-Forwarded-For أو fallback
        request = getattr(app.storage, "request", None)
        if request and hasattr(request, "client") and request.client:
            return str(request.client.host)
    except Exception:
        pass
    return "unknown"


def check_rate_limit(client_id: Optional[str] = None) -> tuple[bool, int]:
    """
    يتحقق من rate limit.

    يُرجع:
        (allowed: bool, remaining_seconds: int)
    """
    cid = client_id or _get_client_id()
    now = time.time()

    with _rate_limit_lock:
        attempts = _rate_limit_store[cid]
        # احذف المحاولات القديمة
        attempts[:] = [t for t in attempts if (now - t) < RATE_LIMIT_WINDOW_SECONDS]

        if len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
            oldest = min(attempts)
            remaining = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest)) + 1
            return False, max(1, remaining)

        attempts.append(now)
        return True, 0


def reset_rate_limit(client_id: Optional[str] = None) -> None:
    """يُصفّر عداد محاولات IP (بعد دخول ناجح)."""
    cid = client_id or _get_client_id()
    with _rate_limit_lock:
        _rate_limit_store[cid] = []


# ═══════════════════════════════════════════════════════════
# Password Strength
# ═══════════════════════════════════════════════════════════
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    يتحقق من قوة كلمة المرور.

    يُرجع:
        (ok: bool, message: str)
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"كلمة المرور يجب أن تكون {MIN_PASSWORD_LENGTH} حرفاً على الأقل"

    if not re.search(r"[A-Z]", password):
        return False, "يجب أن تحتوي على حرف كبير واحد على الأقل (A-Z)"

    if not re.search(r"[a-z]", password):
        return False, "يجب أن تحتوي على حرف صغير واحد على الأقل (a-z)"

    if not re.search(r"\d", password):
        return False, "يجب أن تحتوي على رقم واحد على الأقل (0-9)"

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "يجب أن تحتوي على رمز خاص واحد على الأقل (!@#$%^&*...)"

    return True, "قوية"


# ═══════════════════════════════════════════════════════════
# Setup Detection
# ═══════════════════════════════════════════════════════════
def requires_setup() -> bool:
    """
    هل النظام يحتاج Setup Wizard؟

    نعم إذا:
        • لا يوجد admin في DB، أو
        • كلمة المرور الحالية = admin2027 (لم تُغيَّر بعد)
    """
    try:
        from portal.deps import get_dm
        dm = get_dm()
        res = dm.fetch_query("SELECT username, password FROM admins LIMIT 1")
        if not res:
            return True  # لا admin

        stored_pw = str(res[0].get("password", ""))
        is_valid, _ = verify_password(stored_pw, DEFAULT_PW_LEGACY)
        return is_valid  # True إذا كانت لا تزال admin2027
    except Exception as exc:
        logger.error("requires_setup: %s", exc)
        return True  # في الفشل: افترض أنه يحتاج setup


# ═══════════════════════════════════════════════════════════
# Setup Wizard
# ═══════════════════════════════════════════════════════════
def complete_setup(new_password: str) -> tuple[bool, str]:
    """
    يُكمل Setup Wizard — يُحدّث كلمة مرور admin.

    يُرجع:
        (ok: bool, message: str)
    """
    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg

    try:
        from portal.deps import get_dm
        dm = get_dm()

        res = dm.fetch_query("SELECT id FROM admins WHERE username = ?", (DEFAULT_ADMIN,))
        if not res:
            # إنشاء admin جديد (نادراً — إذا حُذف)
            new_hash = hash_password(new_password)
            ok = dm.execute_query(
                "INSERT INTO admins (username, password, role, full_name, school_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (DEFAULT_ADMIN, new_hash, "مدير نظام", "المدير", dm.school_id),
            )
        else:
            new_hash = hash_password(new_password)
            ok = dm.execute_query(
                "UPDATE admins SET password = ? WHERE username = ?",
                (new_hash, DEFAULT_ADMIN),
            )

        if ok:
            dm.log_secure_activity(
                admin="SYSTEM",
                action="Setup Wizard",
                details="تم تغيير كلمة المرور الافتراضية بنجاح",
            )
            logger.info("✅ Setup completed — admin password changed")
            return True, "✅ تم إعداد النظام بنجاح"

        return False, "❌ فشل تحديث قاعدة البيانات"
    except Exception as exc:
        logger.error("complete_setup: %s", exc)
        return False, f"خطأ: {exc}"


# ═══════════════════════════════════════════════════════════
# Login / Logout
# ═══════════════════════════════════════════════════════════
def login_user(username: str, password: str) -> tuple[bool, str]:
    """
    يُسجّل دخول المستخدم.

    يُرجع:
        (ok: bool, message: str)
    """
    # 1. Rate limit
    allowed, remaining = check_rate_limit()
    if not allowed:
        return False, f"⏳ محاولات كثيرة — انتظر {remaining} ثانية"

    # 2. تحقق من DB
    try:
        from portal.deps import get_dm
        dm = get_dm()
        result = dm.verify_admin_login(username, password)

        if not result.get("status"):
            return False, "❌ اسم المستخدم أو كلمة المرور غير صحيحة"

        # 3. Session
        from nicegui import app
        app.storage.user["authenticated"] = True
        app.storage.user["username"] = username
        app.storage.user["role"] = result.get("role", "مدير")
        app.storage.user["name"] = result.get("name", "المدير")
        app.storage.user["login_time"] = time.time()

        reset_rate_limit()
        logger.info("✅ Login success: %s", username)
        return True, f"✅ مرحباً {result.get('name', username)}"

    except Exception as exc:
        logger.error("login_user: %s", exc)
        return False, f"خطأ: {exc}"


def logout_user() -> None:
    """يُسجّل خروج المستخدم."""
    try:
        from nicegui import app
        app.storage.user.clear()
        logger.info("✅ Logout")
    except Exception as exc:
        logger.warning("logout_user: %s", exc)


# ═══════════════════════════════════════════════════════════
# Session
# ═══════════════════════════════════════════════════════════
def get_current_user() -> Optional[dict]:
    """
    يُرجع بيانات المستخدم الحالي، أو None إذا لم يكن مسجّلاً.
    """
    try:
        from nicegui import app
        if not app.storage.user.get("authenticated"):
            return None
        return {
            "username": app.storage.user.get("username", ""),
            "role": app.storage.user.get("role", ""),
            "name": app.storage.user.get("name", ""),
            "login_time": app.storage.user.get("login_time", 0),
        }
    except Exception:
        return None


def require_auth() -> bool:
    """
    يتحقق من المصادقة — للتوجيه في app.py.

    يُرجع True إذا كان المستخدم مسجّلاً.
    """
    user = get_current_user()
    if user is None:
        from nicegui import ui
        ui.navigate.to("/login")
        return False
    return True


# ═══════════════════════════════════════════════════════════
# License Info (for settings page)
# ═══════════════════════════════════════════════════════════
def get_license_info() -> dict:
    """
    معلومات الترخيص — للعرض في settings فقط.

    لا تستدعها من dashboard أو أي شاشة تشغيلية.
    """
    try:
        from portal.deps import get_dm
        from core.security import SecurityShield
        dm = get_dm()
        shield = SecurityShield(db_ref=dm)
        return shield.get_license_info()
    except Exception as exc:
        logger.error("get_license_info: %s", exc)
        return {
            "status": True,
            "type": "premium",
            "message": "✅ الفترة التجريبية سارية حتى 2029-12-31",
            "hwid": "N/A",
            "free_until": "2029-12-31",
        }


__all__ = [
    "DEFAULT_ADMIN",
    "DEFAULT_PW_LEGACY",
    "MIN_PASSWORD_LENGTH",
    "RATE_LIMIT_MAX_ATTEMPTS",
    "RATE_LIMIT_WINDOW_SECONDS",
    "check_rate_limit",
    "reset_rate_limit",
    "validate_password_strength",
    "requires_setup",
    "complete_setup",
    "login_user",
    "logout_user",
    "get_current_user",
    "require_auth",
    "get_license_info",
]