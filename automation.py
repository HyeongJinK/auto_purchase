from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config
from csv_utils import get_user_info_from_public_csv
from input_values import fill_receiver_info
from login_captcha import login_and_navigate, solve_captcha_with_retries
from popup_close import close_gsall_popup
from product_purchase import navigate_to_product, order_product, navigate_to_enuri, navagate_to_enuri2
from pwChgPopClose import pwChgPopClose

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
        product_name = values[3]
        option_name = values[4]
        quantity = int(values[5])  # 수량은 정수로
        sender = values[6]  # 보내는 사람
        receiver_name = values[7]
        base_addr = values[8]
        dtl_addr = values[9]
        contact = values[10]
        pickup_location = values[11]
        coupon = values[12]  #  쿠폰
        allpoint = values[13]  # allpoint
        gspoint = values[14]  # gspoint
        savings = values[15]  # 적립금
        card = values[16]  # 카드

        try:
            # 로그인
            login_and_navigate(global_driver, user_id, user_password)

            # 캡차
            candidate, value = solve_captcha_with_retries(global_driver, max_retries=3)

            if candidate:
                print(f"[User {idx}] Captcha success: {candidate}, {value}")
                close_gsall_popup(global_driver)
                pwChgPopClose(global_driver)

                # 상품 이동: 에누리 모드일 경우 Enuri 사이트로, 아니면 기본 navigate_to_product 호출
                next_step = True

                if getattr(config, "enuri_flag", False):
                    print("[User {idx}] 에누리 모드 활성화")
                    next_step = navagate_to_enuri2(global_driver, product_name)
                else:
                    print(f"[User {idx}] 일반 모드")
                    navigate_to_product(global_driver, product_id)
                if next_step:

                    # 주문
                    order_product(global_driver, quantity, option_name)
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
                        savings = savings,
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

def main():
    URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vRBO4Sk5XtsHMHsE8KhOtgqnTUZLP3snTjSfQ6GbVIqNQ_j-h03TmVuBMSzq4ymUg/pub?gid=65743775&single=true&output=csv")
    run_automation(URL)
    input("..... ").strip()


if __name__ == "__main__":
    main()