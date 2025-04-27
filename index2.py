import csv
import io
import re
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests
from openpyxl.styles import PatternFill, Font
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from logging_p import setup_logger
from login_captcha import login_and_navigate, solve_captcha_with_retries
from popup_close import close_gsall_popup
from pwChgPopClose import pwChgPopClose

logger = setup_logger("make_execl")  # 추가된 로거 설정)


# ──────────────────────────────────────────────────────────────────────────
# ── CSV Utilities ──
# 1. 구글 시트(CSV) 읽어서 (id, pw) 튜플 리스트 반환
# ──────────────────────────────────────────────────────────────────────────
def fetch_credentials(csv_url: str, start_row: int = 3) -> List[Tuple[str, str]]:
    resp = requests.get(csv_url, timeout=15)
    resp.raise_for_status()

    csv_text = resp.content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(csv_text))

    credentials: List[Tuple[str, str, str]] = []
    for idx, row in enumerate(reader, start=1):
        if idx < start_row:
            continue  # 헤더/비어있는 행 건너뜀

        # 0‑based 인덱스로 3열=2, 4열=3
        if len(row) >= 5:
            name = row[2].strip()
            user_id = row[3].strip()
            user_pw = row[4].strip()
            if user_id and user_pw:
                credentials.append((name, user_id, user_pw))

    return credentials


# ──────────────────────────────────────────────────────────────────────────
# ── Parsers ──
def extract_membership_info(driver, wait_sec: int = 5) -> tuple[str, int] | None:
    """
    리얼 멤버십 페이지에서 등급(VVIP‧VIP 등)과
    '6개월간 xx회' 구매 회수를 추출해서 돌려준다.
    반환: (grade_str, purchase_cnt)  ── 예) ('VVIP', 35)
    실패 시 None
    """
    try:
        # 1) 등급 추출 ───────────────────────────────────────────
        desc_el = WebDriverWait(driver, wait_sec).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".my-membership-info .my-grade-desc")
            )
        )
        # <strong>…</strong> 중 마지막 strong 이 등급
        grade_elements = desc_el.find_elements(By.TAG_NAME, "strong")
        grade = grade_elements[-1].text.strip() if grade_elements else "등급 정보 없음"

        # 2) '6개월간 xx회' 문구가 들어있는 li 찾기 ────────────────
        li_list = driver.find_elements(
            By.CSS_SELECTOR, ".my-membership-info ul.my-grade-up-info li"
        )
        purchase_cnt = None
        try:
            second_li = li_list[1]
            m = re.search(r"6개월간\s*(\d+)\s*회", second_li.text)
            if m:
                purchase_cnt = int(m.group(1))
        except IndexError:
            purchase_cnt = 0  # 6개월간 구매 내역이 없을 경우 0으로 설정

        logger.info(f"회원 등급: {grade}, 구매 회수: {purchase_cnt}")
        return grade, purchase_cnt
    except Exception as e:
        logger.info(f"⚠️ 회원 정보 추출 실패: {e}")
        return ("등급 정보 없음", 0)


def extract_asset_values(driver, wait_sec: int = 5) -> dict[str, str] | None:
    """
    자산(적립금) 페이지의 <ul id="my‑asset‑info"> 영역에서
    - 적립금
    - 이벤트적립금
    - GS ALL 포인트
    값을 문자 그대로 딕셔너리로 반환.
      예) {'적립금': '158,268원',
           '이벤트적립금': '0원',
           'GS ALL 포인트': '0P'}
    못 얻으면 None
    """
    try:
        WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((By.ID, "my-asset-info"))
        )
        result: dict[str, str] = {}
        li_elems = driver.find_elements(By.CSS_SELECTOR, "#my-asset-info > li")

        for li in li_elems:
            label = li.find_element(By.TAG_NAME, "em").text.strip()
            value = li.find_element(By.CSS_SELECTOR, "span strong").text.strip()
            if label in ("적립금", "이벤트적립금", "GS ALL 포인트"):
                result[label] = value

        logger.info(f"자산 추출 완료")
        return result if result else None

    except Exception as e:
        logger.info(f"⚠️ 자산 값 추출 실패: {e}")
        return None


