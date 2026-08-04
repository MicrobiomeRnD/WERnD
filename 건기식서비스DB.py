import requests
import pandas as pd
import re
import json
from datetime import datetime

# ============================================
# 설정
# ============================================

SERVICE_KEY = "sW7R7mOPQruqii2aJGOeeETyUzgleUynjg0sBpB9+mxYT+PjN1xZ9L2Op5tdZ9nqe5VT3PYlxA/yxGEAX6ThrQ=="

BASE_URL = "http://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsList01"

START_DATE = "2026-06-01"
END_DATE = "2026-08-31"

# ============================================
# API 조회
# ============================================

def fetch_page(page_no=1, num_rows=100):

    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_rows,
        "type": "json"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def extract_items(data):

    try:

        body = data["response"]["body"]

        total_count = int(
            body.get("totalCount", 0)
        )

        items = body.get(
            "items",
            {}
        ).get(
            "item",
            []
        )

        if isinstance(items, dict):
            items = [items]

        return items, total_count

    except Exception as e:

        print("응답 파싱 오류")
        print(e)

        return [], 0


def fetch_all():

    all_items = []

    first = fetch_page(
        page_no=1,
        num_rows=5
    )

    items, total_count = extract_items(first)

    all_items.extend(items)

    total_pages = (total_count // 100) + 1

    print(
        f"총 {total_count:,}건 발견"
    )

    for page_no in range(
        2,
        total_pages + 1
    ):

        print(
            f"수집중 {page_no}/{total_pages}"
        )

        data = fetch_page(
            page_no=page_no,
            num_rows=5
        )

        items, _ = extract_items(data)

        all_items.extend(items)

    return pd.DataFrame(all_items)

# ============================================
# 컬럼 찾기
# ============================================

def find_column(df, candidates):

    for col in candidates:
        if col in df.columns:
            return col

    return None


# ============================================
# 날짜 정리
# ============================================

def normalize_date(x):

    if pd.isna(x):
        return pd.NaT

    x = str(x).strip()

    if re.match(r"^\d{8}$", x):
        return pd.to_datetime(
            x,
            format="%Y%m%d",
            errors="coerce"
        )

    return pd.to_datetime(
        x,
        errors="coerce"
    )


# ============================================
# 기능성 분류
# ============================================

def classify_functionality(text):

    if pd.isna(text):
        return ["미분류"]

    text = str(text)

    mapping = {

        "장건강/프로바이오틱스": [
            "프로바이오틱스",
            "유산균",
            "장 건강",
            "배변활동"
        ],

        "체지방/다이어트": [
            "체지방",
            "가르시니아",
            "녹차추출물",
            "다이어트"
        ],

        "관절/뼈": [
            "관절",
            "연골",
            "골다공증",
            "MSM"
        ],

        "눈 건강": [
            "눈",
            "루테인",
            "지아잔틴"
        ],

        "혈압/혈행": [
            "혈압",
            "혈행",
            "EPA",
            "DHA",
            "중성지방"
        ],

        "면역": [
            "면역",
            "아연",
            "홍삼"
        ],

        "인지/기억력": [
            "인지",
            "기억력",
            "포스파티딜세린"
        ],

        "수면": [
            "수면",
            "테아닌"
        ],

        "피부/이너뷰티": [
            "피부",
            "콜라겐",
            "히알루론산"
        ]
    }

    result = []

    for category, keywords in mapping.items():

        for kw in keywords:

            if kw in text:

                result.append(category)

                break

    if len(result) == 0:
        result.append("기타")

    return result


# ============================================
# JSON 변환
# ============================================

def json_converter(obj):

    if isinstance(
        obj,
        (pd.Timestamp, datetime)
    ):
        return obj.strftime(
            "%Y-%m-%d"
        )

    return str(obj)


# ============================================
# 메인
# ============================================

def main():

    print("데이터 수집 시작")
    df = fetch_all()

    if df.empty:
        print("수집된 데이터가 없습니다.")
        return

    print("컬럼 목록:", df.columns.tolist())

    date_col = find_column(
        df,
        [
            "PRD_PRMS_DT",
            "PRDLST_REPORT_DT",
            "REG_DT"
        ]
    )

    func_col = find_column(
        df,
        [
            "PRIMARY_FNCLTY",
            "FNCLTY_CN",
            "IFTKN_ATNT_MATR_CN"
        ]
    )

    if date_col is None:
        raise ValueError(
            "등록일 컬럼을 찾지 못했습니다."
        )

    df["등록일자_정리"] = df[
        date_col
    ].apply(normalize_date)

    start = pd.to_datetime(
        START_DATE
    )

    end = pd.to_datetime(
        END_DATE
    )

    target = df[
        (df["등록일자_정리"] >= start)
        &
        (df["등록일자_정리"] <= end)
    ]

    print(f"대상 건수: {len(target):,}건")

    if func_col is None:
        raise ValueError("기능성 컬럼을 찾지 못했습니다.")

    target["기능성분류"] = target[func_col].apply(classify_functionality)

    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "research_data")
    output_path = os.path.join(output_dir, "건기식_신제품_등록현황.json")

    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            target.to_dict(orient="records"),
            f,
            ensure_ascii=False,
            indent=2,
            default=json_converter
        )

    print(f"저장 완료: {output_path}")


if __name__ == "__main__":
    main()
