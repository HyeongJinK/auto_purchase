# progress_utils.py
root_window = None  # 추가

def set_progress_text_widget(widget, root):
    global progress_text, root_window
    progress_text = widget
    root_window = root
    # 태그 색상 설정
    progress_text.tag_configure('progress', foreground='green')
    progress_text.tag_configure('error', foreground='red')

def update_progress(message, tag='progress'):
    global progress_text, root_window

    if progress_text is not None and root_window is not None:
        try:
            if progress_text.winfo_exists():
                root_window.after(0, _append_message, message, tag)
            else:
                print(message)
        except Exception as e:
            print(f"[progress error] {e}")
            print(message)
    else:
        print(message)

def _append_message(message, tag='progress'):
    """메인 스레드에서만 호출되어야 하는 UI 업데이트 함수"""
    try:
        # 상태 활성화
        progress_text.configure(state="normal")
        progress_text.insert("end", message + "\n", tag)
        progress_text.see("end")
        progress_text.configure(state="disabled")
    except Exception as e:
        print(f"[progress error in _append_message] {e}")
        print(message)