def parse_point_history_from_html(driver, current_balance: int, wait_sec: int = 5) -> dict[str, int]:
    """
    자산 페이지에서 포인트 적립/사용 내역을 분리하여 반환.
    - 적립: (적립일자, 사용기한, 금액)
    사용기록 대신 현재 적립금 기준으로 남은 적립내역을 계산.
    """

    WebDriverWait(driver, wait_sec).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
    )

    accruals = []

    try:
        try:
            nav_div = WebDriverWait(driver, wait_sec).until(
                EC.presence_of_element_located((By.ID, "pageNavigation"))
            )
            page_links = nav_div.find_elements(By.CSS_SELECTOR, "a[data-index]")
            max_page = max([int(link.get_attribute("data-index")) for link in page_links]) if page_links else 1
        except Exception:
            max_page = 1

        for page in range(1, max_page + 1):
            if page != 1:
                try:
                    nav_div = WebDriverWait(driver, wait_sec).until(
                        EC.presence_of_element_located((By.ID, "pageNavigation"))
                    )
                    link = nav_div.find_element(By.CSS_SELECTOR, f"a[data-index='{page}']")
                    driver.execute_script("arguments[0].click();", link)
                    WebDriverWait(driver, wait_sec).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
                    )
                except Exception as e:
                    logger.info(f"페이지 {page} 이동 실패: {e}")
                    continue

            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

            for row in rows:
                try:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) < 3:
                        continue

                    date_text = tds[0].text.strip().split("\n")[0].strip()
                    amount_text = tds[2].text.strip()

                    action_date = datetime.strptime(date_text, "%Y.%m.%d").date()
                    amount = int(amount_text.replace(",", "").replace("원", ""))

                    expire_date = None
                    try:
                        expire_p = tds[0].find_element(By.CSS_SELECTOR, "p.color-lightgray")
                        expire_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", expire_p.text)
                        if expire_match:
                            expire_date = expire_match.group(1)
                    except Exception:
                        pass

                    if amount > 0:
                        accruals.append((action_date, expire_date, amount))

                except Exception as e:
                    logger.info(f"행 파싱 중 에러: {e}")
                    continue

    except Exception as e:
        logger.info(f"포인트 내역 파싱 실패: {e}")
        return {}

    # 최신 적립부터 소진
    accruals_sorted = sorted(accruals, key=lambda x: x[0], reverse=True)

    used_accruals = []

    for accrual_date, expire_date, amount in accruals_sorted:
        if current_balance <= 0:
            break

        if amount <= current_balance:
            used_amount = amount
            current_balance -= amount
        else:
            used_amount = current_balance
            current_balance = 0
        used_accruals.append((accrual_date, expire_date, used_amount))

    # 사용기한별로 합산
    summed_by_expire = defaultdict(int)
    for accrual_date, expire_date, amount in used_accruals:
        if expire_date:
            summed_by_expire[expire_date] += amount

    # 오름차순 정렬 추가
    sorted_summed_by_expire = dict(sorted(summed_by_expire.items(), key=lambda x: x[0]))

    return sorted_summed_by_expire


# ────────────────────────────────────────────────────────────────────
# 2. 로그인 실행
# ────────────────────────────────────────────────────────────────────

URLS = {
    "member": "https://www.gsshop.com/cust/rlmemshp/main.gs?lseq=415248&parent=myshoppc-real",
    "asset": "https://www.gsshop.com/cust/myshop/accm.gs?currPageNo=1"
}


