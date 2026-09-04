import base64
from datetime import datetime

import requests
from django.conf import settings


def get_mpesa_access_token():
    credentials = (
        f"{settings.MPESA_CONSUMER_KEY}:"
        f"{settings.MPESA_CONSUMER_SECRET}"
    )

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
    }

    params = {
        "grant_type": "client_credentials",
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    return data["access_token"]


def generate_mpesa_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    data_to_encode = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        data_to_encode.encode()
    ).decode()

    return password, timestamp
# ------------------mps---------------

def normalize_phone_number(phone_number):
    cleaned = str(phone_number).strip().replace(" ", "")
    if cleaned.startswith("+254"):
        return cleaned.replace("+254", "254")
    if cleaned.startswith("254"):
        return cleaned
    if cleaned.startswith("0"):
        return f"254{cleaned[1:]}"
    return cleaned


def send_stk_push(phone_number, amount, account_reference):
    callback_url = settings.MPESA_CALLBACK_URL
    if not callback_url or "YOUR-PUBLIC-URL" in callback_url:
        raise ValueError(
            "MPESA_CALLBACK_URL is not configured. Set it to your public HTTPS callback URL "
            "(for example via ngrok) before sending STK Push requests."
        )

    normalized_phone = normalize_phone_number(phone_number)
    access_token = get_mpesa_access_token()

    password, timestamp = generate_mpesa_password()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": normalized_phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": normalized_phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": "Nana Lulu Order",
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30,
    )
    print(response.text)

    response.raise_for_status()

    return response.json()