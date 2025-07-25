FROM python:3.10  # `slim` emas — to‘liq Python bazasi

WORKDIR /app

# Tizim kutubxonalarini o‘rnatish (cv2, paddle uchun zarur)
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 ffmpeg wget unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Fayllarni nusxalash
COPY . /app

# Python kutubxonalarini o‘rnatish
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Uvicorn orqali ishga tushirish
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
