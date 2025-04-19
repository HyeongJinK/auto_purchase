from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def close_gsall_popup(driver, wait_sec: int = 3) -> None:
    """
    GS ALL 멤버십 동의 팝업이 떠‑있으면 ‘닫기’ 버튼을 눌러 닫는다.
    (div#gsrIntgLayer  ➜  button#btnClose)

    :param driver: Selenium WebDriver
    :param wait_sec: 레이어를 기다리는 최대 시간(초)
    """
    try:
        # div#gsrIntgLayer 가 나타날 때까지 잠깐 대기
        layer = WebDriverWait(driver, wait_sec).until(
            EC.visibility_of_element_located((By.ID, "gsrIntgLayer"))
        )

        # 자식 버튼 #btnClose 찾기
        close_btn = layer.find_element(By.ID, "btnClose")

        # 안전하게 JS 클릭
        driver.execute_script("arguments[0].click();", close_btn)
        print("🔕 GS ALL 팝업을 닫았습니다.")
    except (TimeoutException, NoSuchElementException):
        # 팝업이 없거나 이미 사라진 경우
        print("ℹ️ GS ALL 팝업이 표시되지 않았습니다.")