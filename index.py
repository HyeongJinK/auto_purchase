import base64
import csv
import io
import re
import time

import cv2
import easyocr
import numpy as np
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

############################################
# 전역 Selenium WebDriver (Optional 사용)
############################################
global_driver = None

############################################
# CSV에서 사용자 정보 가져오기 (웹에 공개된 구글 시트 CSV)
############################################
def get_user_info_from_public_csv(csv_url):
    response = requests.get(csv_url)
    response.raise_for_status()

    content = response.content.decode("utf-8-sig")
    f = io.StringIO(content, newline='')
    reader = csv.DictReader(f)
    data = []
    for row in reader:
        data.append(row)
    return data

############################################
# OCR 함수
############################################
def alternative_easyocr(image_pil, label=""):
    try:
        reader = easyocr.Reader(["en"], gpu=False)
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

############################################
# 자동화 주요 함수: 로그인, 캡차, 주문, 배송지
############################################
def login_and_navigate(driver, user_id, user_password):
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
    candidate_order = [
        "Original",
        "No Black",
        "Grayscale Only",
        "OTSU Threshold",
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
            print(f"현재 URL: {current_url}")

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

def navigate_to_product(driver, product_id):
    product_url = f"https://www.gsshop.com/prd/prd.gs?prdid={product_id}"
    driver.get(product_url)
    print(f"Navigated to product page: {product_url}")

def order_product(driver, quantity):
    try:
        qty_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tabOptCntSub"))
        )
        qty_input.click()
        qty_input.send_keys(Keys.CONTROL, "a")
        qty_input.send_keys(Keys.BACKSPACE)
        qty_input.send_keys(str(quantity))
        print(f"수량을 {quantity}개로 설정했습니다.")

        order_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ordButtn"))
        )
        order_button.click()
        print("바로구매 버튼을 클릭했습니다.")
    except Exception as e:
        print("상품 주문 처리 중 오류 발생:", e)

def fill_receiver_info(driver, receiver_name, base_addr, dtl_addr, contact, pickup_location):
    """
    Fill out the receiver info form, then open the zip code popup and handle steps:
      - receiver_name (id='rcvrNm0')
      - base_addr (id='baseAddr0')
      - detail_addr (popup step)
      - contact: e.g. '01012345678' => prefix, mid, last
      - pickup_location (id='dlvPickMsgCntnt0')
      - In the popup: input base_addr in 'roadNmBldNm', click search, select address,
        fill dtl_addr in 'detailAddress', then click '배송지로 등록'.

    :param driver: Selenium WebDriver.
    :param receiver_name: string, name of the receiver.
    :param base_addr: string, base address.
    :param dtl_addr: string, detail address for the popup.
    :param contact: string, phone number, e.g. '01012345678' (11 digits).
    :param pickup_location: string, e.g. '문앞' for receiving location.
    """
    # 1) Receiver name
    try:
        rcvr_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "rcvrNm0"))
        )
        rcvr_input.clear()
        rcvr_input.send_keys(receiver_name)
        print(f"Receiver name set to: {receiver_name}")
    except Exception as e:
        print("Error setting receiver name:", e)

    # 2) Contact phone number
    try:
        if len(contact) >= 11:
            prefix = contact[:3]
            mid = contact[3:7]
            last = contact[7:11]
        else:
            print("Contact number length is less than expected!")
            prefix = contact[:3]
            mid = contact[3:7] if len(contact) >= 7 else ""
            last = contact[7:] if len(contact) >= 11 else ""

        # hidden input for prefix
        regon_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "genrlRegonTelno0"))
        )
        driver.execute_script("arguments[0].value = arguments[1];", regon_input, prefix)
        print(f"Phone prefix set to: {prefix}")

        # mid
        txno_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "genrlTxnoTelno0"))
        )
        txno_input.clear()
        txno_input.send_keys(mid)
        print(f"Phone mid set to: {mid}")

        # last
        dtl_tel_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "genrlDtlTelno0"))
        )
        dtl_tel_input.clear()
        dtl_tel_input.send_keys(last)
        print(f"Phone last set to: {last}")
    except Exception as e:
        print("Error setting contact number:", e)

    # 3) Pickup location
    try:
        pickup_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dlvPickMsgCntnt0"))
        )
        pickup_input.clear()
        pickup_input.send_keys(pickup_location)
        print(f"Pickup location set to: {pickup_location}")
    except Exception as e:
        print("Error setting pickup location:", e)

    # 4) Zip code popup and detail address
    try:
        # Click '우편번호 찾기' link
        zip_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'우편번호 찾기')]"))
        )
        main_handle = driver.current_window_handle
        zip_btn.click()
        print("Clicked '우편번호 찾기' button.")

        # Wait for popup
        time.sleep(2)
        handles = driver.window_handles
        if len(handles) > 1:
            # The popup is usually the last handle
            new_window = handles[-1]
            if new_window != main_handle:
                driver.switch_to.window(new_window)
                print("Switched to popup window.")
            else:
                print("Popup window handle is same as main_handle; consider checking other handles.")

        # Fill base_addr in the popup
        road_nm_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "roadNmBldNm"))
        )
        road_nm_input.clear()
        road_nm_input.send_keys(base_addr)
        print(f"Popup input 'roadNmBldNm' set to: {base_addr}")

        # Click search button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchSubmit"))
        )
        search_button.click()
        print("검색 버튼을 클릭했습니다.")

        # Search result link
        a_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#srch-lst li a"))
        )
        a_element.click()
        print("해당 a 태그를 클릭했습니다.")

        # detailAddress input
        detail_addr_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "detailAddress"))
        )
        detail_addr_input.clear()
        detail_addr_input.send_keys(dtl_addr)
        print(f"Detail address set to: {dtl_addr}")

        # 배송지로 등록 button
        register_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., '배송지로 등록')]"))
        )
        try:
            register_btn.click()
        except Exception as exc:
            print("일반 클릭 실패:", exc)
            driver.execute_script("arguments[0].click();", register_btn)
        print("배송지로 등록 버튼을 클릭했습니다.")
        time.sleep(2)
        print("2초 대기 후 다음 작업 진행")

        # Optionally close popup and switch back
        # driver.close()
        # driver.switch_to.window(main_handle)
        print("Closed popup window and switched back to main window.")
    except Exception as e:
        print("Error handling the zip code popup:", e)


