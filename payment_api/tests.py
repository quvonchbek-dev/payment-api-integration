import json

import requests

url = 'http://localhost:8000/api/payment/payme/'


def main():
    session = requests.Session()
    session.auth = ("admin", "admin")
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
    r = requests.post(url, json=data, auth=("admin", "admin"))
    print(r.text)


if __name__ == "__main__":
    main()
