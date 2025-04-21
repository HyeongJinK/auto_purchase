def pwChgPopClose(driver):
    original_handle = driver.current_window_handle
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "pwChgInfoPop.gs" in driver.current_url:
            driver.close()
            break  # 하나만 닫고 나와도 OK
    driver.switch_to.window(original_handle)
