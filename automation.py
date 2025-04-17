import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from logger import log
from csv_utils import get_user_info_from_public_csv
from input_values import fill_receiver_info
from login_captcha import login_and_navigate, solve_captcha_with_retries
from product_purchase import navigate_to_product, order_product, navigate_to_enuri
import config
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

############################################
# 전역 Selenium WebDriver (Optional 사용)
############################################
global_driver = None


############################################
# 자동화 주요 함수: 로그인, 캡차, 주문, 배송지
############################################
def run_automation(csv_url):
    global global_driver
    # 1) CSV에서 사용자 목록 로드
    try:
        sheet_data = get_user_info_from_public_csv(csv_url)
    except Exception as e:
        print("CSV URL 로드 실패: " + str(e))
        return

    # 2) 브라우저 시작
    chrome_options = Options()
    global_driver = webdriver.Chrome(options=chrome_options)

    for idx, row in enumerate(sheet_data, start=1):
        print(f"\n=== [User {idx}] Start Process ===")
        global_driver.execute_script("window.open('');")
        global_driver.switch_to.window(global_driver.window_handles[-1])

        # 파싱
        values = list(row.values())
        user_id = values[0]
        user_password = values[1]
        product_id = values[2]
        quantity = int(values[3])  # 수량은 정수로
        sender = values[3]  # 보내는 사람
        receiver_name = values[5]
        base_addr = values[6]
        dtl_addr = values[7]
        contact = values[8]
        pickup_location = values[9]
        coupon = values[10]  #  쿠폰
        allpoint = values[11]  # allpoint
        gspoint = values[12]  # gspoint
        card = values[13]  # 카드

        try:
            # 로그인
            login_and_navigate(global_driver, user_id, user_password)

            # 캡차
            candidate, value = solve_captcha_with_retries(global_driver, max_retries=3)

            if candidate:
                print(f"[User {idx}] Captcha success: {candidate}, {value}")
                # 상품 이동: 에누리 모드일 경우 Enuri 사이트로, 아니면 기본 navigate_to_product 호출
                if getattr(config, "enuri_flag", False):
                    navigate_to_enuri(global_driver, product_id)
                else:
                    navigate_to_product(global_driver, product_id)
                    # wait until the page URL starts with the expected GS Shop prefix
                # 주문
                order_product(global_driver, quantity)
                # 배송지
                fill_receiver_info(
                    driver=global_driver,
                    sender = sender,
                    receiver_name=receiver_name,
                    base_addr=base_addr,
                    dtl_addr=dtl_addr,
                    contact=contact,
                    pickup_location=pickup_location,
                    allpoint = allpoint,
                    gspoint = gspoint,
                    card = card
                )
            else:
                print(f"[User {idx}] 캡차 실패, 이 사용자 작업 종료.")

        except Exception as exc:
            print(f"[User {idx}] 전체 처리 중 오류: " + str(exc))
        finally:
            print("[User {idx}] 브라우저 종료 대기 중...")
            if len(global_driver.window_handles) > 0:
                global_driver.switch_to.window(global_driver.window_handles[0])

    print("\n모든 사용자에 대한 순차 처리가 완료되었습니다.")
    # 브라우저를 임의로 닫지 않음 (사용자가 직접 닫도록)