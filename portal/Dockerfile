# ═══════════════════════════════════════════════════════
# portal/Dockerfile — النشر على Fly.io
# ═══════════════════════════════════════════════════════
FROM python:3.12-slim

# متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORTAL_ENV=production \
    PORTAL_HOST=0.0.0.0 \
    PORTAL_PORT=8080

# مجلد العمل
WORKDIR /app

# تثبيت المتطلبات
COPY portal/requirements.txt /app/portal/requirements.txt
RUN pip install --no-cache-dir -r /app/portal/requirements.txt

# نسخ الكود
COPY config/ /app/config/
COPY core/ /app/core/
COPY utils/ /app/utils/
COPY portal/ /app/portal/

# إنشاء مجلد البيانات (SQLite)
RUN mkdir -p /app/data /app/exports

# المنفذ
EXPOSE 8080

# التشغيل
CMD ["python", "-m", "portal.app"]
