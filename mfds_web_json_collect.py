import requests
import json
import time
from datetime import datetime

# ============================================
# MFDS 건강기능식품 종합정보 서비스 Ajax URL
# ============================================

LIST_PAGE_URL = "https://data.mfds.go.kr/hid/opbaa01/prdtSrchLst.do"
AJAX_URL = "https://data.mfds.go.kr/hid/opbaa01/prdtSrchLstSelect.do"

# 수집 설정
START_PAGE = 1
END_PAGE = 5

# 처음에는 5페이지 정도만 테스트 권장
# 정상 작동 확인 후 END_PAGE를 100, 500 등으로 늘리세요.

RECORD_COUNT_PER_PAGE = 10

# 저장 파일명
RAW_JSON_FILE = "mfds_raw_response.json"
PRODUCT_JSON_FILE = "mfds_products.json"


def make_session():
    """
    먼저 목록 페이지에 접속해서 세션 쿠키를 받은 뒤,
    같은 세션으로 Ajax 요청을 보냅니다.
    """
    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    res = session.get(
        LIST_PAGE_URL,
        headers=headers,
        timeout=30
    )

    print("초기 페이지 접속 상태:", res.status_code)

    return session


def fetch_page(session, page_index=1):
    """
    DevTools Payload 기준으로 POST 요청
    """

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://data.mfds.go.kr",
        "Referer": LIST_PAGE_URL,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "searchType": "1",
        "searchKeyword": "",
        "typeCondition": "",
        "searchCondition": "",
        "rwmtCondition": "",
        "ftnCondition": "",
        "recordCountPerPage": str(RECORD_COUNT_PER_PAGE),
        "buttonName": "searchBtn",
        "isSearchCondition": "false",
        "pageIndex": str(page_index),
        "isSearchAll": "true"
    }

    res = session.post(
        AJAX_URL,
        headers=headers,
        data=payload,
        timeout=60
    )

    print(f"{page_index} 페이지 상태:", res.status_code)

    if res.status_code != 200:
        print(res.text[:500])
        return None

    try:
        return res.json()

    except Exception as e:
        print("JSON 변환 실패:", e)
        print(res.text[:1000])
        return None


def find_product_list(data):
    """
    응답 JSON 구조가 아직 확정되지 않았기 때문에,
    흔한 key명을 자동 탐색합니다.
    """

    if data is None:
        return []

    # 응답 전체가 list인 경우
    if isinstance(data, list):
        return data

    # 응답이 dict인 경우
    if isinstance(data, dict):

        candidate_keys = [
            "list",
            "result",
            "resultList",
            "data",
            "items",
            "rows",
            "prdtList",
            "productList"
        ]

        for key in candidate_keys:
            if key in data and isinstance(data[key], list):
                return data[key]

        # dict 내부에 list가 숨어 있는 경우 자동 탐색
        for key, value in data.items():
            if isinstance(value, list):
                return value

            if isinstance(value, dict):
                nested = find_product_list(value)
                if nested:
                    return nested

    return []


def main():
    print("MFDS 건강기능식품 데이터 수집 시작")
    print("Ajax URL:", AJAX_URL)

    session = make_session()

    all_raw = []
    all_products = []

    for page in range(START_PAGE, END_PAGE + 1):
        data = fetch_page(session, page)

        if data is None:
            print(f"{page} 페이지 수집 실패")
            continue

        all_raw.append({
            "page": page,
            "response": data
        })

        products = find_product_list(data)

        print(f"{page} 페이지 제품 수:", len(products))

        for item in products:
            if isinstance(item, dict):
                item["_page"] = page
                all_products.append(item)

        time.sleep(0.5)

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": LIST_PAGE_URL,
        "ajax_url": AJAX_URL,
        "start_page": START_PAGE,
        "end_page": END_PAGE,
        "record_count_per_page": RECORD_COUNT_PER_PAGE,
        "total_collected_products": len(all_products),
        "products": all_products
    }

    with open(RAW_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(
            all_raw,
            f,
            ensure_ascii=False,
            indent=2
        )

    with open(PRODUCT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("====================================")
    print("수집 완료")
    print("Raw 응답 저장:", RAW_JSON_FILE)
    print("제품 목록 저장:", PRODUCT_JSON_FILE)
    print("총 수집 제품 수:", len(all_products))
    print("====================================")


if __name__ == "__main__":
    main()