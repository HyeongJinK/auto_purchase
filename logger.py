# logger.py
log_text_widget = None

def set_log_widget(widget):
    """
    UI에서 생성한 ScrolledText 위젯을 등록합니다.
    한 번만 호출해 주면 이후부터 log()가 이 위젯에 쓰기를 시도합니다.
    """
    global log_text_widget
    log_text_widget = widget

def log(message):
    """
    등록된 ScrolledText 위젯에 메시지를 출력하거나,
    위젯이 없으면 console 출력으로 fallback 합니다.
    """
    try:
        if log_text_widget:
            log_text_widget.insert('end', message + '\n')
            log_text_widget.see('end')
            # log_text_widget.update()
        else:
            print(message)
    except Exception:
        print(message)