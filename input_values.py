import re
import time
from logger import log
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


def fill_receiver_info(driver, sender, receiver_name, base_addr, dtl_addr, contact, pickup_location, allpoint, gspoint, savings, card):
    """
    :param driver: Selenium WebDriver.
    :param sender: string, 보내는 사람 이름.
    :param receiver_name: string, 받으시는 분.
    :param base_addr: string, 주소.
    :param dtl_addr: string, 상세주소.
    :param contact: string, 전화번호 (예: '01012345678').
    :param pickup_location: string, 수령장소.
    :param allpoint: string, allpoint 정보.
    :param gspoint: string, gspoint 정보.
    :param savings: string, 적립금
    :param card: string, 카드 정보.
    """
    # 0) 체크박스 'chkRealSender'가 체크되어 있는지 확인하고, 필요하면 강제 클릭
    try:
        chk_real_sender = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chkRealSender"))
        )
        # 체크박스가 이미 선택되어 있는지 확인
        if not chk_real_sender.is_selected():
            driver.execute_script("arguments[0].click();", chk_real_sender)
            print("체크박스 'chkRealSender'를 강제로 선택하였습니다.")
        else:
            print("체크박스 'chkRealSender'는 이미 선택되어 있습니다.")
    except Exception as e:
        print("체크박스 'chkRealSender'를 찾거나 클릭하는 중 오류 발생:", e)
    # 0-1) 보내는 사람 입력 (실주문하시는 분 - 'dlv_real_send_name')
    try:
        real_sender_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dlv_real_send_name"))
        )
        real_sender_input.clear()
        real_sender_input.send_keys(sender)
        print(f"Real sender name set to: {sender}")
    except Exception as e:
        print("Error setting real sender name:", e)
    # 1) 받으시는 분
    try:
        rcvr_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "rcvrNm0"))
        )
        rcvr_input.clear()
        rcvr_input.send_keys(receiver_name)
        print(f"Receiver name set to: {receiver_name}")
    except Exception as e:
        print("Error setting receiver name:", e)
    # 2) 연락처 입력
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
    # 3) 수령장소 입력
    try:
        pickup_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dlvPickMsgCntnt0"))
        )
        pickup_input.clear()
        pickup_input.send_keys(pickup_location)
        print(f"Pickup location set to: {pickup_location}")
    except Exception as e:
        print("Error setting pickup location:", e)

    apply_allpoint_logic(driver, allpoint)
    apply_gspoint_logic(driver, gspoint)
    apply_savings_logic(driver, savings)


    select_card_option(driver, card)


    # 4) 쿠폰 조회 및 적용 버튼 클릭
    # ── 쿠폰 버튼을 누르기 전에 더블‑쿠폰 수량 확인 ──
    try:
        dbl_qty_elem = driver.find_element(By.ID, "prdDblCpnQty1")
        dbl_qty = int(dbl_qty_elem.text.strip())
    except Exception:
        dbl_qty = 0  # 요소를 찾지 못하거나 파싱 실패 시 0으로 간주

    if dbl_qty >= 1:
        # 버튼이 클릭 가능해질 때까지 대기 후 클릭
        coupon_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "span.gs-btn.mid.vmid > button[onclick*='openCoupon']"
            ))
        )
        main_handle = driver.current_window_handle
        coupon_btn.click()
        print("쿠폰 조회 및 적용 버튼을 클릭했습니다.")

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

        # 1) 테이블의 tbody 열을 기다려 가져오기
        tbody = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
        )
        # 2) 모든 상품 행(<tr>)을 순회
        rows = tbody.find_elements(By.CSS_SELECTOR, "tr")
        for idx, row in enumerate(rows, start=1):
            print(f"--- Row {idx} ---")
            for coupon_type, select_name in [
                # ("일반쿠폰", "selectGenrlCpn"),
                ("더블쿠폰", "selectDblCpn"),
            ]:
                try:
                    sel_elem = row.find_element(By.CSS_SELECTOR, f"select[name='{select_name}']")
                    if sel_elem:
                        select = Select(sel_elem)
                        opts = select.options
                        if len(opts) >= 2:
                            select.select_by_index(1)
                            print(f"{coupon_type}: '{opts[1].text}' 선택 완료")
                        else:
                            print(f"{coupon_type}: 옵션이 2개 미만입니다. ({len(opts)}개)")
                except Exception as e:
                    print(f"{coupon_type} 처리 중 오류 발생:", e)

        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnCouponApply"))
            )
            try:
                btn.click()  # 일반 클릭
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            print("‘쿠폰 사용하기’버튼을 클릭했습니다.")
        except Exception as e:
            print("‘쿠폰 사용하기’버튼 클릭 실패:", e)

        driver.switch_to.window(main_handle)
    else:
        # 수량이 2가 아니면 쿠폰 로직 건너뜀
        print(f"더블 쿠폰 수량이 {dbl_qty}이므로 쿠폰 조회/적용을 건너뜁니다.")

    # 4) 우편번호 찾기 팝업 및 주소 입력 (기존 코드 그대로)
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

