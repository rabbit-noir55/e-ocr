from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
import time
from functools import wraps

# Logger sozlash
logger = logging.getLogger(__name__)

# Sozlamalar
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png']
MAX_PROCESSING_TIME = 10  # soniya
REQUEST_TIMEOUT = 30  # soniya

# Xatolarni ushlash uchun dekorator
def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Noto'g'ri qiymat: {str(e)}")
            raise
        except IOError as e:
            logger.error(f"IO xatolik: {str(e)}")
            raise
        except Exception as e:
            logger.critical(f"Kutilmagan xatolik: {str(e)}", exc_info=True)
            raise
    return wrapper

# Vaqt cheklovi dekoratori
def timeout_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        processing_time = time.time() - start_time
        
        if processing_time > MAX_PROCESSING_TIME:
            logger.warning(f"Funksiya {func.__name__} {processing_time:.2f} soniyada yakunlandi")
        
        return result
    return wrapper

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validate_environment()

    def _validate_environment(self):
        """Server muhitini tekshirish"""
        try:
            import cv2
            import numpy as np
            from PIL import Image, ImageOps
        except ImportError as e:
            logger.critical(f"Kerakli kutubxona yo'q: {str(e)}")
            raise ImportError("Kerakli tasvir qayta ishlash kutubxonalari o'rnatilmagan")

    @handle_errors
    def validate_image(self, image):
        """Rasmni tekshirish"""
        if not image:
            raise ValueError("Rasm fayli topilmadi")
        
        if image.size > MAX_IMAGE_SIZE:
            raise ValueError(
                f"Rasm hajmi {image.size//1024//1024}MB, "
                f"ruxsat etilgan maksimum {MAX_IMAGE_SIZE//1024//1024}MB"
            )
        
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Rasm formati {image.content_type} qo'llab-quvvatlanmaydi. "
                f"Faqat {', '.join(ALLOWED_IMAGE_TYPES)} formatlari qo'llab-quvvatlanadi"
            )
        
        # Fayl nomini tekshirish
        if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValueError("Noto'g'ri fayl kengaytmasi")

    @timeout_handler
    @handle_errors
    def process_request(self, image):
        """So'rovni qayta ishlash"""
        from .ocr_utils import captcha_text  # OCR funksiyasi alohida modulda
        
        start_time = time.time()
        result = captcha_text(image)
        processing_time = time.time() - start_time
        
        if processing_time > MAX_PROCESSING_TIME:
            logger.warning(f"OCR jarayoni {processing_time:.2f} soniyada yakunlandi")
        
        if not result:
            raise ValueError("CAPTCHA matni aniqlanmadi")
        
        return result

    def post(self, request, format=None):
        try:
            # So'rov vaqtini tekshirish
            if hasattr(request, 'start_time') and time.time() - request.start_time > REQUEST_TIMEOUT:
                raise TimeoutError("So'rov muddati tugadi")

            image = request.FILES.get('image')
            
            # Rasmni tekshirish
            self.validate_image(image)
            
            # OCR jarayoni
            text = self.process_request(image)
            
            logger.info(
                f"CAPTCHA muvaffaqiyatli tahlil qilindi. "
                f"Fayl: {image.name}, Hajmi: {image.size} bayt, Natija: {text}"
            )
            
            return Response({"message": text}, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Noto'g'ri so'rov: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TimeoutError as e:
            logger.error(f"So'rov muddati tugadi: {str(e)}")
            return Response(
                {"error": "Ishlov berish uchun etarli vaqt yo'q"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        except ImportError as e:
            logger.critical(f"Kutubxona yetishmayapti: {str(e)}")
            return Response(
                {"error": "Server sozlamalarida muammo"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(
                f"CAPTCHA tahlil qilishda xatolik. "
                f"Fayl: {image.name if image else 'N/A'}, Xatolik: {str(e)}",
                exc_info=True
            )
            return Response(
                {"error": "CAPTCHA tahlil qilinmadi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