def login(driver, name: str, user_id: str, user_pw: str):
    logger.info(f"🔑 로그인 시도: {user_id} pw: {user_pw}")

    # ── 새 탭을 열어 각 계정별 작업을 분리 ─────────────────────────
    try:
        # Selenium 4 권장 방식
        driver.switch_to.new_window('tab')
    except Exception:
        # Selenium <4 호환 (fallback)
        driver.execute_script("window.open('about:blank','_blank');")
        driver.switch_to.window(driver.window_handles[-1])

    login_and_navigate(driver, user_id, user_pw)  # None 대신 실제 드라이버 객체를 넣어야 함
    candidate, value = solve_captcha_with_retries(driver, max_retries=5)

    if candidate:
        close_gsall_popup(driver)
        try:
            pwChgPopClose(driver)
        except Exception as e:
            logger.info(f"비밀번호 변경 팝업 처리 실패: {e}")


        try:
            # ── 로그인 후 마이페이지(실멤버십)로 이동 ─────────────────────
            driver.get(URLS["member"])
            WebDriverWait(driver, 10).until(
                EC.url_contains("cust/rlmemshp")
            )

            logger.info(f"📄 회원 페이지로 이동 완료 → {URLS['member']}")

            grade, cnt = extract_membership_info(driver)

            # ── 자산(적립금) 페이지로 이동 ───────────────────────────
            driver.get(URLS["asset"])
            WebDriverWait(driver, 10).until(
                EC.url_contains("cust/myshop/accm")
            )
            logger.info(f"📄 자산 페이지 이동 완료 → {URLS['asset']}")

            asset_info = extract_asset_values(driver)
            current_balance = int(asset_info.get("적립금", "0").replace(",", "").replace("원", "").strip())
            hist = parse_point_history_from_html(driver, current_balance)

            # 사용 끝난 탭 닫기
            driver.close()
            try:
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
                    logger.info("기존 창으로 성공적으로 전환됨.")
                else:
                    logger.info("⚠️ 남아 있는 창이 없어 전환을 생략합니다.")
            except Exception as e:
                logger.info(f"⚠️ 창 전환 실패: {e}")

            return {
                "NAME": name,
                "ID": user_id,
                "적립금": asset_info.get("적립금", "0원"),
                "이벤트적립금": asset_info.get("이벤트적립금", "0원"),
                "GS ALL 포인트": asset_info.get("GS ALL 포인트", "0P"),
                "회원등급": grade,
                "6개월 주문": cnt,
                "expiries": hist
            }
        except Exception as e:
            logger.info(f"⛔ {user_id} 처리 실패: {e}")
            return None


# ────────────────────────────────────────────────────────────────────
# 2) 메인 루프 – 모든 사용자 결과 누적
# ────────────────────────────────────────────────────────────────────
def create_driver():
    chrome_options = Options()
    return webdriver.Chrome(options=chrome_options)


def save_to_excel(results, output_path):
    # ──────────────────────────────────
    # 3) DataFrame 생성
    # ──────────────────────────────────
    all_expiry_dates = set()
    for info in results:
        all_expiry_dates.update(info["expiries"].keys())

    expiry_cols = sorted(all_expiry_dates)          # 빠른 날짜순
    base_cols = ["NAME", "ID", "적립금", "이벤트적립금", "GS ALL 포인트", "회원등급", "6개월 주문"]
    full_cols = base_cols + expiry_cols             # 최종 컬럼 순서

    rows = []
    for info in results:
        row = {col: "" for col in full_cols}
        for bc in base_cols:
            row[bc] = info.get(bc, "")

        for exp in expiry_cols:
            row[exp] = info["expiries"].get(exp, 0)

        rows.append(row)

    df = pd.DataFrame(rows)[full_cols]

    # ──────────────────────────────────
    # 4) Excel 저장
    # ──────────────────────────────────
    output_path = Path(output_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GS 데이터")

        ws = writer.sheets["GS 데이터"]

        # 제목 색상 지정
        header_fill = PatternFill(start_color="FFDCE6F1", end_color="FFDCE6F1", fill_type="solid")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = Font(bold=True)

        # 숫자 형식 적용 (3자리마다 콤마)
        comma_fmt = "#,##0"
        # 3번째 열부터 마지막 열까지 적용
        for col in range(3, ws.max_column + 1):
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=col)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = comma_fmt


def run_all(csv_url: str, out_excel: str = "gs_assets.xlsx"):
    logger.info(f"수집 시작 - URL: {csv_url}")
    creds = fetch_credentials(csv_url)
    if not creds:
        logger.warning("CSV에 유효한 계정이 없습니다.")
        logger.info("CSV에 유효한 계정이 없습니다.")
        return

    driver = create_driver()

    results = []

    for name, uid, pw in creds:
        info = login(driver, name, uid, pw)
        if info:
            results.append(info)

    if not results:
        logger.warning("📛 수집된 결과가 없습니다.")
        logger.info("📛 수집된 결과가 없습니다.")
        return

    save_to_excel(results, out_excel)

    logger.info(f"✅ 결과 저장 완료 → {Path(out_excel).resolve()}")
    logger.info(f"✅ 결과 저장 완료 → {Path(out_excel).resolve()}")


def main():
    URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vR_u3fMoCtuUVO7o1pf-GOr1pkrL_fJTx06JVY0xLgGEWz_Dah65qs8VJpU0tNMXQ/pub?gid=1943453742&single=true&output=csv")
    run_all(URL, f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    input("..... ").strip()


if __name__ == "__main__":
    main()
