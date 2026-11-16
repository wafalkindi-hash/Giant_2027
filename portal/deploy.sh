#!/bin/bash
# ═══════════════════════════════════════════════════════
# deploy.sh — نشر البوابة على Fly.io
# ═══════════════════════════════════════════════════════
set -e

echo "🚀 بدء النشر على Fly.io..."

cd "$(dirname "$0")"

if ! command -v fly &> /dev/null; then
    echo "❌ flyctl غير مثبت"
    exit 1
fi

fly deploy

echo "✅ تم النشر — افتح: fly open"
