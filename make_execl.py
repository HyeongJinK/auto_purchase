import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from index2 import run_all  # 위 리팩토링된 스크립트의 run_all 함수
from progress_utils import set_progress_text_widget, update_progress
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'default_url.txt')

def load_default_url():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    # if missing, write the hard-coded default and return it
    default = ("")
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(default)
    return default

class App:
    def __init__(self, root):
        self.root = root
        root.title("GS Shop Data Collector")

        tk.Label(root, text="CSV URL:").pack(padx=10, pady=(10,0), anchor="w")
        self.url_var = tk.StringVar(value=load_default_url())
        self.entry = tk.Entry(root, textvariable=self.url_var, width=80)
        self.entry.pack(padx=10, pady=5)

        progress_frame = tk.Frame(root)
        progress_frame.pack(padx=10, pady=(5,10), fill="both", expand=True)
        self.progress_text = tk.Text(progress_frame, height=10, state="disabled")
        self.progress_text.pack(fill="both", expand=True)

        # progress_text를 progress_utils에 등록
        set_progress_text_widget(self.progress_text, root)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        self.run_btn = tk.Button(btn_frame, text="실행", width=12, command=self.on_run)
        self.run_btn.pack(side="left", padx=5)
        self.exit_btn = tk.Button(btn_frame, text="종료", width=12, command=self.on_exit)
        self.exit_btn.pack(side="left", padx=5)

    def on_run(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "CSV URL을 입력해주세요.")
            return

        update_progress(f"실행 버튼 클릭 - 입력 URL: {url}")

        # 비활성화 & 상태 표시
        self.run_btn.config(state="disabled", text="실행 중...")
        self.entry.config(state="disabled")

        # 작업 스레드로 실행
        threading.Thread(target=self._worker, args=(url,), daemon=True).start()

    def _worker(self, url):
        # 파일명에 타임스탬프 붙여서 저장
        out_name = f"assets_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        update_progress(f"작업 시작 - 저장 파일명: {out_name}")
        try:
            run_all(url, out_name)
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    f.write(url)
            except Exception:
                pass
            self._notify(f"완료! → {out_name}")
        except Exception as e:
            update_progress(f"작업 중 오류 발생: {e}")
            self._notify(f"실행 중 오류 발생:\n{e}")

    def _notify(self, msg):
        # GUI 스레드로 돌아와서 알림 및 버튼 복원
        def _on_gui():
            messagebox.showinfo("작업 결과", msg)
            self.run_btn.config(state="normal", text="실행")
            self.entry.config(state="normal")
        self.root.after(0, _on_gui)

    def on_exit(self):
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    app = App(root)
    root.mainloop()