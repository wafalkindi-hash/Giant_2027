# 🏛️ البوابة الإدارية — NiceGUI Portal

## التشغيل المحلي
$env:PORTAL_PORT="8080"
python -m portal.app

ثم افتح: http://localhost:8080

## النشر على Fly.io
1. تثبيت flyctl:
   iwr https://fly.io/install.ps1 -useb | iex
2. تسجيل الدخول:
   fly auth signup
3. إنشاء التطبيق:
   cd portal
   fly launch --no-deploy
4. نشر:
   fly deploy
5. فتح:
   fly open

## متغيرات البيئة
- PORTAL_PORT: المنفذ (افتراضي 8080)
- PORTAL_HOST: المضيف (افتراضي 0.0.0.0)
- PORTAL_ENV: dev أو production
- STORAGE_SECRET: سر الجلسة (غيّره في الإنتاج!)

## المتطلبات
- Python 3.12+
- nicegui==3.19.0
- cryptography
