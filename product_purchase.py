import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


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


def click_first_product_in_enuri_list(driver):
    try:
        first_product = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.goods-bundle li.prodItem a"))
        )
        if not first_product:
            print("[오류] 첫 번째 상품이 존재하지 않습니다.")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_product)
        driver.execute_script("arguments[0].click();", first_product)
        print("첫 번째 상품 클릭 완료")
        return True
    except TimeoutException:
        print("[오류] 첫 번째 상품을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"[오류] 첫 번째 상품 클릭 실패: {e}")
        return False


def click_mini_vip_buy_button(driver):
    try:
        # 1. miniVIP div가 is--visible 상태가 될 때까지 기다림
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#miniVIP.is--visible"))
        )
        print("miniVIP가 보이기 시작했습니다.")

        # 2. miniVIP 안에 있는 구매하기 링크가 클릭 가능해질 때까지 기다림
        buy_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#miniVIP.is--visible a.product__link--shop"))
        )
        print("구매하기 버튼이 클릭 가능해졌습니다.")

        # 3. 구매하기 버튼 클릭
        buy_button.click()
        print("구매하기 버튼 클릭 완료")

    except TimeoutException:
        print("에러: miniVIP나 구매하기 버튼을 찾지 못했습니다.")


def navagate_to_enuri2(driver, product_name):
    enuri_url = f"https://www.enuri.com/search.jsp?keyword={product_name}"
    driver.get(enuri_url)
    time.sleep(2)

    apply_gsshop_filter(driver)
    # 상품 리스트 중 첫 번째 상품 클릭
    time.sleep(1)
    if not click_first_product_in_enuri_list(driver):
        return False

    click_mini_vip_buy_button(driver)

    return True



# GS SHOP 필터를 적용하는 함수
def apply_gsshop_filter(driver):
    wait = WebDriverWait(driver, 10)

    try:
        # 1. 쇼핑몰 선택 버튼 클릭
        select_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".list-filter__btn--select")))
        driver.execute_script("arguments[0].click();", select_btn)
        print("쇼핑몰 선택 버튼(JS 강제) 클릭 완료")

        # 2. 쇼핑몰 리스트 표시 대기
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".lay-mall__list")))
        print("쇼핑몰 리스트 표시 완료")

        # GS SHOP label 찾기
        lay_mall_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.lay-mall__list")))
        li_elements = lay_mall_list.find_elements(By.CSS_SELECTOR, "li.mirror-attrs")

        found = False
        for li in li_elements:
            try:
                label = li.find_element(By.TAG_NAME, "label")
                shop_name = label.get_attribute("title")
                if shop_name.strip() == "GS SHOP":
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)
                    driver.execute_script("arguments[0].click();", label)
                    print("GS SHOP 항목(label) 강제 클릭 완료")
                    found = True
                    break
            except Exception as e:
                print(f"[오류] li 요소 처리 중 예외 발생: {e}")

        if not found:
            print("[오류] GS SHOP label을 찾을 수 없습니다.")
            driver.save_screenshot("gsshop_label_not_found.png")
            return

        # 4. 적용 버튼 클릭
        apply_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn__group .btn__apply")))
        driver.execute_script("arguments[0].click();", apply_btn)
        print("적용 버튼 클릭 완료")

        close_coupon_popup(driver)

        print(f"url: {driver.current_url}")
        WebDriverWait(driver, 10).until(
            EC.url_contains("with.gsshop.com")
        )

    except Exception as e:
        print(f"GS SHOP 필터 적용 중 오류 발생: {e}")
        print(f"현재 페이지 URL: {driver.current_url}")
        # driver.save_screenshot("apply_gsshop_filter_error.png")
        print("스크린샷 저장: apply_gsshop_filter_error.png")



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

    close_coupon_popup(driver)

    print(f"url: {driver.current_url}")
    WebDriverWait(driver, 10).until(
        EC.url_contains("with.gsshop.com")
    )

def order_product(driver, quantity, option_name):
    close_coupon_popup(driver)

    if (option_name is not None) and (option_name != ""):
        try:
            wait = WebDriverWait(driver, 10)
            option_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#option1Div .option_name"))
            )
            matched = False
            for opt in option_elements:
                full_text = opt.get_attribute('innerText').strip()
                print(f"옵션 텍스트: {full_text}")
                if option_name in full_text:
                    try:
                        parent_a_tag = opt.find_element(By.XPATH, "..")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_a_tag)
                        driver.execute_script("arguments[0].click();", parent_a_tag)
                        print(f"옵션 '{full_text}' 선택 완료 (강제 클릭)")
                        matched = True
                        break
                    except Exception as e_click:
                        print(f"옵션 '{full_text}' 클릭 실패: {e_click}")

            # 옵션 클릭 후 새로 생긴 영역에서 수량 input 찾기
            try:
                print("선택한 옵션 수량 설정 시도 중...")
                # 새로 추가된 옵션의 input을 찾음
                dl_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "dl.pro_view"))
                )
                qty_input = dl_element.find_element(By.CSS_SELECTOR,
                                                    ".sel_in input[type='text']")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", qty_input)

                if qty_input.is_enabled() and qty_input.is_displayed():
                    qty_input.click()
                    qty_input.send_keys(Keys.CONTROL, "a")
                    qty_input.send_keys(Keys.BACKSPACE)
                    qty_input.send_keys(str(quantity))
                    print(f"수량을 {quantity}개로 설정했습니다. (옵션 있는 상품)")
                else:
                    print("수량 입력창이 비활성화 상태입니다. JavaScript로 값 설정 시도")
                    driver.execute_script("arguments[0].value = arguments[1];", qty_input, str(quantity))
                    print(f"수량을 {quantity}개로 JS로 설정했습니다.")
            except Exception as e_qty:
                print(f"수량 설정 중 오류 발생: {e_qty}")


            if not matched:
                print(f"옵션 이름 '{option_name}'에 해당하는 항목을 찾을 수 없습니다.")
        except Exception as e:
            print(f"옵션 선택 중 오류 발생 또는 옵션 없음: {e}")
    else :
        try:
            qty_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "tabOptCntSub"))
            )
            qty_input.click()
            qty_input.send_keys(Keys.CONTROL, "a")
            qty_input.send_keys(Keys.BACKSPACE)
            qty_input.send_keys(str(quantity))
            print(f"수량을 {quantity}개로 설정했습니다.")
        except Exception as e:
            print(f"수량 설정 중 오류 발생: {e}")

    try:
        order_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ordButtn"))
        )
        order_button.click()
        print("바로구매 버튼을 클릭했습니다.")
    except Exception as e:
        print(f"바로구매 버튼 클릭 중 오류 발생: {e}")

def close_coupon_popup(driver):
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

# https://with.gsshop.com/cust/alia/popup/aliaCpnPop.gs?goUrl=%2Fprd%2Fprd.gs%3Fprdid%3D26668720%26vodFlag%3DN%26utm_source%3Dprice%26utm_medium%3Daffiliate%26utm_campaign%3Denuri%26media%3DPg%26fromWith%3DY