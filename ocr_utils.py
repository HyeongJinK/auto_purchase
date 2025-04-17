import re
import easyocr
import numpy as np
from logger import log

############################################
# OCR 함수
############################################
def alternative_easyocr(image_pil, label=""):
    try:
        reader = easyocr.Reader(["en"], gpu=True)
        np_img = np.array(image_pil)
        result = reader.readtext(np_img, detail=0, paragraph=True)
        text = "".join(result)
        digits = re.sub(r'\\D', '', text)
        print(f"[{label} - EasyOCR] Extracted digits: {digits}")
        return digits
    except Exception as e:
        print(f"[{label} - EasyOCR] OCR extraction error: {e}")
        return ""

def run_ocr_method(image_pil, label=""):
    return alternative_easyocr(image_pil, label=label)