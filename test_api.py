import requests

SERVICE_KEY = "현재사용중인인증키"

url = "https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsList01"

params = {
    "serviceKey": SERVICE_KEY,
    "pageNo": 1,
    "numOfRows": 1,
    "type": "json"
}

print("API 접속 테스트")

r = requests.get(
    url,
    params=params,
    timeout=120
)

print("Status:", r.status_code)
print(r.text[:1000])