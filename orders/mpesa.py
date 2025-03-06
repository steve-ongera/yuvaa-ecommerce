# 1. First, install required packages
# pip install requests python-decouple

# 2. Create a new file called mpesa.py in your app directory

import requests
import base64
import json
from datetime import datetime
from django.conf import settings
from decouple import config

class MpesaC2BCredential:
    consumer_key = config('MPESA_CONSUMER_KEY')
    consumer_secret = config('MPESA_CONSUMER_SECRET')
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
class MpesaAccessToken:
    @staticmethod
    def validated_mpesa_access_token():
        r = requests.get(
            MpesaC2BCredential.api_URL,
            auth=(MpesaC2BCredential.consumer_key, MpesaC2BCredential.consumer_secret)
        )
        mpesa_access_token = json.loads(r.text)
        return mpesa_access_token['access_token']

class LipaNaMpesaPassword:
    @staticmethod
    def lipa_na_mpesa_password():
        # Paybill Number
        business_short_code = config('MPESA_SHORTCODE')  # Your M-Pesa Paybill Number (247247)
        passkey = config('MPESA_PASSKEY')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = business_short_code + passkey + timestamp
        online_password = base64.b64encode(data_to_encode.encode())
        return {
            'timestamp': timestamp,
            'password': online_password.decode('utf-8'),
            'shortcode': business_short_code
        }

def initiate_stk_push(phone_number, amount, order_id, account_reference='0757790687', callback_url=None):
    """
    Initiates an STK push transaction for M-Pesa Paybill
    
    Parameters:
    phone_number (str): Customer's phone number
    amount (int/float): Amount to be charged
    order_id (str): Unique identifier for the order
    account_reference (str): Account number to show on M-Pesa (default: 0757790687)
    callback_url (str): URL to receive M-Pesa callback (defaults to settings)
    """
    access_token = MpesaAccessToken.validated_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": "Bearer %s" % access_token}
    
    # Format phone number: Remove leading 0 and add country code
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    # Get password and timestamp
    lipana_data = LipaNaMpesaPassword.lipa_na_mpesa_password()
    
    # Use provided callback or get from settings
    if callback_url is None:
        callback_url = config('MPESA_CALLBACK_URL')
    
    request_data = {
        "BusinessShortCode": lipana_data['shortcode'],  # 247247 as configured
        "Password": lipana_data['password'],
        "Timestamp": lipana_data['timestamp'],
        "TransactionType": "CustomerPayBillOnline",  # For Paybill number
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": lipana_data['shortcode'],  # 247247
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,  # Default: 0757790687
        "TransactionDesc": f"Payment for Order #{order_id}"
    }
    
    response = requests.post(api_url, json=request_data, headers=headers)
    return response.json()

# 3. Add a C2B API registration method 
def register_c2b_urls():
    """
    Register URLs for C2B API to handle payments made directly to Paybill
    Must be called once during setup or when URLs change
    """
    access_token = MpesaAccessToken.validated_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = {"Authorization": "Bearer %s" % access_token}
    
    options = {
        "ShortCode": config('MPESA_SHORTCODE'),  # 247247
        "ResponseType": "Completed",  # Can be 'Cancelled' or 'Completed'
        "ConfirmationURL": config('MPESA_CONFIRMATION_URL'),  # Must be HTTPS
        "ValidationURL": config('MPESA_VALIDATION_URL')  # Must be HTTPS
    }
    
    response = requests.post(api_url, json=options, headers=headers)
    return response.json()

# 4. Add a method to simulate C2B transactions (useful for testing)
def simulate_c2b_transaction(phone_number, amount, bill_ref_number=None):
    """
    Simulates a C2B transaction (only works in sandbox environment)
    
    Parameters:
    phone_number (str): Customer's phone number
    amount (int/float): Amount to be charged
    bill_ref_number (str): Optional reference number (defaults to account number 0757790687)
    """
    if bill_ref_number is None:
        bill_ref_number = "0757790687"  # Default account number
        
    access_token = MpesaAccessToken.validated_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate"
    headers = {"Authorization": "Bearer %s" % access_token}
    
    # Format phone number
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    request_data = {
        "ShortCode": config('MPESA_SHORTCODE'),  # 247247
        "CommandID": "CustomerPayBillOnline",
        "Amount": int(amount),
        "Msisdn": phone_number,
        "BillRefNumber": bill_ref_number
    }
    
    response = requests.post(api_url, json=request_data, headers=headers)
    return response.json()

# 5. Query transaction status
def query_transaction_status(checkout_request_id):
    """
    Checks the status of an STK Push transaction
    
    Parameters:
    checkout_request_id (str): The CheckoutRequestID from an STK push request
    """
    access_token = MpesaAccessToken.validated_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": "Bearer %s" % access_token}
    
    lipana_data = LipaNaMpesaPassword.lipa_na_mpesa_password()
    
    query_data = {
        "BusinessShortCode": lipana_data['shortcode'],
        "Password": lipana_data['password'],
        "Timestamp": lipana_data['timestamp'],
        "CheckoutRequestID": checkout_request_id
    }
    
    response = requests.post(api_url, json=query_data, headers=headers)
    return response.json()