import base64
import io
import time
from logger import log
import cv2
import numpy as np
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ocr_utils import run_ocr_method


def login_and_navigate(driver, user_id, user_password):
    """
    주어진 아이디와 비밀번호로 로그인 페이지에 접속하여 로그인합니다.
    :param driver: Selenium WebDriver.
    :param user_id: 사용자 아이디.
    :param user_password: 사용자 비밀번호.
    """
    login_url = "https://www.gsshop.com/cust/login/login.gs?ssoChk=Y&returnurl=%2Findex.gs"
    driver.get(login_url)
    try:
        input_elem = driver.find_element(By.ID, "id")
        driver.execute_script("arguments[0].value = arguments[1];", input_elem, user_id)
        password_elem = driver.find_element(By.ID, "passwd")
        driver.execute_script("arguments[0].value = arguments[1];", password_elem, user_password)
        login_button = driver.find_element(By.ID, "btnLogin")
        login_button.click()
    except Exception as e:
        print("Error with login elements:", e)

def capture_captcha(driver):
    """
    캡차 이미지를 캡처하여 PIL 이미지로 반환하고, 'captcha.jpg'로 저장합니다.
    :param driver: Selenium WebDriver.
    :return: PIL Image 또는 실패 시 None.
    """
    try:
        captcha_img_elem = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "capchaimg"))
        )
        captcha_base64 = captcha_img_elem.screenshot_as_base64
        image_data = base64.b64decode(captcha_base64)
        original_image = Image.open(io.BytesIO(image_data))
        original_image.save("captcha.jpg")
        print("Original captcha image saved to: captcha.jpg")
        return original_image
    except Exception as e:
        print("Error capturing captcha:", e)
        return None

def try_candidates(driver, original_image, gray):
    """
    여러 OCR 기법을 순차적으로 적용하여 캡차를 해결하려 시도합니다.
    성공 시 (candidate, ocr_value)를, 모두 실패하면 (None, None)을 반환합니다.
    :param driver: Selenium WebDriver.
    :param original_image: 캡차의 원본 PIL 이미지.
    :param gray: 원본 이미지를 그레이스케일로 변환한 OpenCV 이미지.
    """
    candidate_order = [
        "Original",
        "No Black",
        "Grayscale Only",
        # "OTSU Threshold",
        "Adaptive Threshold",
        "Bilateral + Adaptive",
        "Morphological Closing"
    ]
    for candidate in candidate_order:
        print(f"\nCalculating OCR for candidate: {candidate}")
        ocr_value = None

        if candidate == "Original":
            ocr_value = run_ocr_method(original_image, label="Method0: Original (No Processing)")
        elif candidate == "No Black":
            original_gray = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2GRAY)
            no_black = original_gray.copy()
            no_black[no_black < 30] = 255
            cv2.imwrite("method0_no_black.png", no_black)
            pil_img = Image.fromarray(no_black)
            ocr_value = run_ocr_method(pil_img, label="Method0-1: No Black")
        elif candidate == "Grayscale Only":
            cv2.imwrite("method1_gray.png", gray)
            pil_img = Image.fromarray(gray)
            ocr_value = run_ocr_method(pil_img, label="Method1: Grayscale Only")
        elif candidate == "OTSU Threshold":
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            otsu_inv = 255 - otsu
            cv2.imwrite("method2_otsu.png", otsu_inv)
            pil_img = Image.fromarray(otsu_inv)
            ocr_value = run_ocr_method(pil_img, label="Method2: OTSU Threshold")
        elif candidate == "Adaptive Threshold":
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                             cv2.THRESH_BINARY_INV, blockSize=11, C=2)
            adaptive_inv = 255 - adaptive
            cv2.imwrite("method3_adaptive.png", adaptive_inv)
            pil_img = Image.fromarray(adaptive_inv)
            ocr_value = run_ocr_method(pil_img, label="Method3: Adaptive Threshold")
        elif candidate == "Bilateral + Adaptive":
            bilateral = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
            adaptive_bilateral = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                       cv2.THRESH_BINARY_INV, blockSize=11, C=2)
            adaptive_bilateral_inv = 255 - adaptive_bilateral
            cv2.imwrite("method4_bilateral_adaptive.png", adaptive_bilateral_inv)
            pil_img = Image.fromarray(adaptive_bilateral_inv)
            ocr_value = run_ocr_method(pil_img, label="Method4: Bilateral + Adaptive")
        elif candidate == "Morphological Closing":
            closing_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            closed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, closing_kernel, iterations=1)
            closed_inv = 255 - closed
            cv2.imwrite("method5_morphological_closing.png", closed_inv)
            pil_img = Image.fromarray(closed_inv)
            ocr_value = run_ocr_method(pil_img, label="Method5: Morphological Closing")

        print(f"{candidate} OCR 결과: {ocr_value}")
        if not ocr_value:
            print(f"{candidate} 결과가 비어있으므로 건너뜁니다.")
            continue

        try:
            confirm_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "confirmNum"))
            )
            confirm_elem.clear()
            confirm_elem.send_keys(ocr_value)

            confirm_btn = driver.find_element(By.ID, "capchaConfirmBtn")
            confirm_btn.click()

            time.sleep(1)
            current_url = driver.current_url
            # print(f"현재 URL: {current_url}")

            if current_url.startswith("https://www.gsshop.com/index.gs"):
                print(f"{candidate} 결과로 로그인 성공 또는 캡챠 통과 판정!")
                return candidate, ocr_value

            input_container = driver.find_element(By.CSS_SELECTOR, "div.gui-input.huge")
            class_attr = input_container.get_attribute("class")
            print(f"확인 후 입력 필드 클래스: {class_attr}")

            if "error" in class_attr:
                print(f"{candidate} 결과는 실패로 판단됩니다. 다음 후보를 시도합니다.")
                try:
                    clear_btn = input_container.find_element(By.CSS_SELECTOR, "a[data-type='clearValue']")
                    clear_btn.click()
                except Exception as ce:
                    print("지우기 버튼 클릭 실패:", ce)
                time.sleep(1)
            else:
                print(f"{candidate} 결과로 로그인 성공 또는 캡챠 통과 판정!")
                return candidate, ocr_value
        except Exception as e:
            print(f"Candidate 시도 중 오류 발생 ({candidate}):", e)
    return None, None

def solve_captcha_with_retries(driver, max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"\n[Captcha Attempt {attempt}/{max_retries}]")
        original_image = capture_captcha(driver)
        if original_image is None:
            print("Captcha image capture failed.")
            continue
        cv_image = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        candidate, ocr_value = try_candidates(driver, original_image, gray)
        if candidate:
            print(f"\n[Success] Captcha solved with candidate: {candidate}")
            return candidate, ocr_value
        else:
            print("[Fail] Captcha solving failed for all candidates.")
            if attempt < max_retries:
                try:
                    reload_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".gui-btn.security-code_reload"))
                    )
                    reload_button.click()
                    print("Clicked '새로고침' to refresh captcha.")
                    time.sleep(2)
                except Exception as e:
                    print("Error clicking refresh button:", e)
                    continue
    print(f"\n[Error] Failed to solve captcha after {max_retries} attempts.")
    return None, None