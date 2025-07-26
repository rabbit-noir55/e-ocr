# ocr_utils.py
import cv2
import numpy as np
from PIL import Image, ImageOps
import logging
import re

logger = logging.getLogger(__name__)

# Rasmni tozalash parametrlari
DEFAULT_TARGET_HEIGHT = 64
DEFAULT_TARGET_WIDTH = 320
GAUSSIAN_BLUR_KERNEL = (5, 5)

def clean_string(input_str):
    """Faqat raqamlarni qoldirish"""
    return re.sub(r'[^0-9]', '', input_str)

def remove_noise_and_clean(image_array):
    """
    Rasm shovqinini olib tashlash va tozalash
    :param image_array: NumPy array ko'rinishidagi rasm
    :return: Tozalangan rasm (NumPy array)
    """
    try:
        # RGB dan GrayScale ga o'tkazish
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Gauss filtri bilan silliqlash
        blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KERNEL, 0)
        
        # Otsu's thresholding
        _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # GrayScale dan RGB ga qaytarish
        final_img = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)
        
        return final_img
    except Exception as e:
        logger.error(f"Rasmni tozalashda xatolik: {str(e)}", exc_info=True)
        raise

def preprocess_image(image_file, target_height=None, target_width=None):
    """
    Rasmni OCR uchun tayyorlash
    :param image_file: Upload qilingan rasm fayli
    :param target_height: Maqsadli balandlik
    :param target_width: Maqsadli kenglik
    :return: Qayta ishlangan rasm (NumPy array)
    """
    target_height = target_height or DEFAULT_TARGET_HEIGHT
    target_width = target_width or DEFAULT_TARGET_WIDTH
    
    try:
        # PIL Image ochish
        pil_image = Image.open(image_file)
        
        # RGBA yoki P formatdagi rasmlarni RGB ga o'tkazish
        if pil_image.mode in ['RGBA', 'P', 'L']:
            pil_image = pil_image.convert('RGB')
        
        # Rasm o'lchamini standartlashtirish
        pil_image = ImageOps.pad(
            pil_image, 
            (target_width, target_height), 
            color=(255, 255, 255),  # oq fon
            centering=(0.5, 0.5))
        
        # NumPy array ga o'tkazish
        img_array = np.array(pil_image)
        
        # Shovqinni olib tashlash
        cleaned_img = remove_noise_and_clean(img_array)
        
        return cleaned_img
    except Exception as e:
        logger.error(f"Rasmni qayta ishlashda xatolik: {str(e)}", exc_info=True)
        raise

def captcha_text(image_file):
    """
    CAPTCHA rasmidan matnni ajratib olish
    :param image_file: Upload qilingan rasm fayli
    :return: Tozalangan matn (faqat raqamlar)
    """
    try:
        # PaddleOCR importi faqat kerak bo'lganda
        from paddleocr import PaddleOCR
        
        # Rasmni tayyorlash
        processed_img = preprocess_image(image_file)
        
        # OCR modelini yaratish
        ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        
        # Matnni aniqlash
        result = ocr.predict(processed_img)
        
        # Natijalarni tozalash
        cleaned_text = clean_string(' '.join([res['rec_texts'][0] for res in result]))
        
        if not cleaned_text:
            logger.warning("CAPTCHA matni aniqlanmadi")
            return ""
            
        return cleaned_text
    except Exception as e:
        logger.error(f"CAPTCHA tahlil qilishda xatolik: {str(e)}", exc_info=True)
        raise
