import requests
import hashlib
import time

merchant_id = 20379
service_id = 27979
merchant_user_id = 32644
secret_key = 'f8MwzPA0fqA7'

base_url = 'https://api.click.uz/v2/merchant/'

"https://my.click.uz/services/pay?service_id=27979&merchant_id=32644&amount=1000&transaction_param=abc&return_url=https://google.com"


def generate_auth_header():
    timestamp = str(int(time.time()))
    digest = hashlib.sha1((timestamp + secret_key).encode()).hexdigest()
    return {
        'Auth': f'{merchant_user_id}:{digest}:{timestamp}'
    }


def create_invoice(amount, phone_number, merchant_trans_id):
    endpoint = 'invoice/create'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    data = {
        'service_id': service_id,
        'amount': amount,
        'phone_number': phone_number,
        'merchant_trans_id': merchant_trans_id
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def check_invoice_status(invoice_id):
    endpoint = f'invoice/status/{service_id}/{invoice_id}'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    response = requests.get(url, headers=headers)
    return response.json()


def check_payment_status(payment_id):
    endpoint = f'payment/status/{service_id}/{payment_id}'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    response = requests.get(url, headers=headers)
    return response.json()


def check_payment_status_by_mti(merchant_trans_id, payment_date):
    endpoint = f'payment/status_by_mti/{service_id}/{merchant_trans_id}/{payment_date}'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    response = requests.get(url, headers=headers)
    return response.json()


def reverse_payment(payment_id):
    endpoint = f'payment/reversal/{service_id}/{payment_id}'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    response = requests.delete(url, headers=headers)
    return response.json()


def create_card_token(card_number, expire_date, temporary):
    endpoint = 'card_token/request'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    data = {
        'service_id': service_id,
        'card_number': card_number,
        'expire_date': expire_date,
        'temporary': temporary
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def verify_card_token(card_token, sms_code):
    endpoint = 'card_token/verify'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    data = {
        'service_id': service_id,
        'card_token': card_token,
        'sms_code': sms_code
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def make_payment_with_card_token(card_token, amount, transaction_parameter):
    endpoint = 'card_token/payment'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    data = {
        'service_id': service_id,
        'card_token': card_token,
        'amount': amount,
        'transaction_parameter': transaction_parameter
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def delete_card_token(card_token):
    endpoint = f'card_token/{service_id}/{card_token}'
    url = base_url + endpoint
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        **generate_auth_header()
    }
    response = requests.delete(url, headers=headers)
    return response.json()


def main():
    # print(create_invoice(1000, '+998904613136', 1))
    # {'error_code': 0, 'error_note': '', 'invoice_id': 143265938, 'eps_id': '0064'} 🟢
    # {'error_code': 0, 'error_note': '', 'invoice_id': 143265965, 'eps_id': '0064'}
    # {'error_code': 0, 'error_note': '', 'invoice_id': 143265271, 'eps_id': '0064'}
    # {'error_code': 0, 'error_note': '', 'invoice_id': 143265594, 'eps_id': '0064'}
    payment_id = 2702080657  # 🟢
    # payment_id = check_invoice_status(143265938)['payment_id']
    print(payment_id)
    print(check_payment_status(payment_id))


if __name__ == '__main__':
    main()
