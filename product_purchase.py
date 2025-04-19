import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

def navigate_to_product(driver, product_id):
    product_url = f"https://www.gsshop.com/prd/prd.gs?prdid={product_id}"
    driver.get(product_url)
    print(f"Navigated to product page: {product_url}")

def wait_for_table_update(driver, table_before, max_wait_time=10):
    """테이블이 업데이트될 때까지 대기"""
    print("테이블 업데이트 대기 중...")

    # 방법 1: 로딩 인디케이터 감지 (있는 경우)
    try:
        loading = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
        )
        WebDriverWait(driver, max_wait_time).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
        )
        print("로딩 완료 감지됨")
        time.sleep(0.5)  # 로딩 후 추가 안정화 시간
        return
    except:
        print("로딩 인디케이터를 찾을 수 없음, 테이블 변경 감지로 전환")

    # 방법 2: 테이블 내용 변경 감지
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            current_table = driver.find_element(By.CSS_SELECTOR, ".tb-compare__list tbody").get_attribute('innerHTML')
            if current_table != table_before:
                print("테이블 업데이트 감지됨")
                time.sleep(0.5)  # 추가 안정화 시간
                return
        except StaleElementReferenceException:
            # StaleElementReferenceException이 발생하면 테이블이 업데이트된 것
            print("StaleElementReference 예외 발생 - 테이블이 업데이트됨")
            time.sleep(0.5)
            return
        except Exception as e:
            print(f"테이블 확인 중 오류: {e}")
        time.sleep(0.5)

    # 시간 초과 시 마지막 대기
    print("테이블 업데이트 대기 시간 초과, 계속 진행")
    time.sleep(1.5)  # 안전을 위한 최소 대기시간

def navigate_to_enuri(driver, product_id):
    enuri_url = f"https://www.enuri.com/detail.jsp?modelno={product_id}"
    driver.get(enuri_url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # 필터 적용 전 테이블 상태 저장
    try:
        table_before = driver.find_element(By.CSS_SELECTOR, ".tb-compare__list tbody").get_attribute('innerHTML')
    except:
        table_before = ""

    # 1. 필터의 쇼핑몰 버튼 클릭 (팝업이 닫혀있는 경우)
    try:
        shop_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#filter_select .filter__btn--shop")
        ))
        shop_btn.click()
        print("쇼핑몰 필터 버튼 클릭됨")
    except:
        print("쇼핑몰 필터 팝업이 이미 열려있거나 버튼을 찾을 수 없음")

    # 2. 팝업 레이어가 표시될 때까지 대기
    wait.until(EC.visibility_of_element_located((By.ID, "mall_layer")))
    print("필터 팝업 레이어 표시됨")

    # 3. GS SHOP 체크박스 선택
    gsshop_checkbox = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "label[for='chkSELECT_SHOP_75']")
    ))
    gsshop_checkbox.click()
    print("GS SHOP 체크박스 선택됨")

    # 4. 적용 버튼 클릭
    apply_btn = wait.until(EC.element_to_be_clickable(
        (By.ID, "mall-layer-apply")
    ))
    driver.execute_script("arguments[0].click();", apply_btn)
    print("적용 버튼 클릭됨")

    # 5. 팝업 닫힘 확인
    wait.until(EC.invisibility_of_element_located((By.ID, "mall_layer")))
    print("필터 적용 완료")

    # 6. 테이블 업데이트 대기 (두 가지 방법)
    wait_for_table_update(driver, table_before)

    try:
        # 필터 적용 후 첫 번째 상품의 구매 버튼 클릭
        wait = WebDriverWait(driver, 10)
        first_buy_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "table.tb-compare__list tbody tr:first-child")
        ))
        first_buy_btn.click()
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