def apply_point_logic(driver, current_span_id, input_id, checkbox_id, point_value, point_label):
    """
    주어진 포인트 관련 요소들(current_span_id, input_id, checkbox_id)을 사용하여,
    point_value에 따라 값을 입력하거나 체크박스를 선택합니다.

    - point_value가 -1이면 현재 보유 포인트가 0이 아닐 경우 체크박스를 선택합니다.
    - 그 외에는 point_value와 현재 보유 포인트 중 더 작은 값을 입력합니다.

    :param driver: Selenium WebDriver.
    :param current_span_id: 현재 보유 포인트를 담고 있는 <span>의 id (예: "gsAllPntAccmAmt" 또는 "gsnpntAccmAmt")
    :param input_id: 포인트 입력창의 id (예: "dc_txt_gsallpnt_accm_amt" 또는 "dc_txt_gsnpnt_accm_amt")
    :param checkbox_id: 모두 사용 체크박스의 id (예: "gsallpnt_accm_chk" 또는 "gsnpnt_accm_chk")
    :param point_value: int, 입력할 포인트 값 (-1이면 모두 사용)
    :param point_label: string, 디버깅용 라벨 (예: "GS ALL 포인트" 또는 "GS POINT")
    """
    try:
        span_elem = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, current_span_id))
        )
        current_text = span_elem.text.strip()  # 예: "123P"
        current_point = int(re.sub(r'\D', '', current_text))
        print(f"[{point_label}] 현재 포인트: {current_point}")
    except Exception as e:
        print(f"[{point_label}] 포인트를 읽는 중 오류 발생:", e)
        return

    if current_point == 0:
        print(f"[{point_label}] 현재 보유 포인트가 0이므로 입력하지 않습니다.")
        return

    if int(point_value) == -1:
        try:
            checkbox = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, checkbox_id))
            )
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"[{point_label}] 모두 사용 체크박스를 선택했습니다.")
            else:
                print(f"[{point_label}] 모두 사용 체크박스가 이미 선택되어 있습니다.")
        except Exception as e:
            print(f"[{point_label}] 모두 사용 체크박스를 처리하는 중 오류 발생:", e)
    else:
        point_value = int(point_value)
        value_to_input = point_value if point_value <= current_point else current_point
        try:
            input_elem = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, input_id))
            )
            input_elem.clear()
            input_elem.send_keys(str(value_to_input))
            print(f"[{point_label}] 입력창에 {value_to_input}원을 입력했습니다.")
        except Exception as e:
            print(f"[{point_label}] 입력창에 값을 입력하는 중 오류 발생:", e)

def apply_allpoint_logic(driver, allpoint):
    apply_point_logic(driver,
                      current_span_id="gsAllPntAccmAmt",
                      input_id="dc_txt_gsallpnt_accm_amt",
                      checkbox_id="gsallpnt_accm_chk",
                      point_value=allpoint,
                      point_label="GS ALL 포인트")

def apply_gspoint_logic(driver, gspoint):
    apply_point_logic(driver,
                      current_span_id="gsnpntAccmAmt",
                      input_id="dc_txt_gsnpnt_accm_amt",
                      checkbox_id="gsnpnt_accm_chk",
                      point_value=gspoint,
                      point_label="GS POINT")


# 적립금 입력 로직 추가
def apply_savings_logic(driver, savings):
    try:
        juklib_tr = driver.find_element(By.ID, "div_juklib")
        if not juklib_tr.is_displayed():
            print("[적립금] 비활성화 상태 (is_displayed=False) - 입력 생략")
            return
    except Exception as e:
        print("[적립금] div_juklib 찾는 중 오류 발생:", e)
        return

    try:
        input_elem = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "dcAccmDcAmtTxt"))
        )
        input_elem.clear()
        input_elem.send_keys(str(savings))
        print(f"[적립금] {savings}원을 입력했습니다.")
    except Exception as e:
        print("[적립금] 입력창에 값을 입력하는 중 오류 발생:", e)


def select_card_option(driver, card_value):
    """
    신용카드 결제 수단을 활성화한 후 카드 옵션 select 박스에서 지정된 card_value를 선택합니다.

    Steps:
      1. 카드 선택 라디오 버튼 (id="cardChoice")가 선택되지 않았다면 클릭
      2. 카드 탭 영역 (id="card_tab_area")이 보일 때까지 기다린 후 탭 헤더를 클릭하여 활성화
      3. 카드 옵션 select 박스 (id="pay_slt_card")에서 전달받은 card_value와 일치하는 옵션을 선택

    :param driver: Selenium WebDriver
    :param card_value: 선택할 카드 옵션의 value값 (예: "POLARIS_LGLG")
    """
    # Step 1: 카드 라디오 버튼 클릭 (필요 시)
    try:
        label_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='chk-method-other']"))
        )
        label_elem.click()
        print("라디오 버튼 대신 레이블 'chk-method-other'를 클릭했습니다.")
    except Exception as e:
        print("라벨 'chk-method-other' 클릭 중 오류 발생:", e)

    # Step 2: 카드 탭 활성화
    try:
        card_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='cardChoice']"))
        )
        card_label.click()
        print("신용카드 라벨을 클릭하였습니다.")
    except Exception as e:
        print("신용카드 라벨 클릭 중 오류 발생:", e)

    # Step 3: 카드 옵션 선택
    try:
        select_elem = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "pay_slt_card"))
        )
        select_box = Select(select_elem)
        select_box.select_by_visible_text(card_value)
        print(f"카드 옵션 '{card_value}'의 텍스트를 선택하였습니다.")
    except Exception as e:
        print("카드 옵션 선택 중 오류 발생:", e)