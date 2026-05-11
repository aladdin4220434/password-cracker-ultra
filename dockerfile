FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إعدادات الأداء
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2
ENV UVLOOP=true

# منفذ التشغيل
EXPOSE 5000

# تشغيل باستخدام gunicorn
CMD ["gunicorn", "-w", "4", "--threads", "8", "--worker-class", "gthread", "--bind", "0.0.0.0:5000", "app:app"]
