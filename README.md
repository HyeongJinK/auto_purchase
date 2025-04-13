```
python -m venv venv
source venv/bin/activate
pip install keras-ocr easyocr tensorflow opencv-python numpy pillow selenium
```


```bash
pip freeze > requirements.txt

pip install -r requirements.txt

pip install pyinstaller

윈도우
pyinstaller --onefile --noconsole index.py
mac
pyinstaller --onefile --windowed index.py
pyinstaller --onedir --windowed index.py

```