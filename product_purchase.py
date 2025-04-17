import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from logger import log

def navigate_to_product(driver, product_id):
    product_url = f"https://www.gsshop.com/prd/prd.gs?prdid={product_id}"
    driver.get(product_url)
    print(f"Navigated to product page: {product_url}")

def navigate_to_enuri(driver, product_id):
    enuri_url = f"https://www.enuri.com/detail.jsp?modelno={product_id}"
    driver.get(enuri_url)

    # Enuri site: click the first li under filter_select
    time.sleep(3)
    # try:
    #     first_li = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "#filter_select li:first-child"))
    #     )
    #     first_li.click()
    #     print(f"[User {idx}] Enuri mode: '쇼핑몰' 필터 첫 번째 li 클릭 완료")
    # except Exception as e:
    #     print(f"[User {idx}] Enuri mode: '쇼핑몰' 필터 첫 번째 li 클릭 오류: {e}")
    #
    # try:
    #     # GS SHOP 라벨을 클릭하여 체크박스를 토글합니다.
    #     gs_shop_label = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable(
    #             (By.CSS_SELECTOR, "label[for='chkSELECT_SHOP_75']")
    #         )
    #     )
    #     gs_shop_label.click()
    #     print(f"[User {idx}] Enuri mode: 'GS SHOP' 라벨 클릭 완료")
    # except Exception as e:
    #     print(f"[User {idx}] Enuri mode: 'GS SHOP' 라벨 클릭 중 오류 발생: {e}")
    #
    # # Enuri site: click the "적용" button
    # time.sleep(2)
    # try:
    #     apply_btn = WebDriverWait(driver, 10).until(
    #         # EC.element_to_be_clickable((By.ID, "mall-layer-apply"))
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "div.btn__group button.btn__apply"))
    #     )
    #     print(apply_btn)
    #     apply_btn.click()
    #     print(f"[User {idx}] Enuri mode: '적용' 버튼 클릭 완료")
    # except Exception as e:
    #     print(f"[User {idx}] Enuri mode: '적용' 버튼 클릭 중 오류 발생: {e}")

    # Enuri site: click the first comparison row in the price table
    try:
        first_row = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "table.tb-compare__list tbody tr:first-child")
            )
        )
        first_row.click()
        print(f"Enuri mode: 첫 번째 비교 행 클릭 완료")
    except Exception as e:
        print(f"Enuri mode: 첫 번째 비교 행 클릭 중 오류 발생: {e}")

    handles = driver.window_handles
    time.sleep(3)

    # 1) 모든 핸들 순회
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        url = driver.current_url
        # 2) URL에 "/cust/alia/popup"이 포함되어 있으면 닫기
        if "with.gsshop.com/cust/alia/popup" in url:
            print(f"Closing popup tab: {url}")
            driver.close()
            break  # 하나만 닫고 나와도 OK

    if len(handles) - 1:
        next_handle = handles[-1]
        driver.switch_to.window(next_handle)

    print(f"url: {driver.current_url}")
    WebDriverWait(driver, 10).until(
        EC.url_contains("with.gsshop.com")
    )

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