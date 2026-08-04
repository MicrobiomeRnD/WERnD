import requests
import json
import time
import argparse
import calendar
import os
from datetime import date, datetime

# ============================================
# MFDS 건강기능식품 종합정보 서비스 Ajax URL
# ============================================

LIST_PAGE_URL = "https://data.mfds.go.kr/hid/opbaa01/prdtSrchLst.do"
AJAX_URL = "https://data.mfds.go.kr/hid/opbaa01/prdtSrchLstSelect.do"

# 수집 설정
DEFAULT_MAX_PRODUCTS = 200
RECORD_COUNT_PER_PAGE = 10

# 기본 저장 위치는 이 스크립트 기준 new_products_data 폴더입니다.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "new_products_data")
RAW_JSON_BASENAME = "mfds_raw_response.json"
PRODUCT_JSON_BASENAME = "mfds_products.json"
PRODUCT_JS_BASENAME = "mfds_products_data.js"


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력해야 합니다.")
    return number


def parse_args():
    parser = argparse.ArgumentParser(
        description="MFDS 신규 건강기능식품 데이터를 수집합니다."
    )
    parser.add_argument(
        "--max-products",
        type=positive_int,
        default=DEFAULT_MAX_PRODUCTS,
        metavar="N",
        help=f"수집할 최대 제품 수 (기본값: {DEFAULT_MAX_PRODUCTS})"
    )
    parser.add_argument(
        "--outdir",
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIRPATH",
        help="출력 폴더 (기본값: 스크립트 옆 new_products_data)"
    )
    return parser.parse_args()


def months_ago(day, months):
    """day에서 달력 기준 months개월 전 날짜를 반환합니다."""
    month_index = day.year * 12 + day.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def product_date(item):
    value = item.get("rptYmd")
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


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
    args = parse_args()
    end_date = date.today()
    start_date = months_ago(end_date, 3)
    output_dir = os.path.abspath(os.path.expanduser(args.outdir))
    raw_json_file = os.path.join(output_dir, RAW_JSON_BASENAME)
    product_json_file = os.path.join(output_dir, PRODUCT_JSON_BASENAME)
    product_js_file = os.path.join(output_dir, PRODUCT_JS_BASENAME)

    print("MFDS 건강기능식품 데이터 수집 시작")
    print("Ajax URL:", AJAX_URL)
    print(f"등록일 범위: {start_date} ~ {end_date}")
    print(f"최대 제품 수: {args.max_products:,}개")
    print("출력 폴더:", output_dir)

    session = make_session()

    all_raw = []
    all_products = []
    page = 1

    while len(all_products) < args.max_products:
        data = fetch_page(session, page)

        if data is None:
            print(f"{page} 페이지 수집 실패")
            break

        all_raw.append({
            "page": page,
            "response": data
        })

        products = find_product_list(data)

        print(f"{page} 페이지 제품 수:", len(products))

        if not products:
            print("더 이상 제품이 없어 수집을 종료합니다.")
            break

        dated_products = []
        for item in products:
            if isinstance(item, dict):
                registered = product_date(item)
                if registered is not None:
                    dated_products.append(registered)
                if registered is not None and start_date <= registered <= end_date:
                    item["_page"] = page
                    all_products.append(item)
                    if len(all_products) >= args.max_products:
                        break

        if not dated_products:
            print("등록일을 해석할 수 없어 수집을 종료합니다.")
            break

        # 목록이 최신순이라는 전제에서 한 페이지 전체가 시작일보다 오래되면 종료합니다.
        if dated_products and max(dated_products) < start_date:
            print("3개월 수집 범위를 벗어나 수집을 종료합니다.")
            break

        page += 1
        time.sleep(0.5)

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": LIST_PAGE_URL,
        "ajax_url": AJAX_URL,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "start_page": 1,
        "end_page": page,
        "record_count_per_page": RECORD_COUNT_PER_PAGE,
        "max_products": args.max_products,
        "total_collected_products": len(all_products),
        "products": all_products
    }

    os.makedirs(output_dir, exist_ok=True)

    with open(raw_json_file, "w", encoding="utf-8") as f:
        json.dump(
            all_raw,
            f,
            ensure_ascii=False,
            indent=2
        )

    with open(product_json_file, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    with open(product_js_file, "w", encoding="utf-8") as f:
        f.write("window.mfdsProductsData = ")
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write(";\n")

    print("====================================")
    print("수집 완료")
    print("Raw 응답 저장:", raw_json_file)
    print("제품 목록 저장:", product_json_file)
    print("로컬 fallback 저장:", product_js_file)
    print("총 수집 제품 수:", len(all_products))
    print("====================================")


if __name__ == "__main__":
    main()
