import os
import requests
from requests.exceptions import RequestException

# 1. Rasm faylini tekshirish
image_path = os.path.join(os.path.dirname(__file__), 'image.png')
if not os.path.exists(image_path):
    print(f"Xato: {image_path} fayli topilmadi")
    print(f"Joriy papka: {os.getcwd()}")
    print(f"Mavjud fayllar: {os.listdir()}")
    exit()

# 2. API manzilini to'g'ri belgilash
url = "http://127.0.0.1:8000/upload/"

try:
    # 3. Rasmni yuklash
    with open(image_path, 'rb') as img_file:
        files = {'image': (os.path.basename(image_path), img_file, 'image/jpeg')}
        
        # 4. So'rov yuborish
        response = requests.post(url, files=files, timeout=100)
        response.raise_for_status()  # HTTP xatolarni ushlash
        
        # 5. Natijani ko'rish
        print("Muvaffaqiyatli javob!")
        print("Status kod:", response.status_code)
        print("Javob:", response.json())

except RequestException as e:
    print(f"Xato yuz berdi: {e}")

except Exception as e:
    print(f"Kutilmagan xato: {e}")