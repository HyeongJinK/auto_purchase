import csv
import requests
import io

############################################
# CSV에서 사용자 정보 가져오기 (웹에 공개된 구글 시트 CSV)
############################################
def get_user_info_from_public_csv(csv_url):
    """
    구글 시트를 웹에 게시(Publish to the web)한 CSV URL에서
    데이터를 받아 파이썬 dict 형식으로 반환.
    """
    response = requests.get(csv_url)
    response.raise_for_status()

    # UTF-8-sig로 디코딩하여 BOM 문제 해결
    content = response.content.decode("utf-8-sig")
    f = io.StringIO(content, newline='')
    reader = csv.DictReader(f)
    data = []
    for row in reader:
        data.append(row)
    return data