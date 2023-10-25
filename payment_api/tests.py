import json

import requests

url = 'http://localhost:8000/api/payment/payme/'


def main():
    session = requests.Session()
    session.auth = ("admin", "admin")
    auth = session.get(url)
    data = {
        "method": "CheckPerformTransaction",
        "params": {
            "amount": 100000,
            "account": {
                "id": 24
            }
        },
        "id": 12
    }
    r = session.post(url, json=data)
    print(r.text, file=open("result.json", "w"))


if __name__ == "__main__":
    main()
