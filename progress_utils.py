# progress_utils.py
root_window = None  # 추가

def set_progress_text_widget(widget, root):
    global progress_text, root_window
    progress_text = widget
    root_window = root

def update_progress(message):
    global progress_text, root_window

    if progress_text is not None and root_window is not None:
        try:
            if progress_text.winfo_exists():
                root_window.after(0, _append_message, message)
            else:
                print(message)
        except Exception as e:
            print(f"[progress error] {e}")
            print(message)
    else:
        print(message)

def _append_message(message):
    """메인 스레드에서만 호출되어야 하는 UI 업데이트 함수"""
    try:
        progress_text.configure(state="normal")
        progress_text.insert("end", message + "\n")
        progress_text.see("end")
        progress_text.configure(state="disabled")

    except Exception as e:
        print(f"[progress error in _append_message] {e}")
        print(message)