############################################
# run_automation(csv_url)
############################################
def run_automation(csv_url):
    global global_driver
    # 1) CSV에서 사용자 목록 로드
    try:
        sheet_data = get_user_info_from_public_csv(csv_url)
    except Exception as e:
        print("CSV URL 로드 실패:", e)
        return

    # 2) 브라우저 시작
    chrome_options = Options()
    global_driver = webdriver.Chrome(options=chrome_options)

    for idx, row in enumerate(sheet_data, start=1):
        print(f"\n=== [User {idx}] Start Process ===")
        global_driver.execute_script("window.open('');")
        global_driver.switch_to.window(global_driver.window_handles[-1])

        # 파싱
        user_id = row.get("id", "")
        user_password = row.get("password", "")
        product_id = row.get("product_id", "")
        quantity = int(row.get("quantity", 1))
        receiver_name = row.get("receiver_name", "")
        base_addr = row.get("base_addr", "")
        dtl_addr = row.get("dtl_addr", "")
        contact = row.get("contact", "")
        pickup_location = row.get("pickup_location", "")

        try:
            # 로그인
            login_and_navigate(global_driver, user_id, user_password)

            # 캡차
            candidate, value = solve_captcha_with_retries(global_driver, max_retries=3)
            if candidate:
                print(f"[User {idx}] Captcha success: {candidate}, {value}")
                # 상품 이동
                navigate_to_product(global_driver, product_id)
                # 주문
                order_product(global_driver, quantity)
                # 배송지
                fill_receiver_info(
                    driver=global_driver,
                    receiver_name=receiver_name,
                    base_addr=base_addr,
                    dtl_addr=dtl_addr,
                    contact=contact,
                    pickup_location=pickup_location
                )
            else:
                print(f"[User {idx}] 캡차 실패, 이 사용자 작업 종료.")

        except Exception as exc:
            print(f"[User {idx}] 전체 처리 중 오류:", exc)
        finally:
            if len(global_driver.window_handles) > 0:
                global_driver.switch_to.window(global_driver.window_handles[0])

    print("\n모든 사용자에 대한 순차 처리가 완료되었습니다.")
    # 브라우저를 임의로 닫지 않음 (사용자가 직접 닫도록)

############################################
# Tkinter UI
############################################
import tkinter as tk
def on_run_button_click():
    button_run.config(text="실행중...", state="disabled")
    root.update_idletasks()

    csv_url = entry_csv_url.get().strip()
    if not csv_url:
        from tkinter import messagebox
        messagebox.showwarning("입력 오류", "CSV URL을 입력해주세요.")
        button_run.config(text="실행", state="normal")
        return

    run_automation(csv_url)

    button_run.config(text="실행", state="normal")
    from tkinter import messagebox
    messagebox.showinfo("완료", "모든 작업이 완료되었습니다.")

def on_exit_button_click():
    # 브라우저는 임의로 닫지 않는다
    root.quit()

root = tk.Tk()
root.title("Auto Purchase")
root.geometry("400x180")

label = tk.Label(root, text="CSV URL:")
label.pack(pady=5)

entry_csv_url = tk.Entry(root, width=50)
entry_csv_url.pack(pady=5)

button_run = tk.Button(root, text="실행", command=on_run_button_click)
button_run.pack(pady=10)

button_exit = tk.Button(root, text="프로그램 종료", command=on_exit_button_click)
button_exit.pack(pady=5)

root.mainloop()