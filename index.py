import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter import messagebox

import config
from automation import run_automation
from logger import set_log_widget


def on_run_button_click():
    log_text.delete("1.0", tk.END)
    button_run.config(text="실행중...", state="disabled")
    root.update_idletasks()

    csv_url = entry_csv_url.get().strip()
    if not csv_url:
        messagebox.showwarning("입력 오류", "CSV URL을 입력해주세요.")
        button_run.config(text="실행", state="normal")
        return

    try:
        run_automation(csv_url)
        print("모든 작업이 완료되었습니다.")
        messagebox.showinfo("완료", "모든 작업이 완료되었습니다.")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")
        messagebox.showerror("에러", f"실행 중 오류 발생: {e}")

    button_run.config(text="실행", state="normal")

def on_exit_button_click():
    root.quit()

root = tk.Tk()
root.title("Auto Purchase")
root.geometry("500x380")

var_enuri = tk.BooleanVar(master=root)
var_enuri.set(getattr(config, "enuri_flag", False))

def on_enuri_toggle():
    flag = var_enuri.get()
    config.enuri_flag = flag
    print(f"[UI] 에누리 체크 상태: {flag}")

label = tk.Label(root, text="CSV URL:")
label.pack(pady=5)

entry_csv_url = tk.Entry(root, width=50)
entry_csv_url.insert(0, "https://docs.google.com/spreadsheets/d/e/2PACX-1vRSQv8S1GKaUtgYaMOpBeGB7CmV_574soJxMDUOBvWTQpSCXOEZwxT7L5y_kWu5wYoqflpRVoKLK8SK/pub?gid=0&single=true&output=csv")
entry_csv_url.pack(pady=5)

check_enuri = tk.Checkbutton(root, text="에누리", variable=var_enuri, command=on_enuri_toggle)
check_enuri.pack(pady=5)

log_text = scrolledtext.ScrolledText(root, height=10, width=60)
log_text.pack(pady=5)

set_log_widget(log_text)

button_run = tk.Button(root, text="실행", command=on_run_button_click)
button_run.pack(pady=10)

button_exit = tk.Button(root, text="프로그램 종료", command=on_exit_button_click)
button_exit.pack(pady=5)

root.mainloop()