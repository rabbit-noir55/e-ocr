FROM python:3.10-slim

WORKDIR /app

# Tizim paketlari (libgl1 - cv2 uchun zarur)
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

# Talablar
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
