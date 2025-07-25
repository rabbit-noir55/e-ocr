from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from paddleocr import PaddleOCR
import io
from PIL import Image,ImageOps
import numpy as np
import re
import cv2
def process_image(image_file):

    pil_image = Image.open(image_file)

    # RGBA yoki P formatdagi rasmlarni RGB formatga o'tkazamiz
    if pil_image.mode in ['RGBA', 'P', 'L']:
        pil_image = pil_image.convert('RGB')

    # Kichkina rasmlarda avtomatik padd qilish (masalan, CAPTCHA lar)
    target_height = 64
    target_width = 320

    pil_image = ImageOps.pad(pil_image, (target_width, target_height), color=(255,255,255), centering=(0.5, 0.5))

    img_array = np.array(pil_image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # Agar PaddleOCR model shovqinsiz rasm bilan yaxshi ishlasa:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    final_img = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)

    print(f"Final shape: {final_img.shape}, dtype: {final_img.dtype}, contiguous: {final_img.flags['C_CONTIGUOUS']}")
    return final_img

def clean_string(input_str):
    # Faqat raqamlar qoladi, bo'shliqlar va boshqa barcha belgilar olib tashlanadi
    cleaned_str = re.sub(r'[^0-9]', '', input_str)  # faqat raqamlar qoladi
    return cleaned_str
  # text detection + text recognition
def  captcha_text(img):
     ocr = PaddleOCR(
    use_doc_orientation_classify=False, 
    use_doc_unwarping=False, 
    use_textline_orientation=False)
     result=ocr.predict(process_image(img))
     return clean_string(' '.join([res['rec_texts'][0] for res in result]) )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        image = request.FILES.get('image')
        if not image:
            return Response({"error": "Rasm topilmadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Bu yerda sizning captcha_text() funksiyangiz chaqiriladi
            text = captcha_text(image)
            return Response({"message": text}, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)  # bu terminalga to‘liq traceback chiqaradi
            return Response(
                {"error": f"Ichki xatolik: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
