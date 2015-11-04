import json

from plaid import Client
from plaid import errors as plaid_errors

class PlaidCredentials(object):
    def __init__(self, client_id, secret, public_key):
        self.client_id = client_id
        self.secret = secret
        self.public_key = public_key

class BankCredentials(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

def get_bank_credentials():
    bank = raw_input("Bank: ")
    username = raw_input("Username: ")
    password = raw_input("Password: ")
    return bank, BankCredentials(username, password)

def connect(plaid_credentials, bank, bank_credentials):
    client = Client(client_id=plaid_credentials.client_id, secret=plaid_credentials.secret)
    try:
        response = client.connect(bank, {
            'username': bank_credentials.username,
            'password': bank_credentials.password
        })

        data = json.loads(response.content)
        if response.status_code == 200:
            print data
            if "access_token" in data:
                client_access_token = data["access_token"]
                client = Client(client_id=plaid_credentials.client_id, secret=plaid_credentials.secret, access_token=client_access_token)
                response = client.connect_get()
                data = json.loads(response.content)
                print "Transactions"
                print data
                with open("tx.json", "w") as f:
                    f.write(json.dumps(data))
        else:
            print "Something went horribly wrong..."
            print data
            
    except plaid_errors.UnauthorizedError as e:
         # handle this
        print e

with open("secrets", "r") as f:
    lines = f.readlines()
    client_id = lines[0].strip()
    secret = lines[1].strip()
    public_key = lines[2].strip()

    plaid_credentials = PlaidCredentials(client_id, secret, public_key)
    print plaid_credentials.__dict__
    bank, bank_credentials = get_bank_credentials()
    connect(plaid_credentials, bank, bank_credentials)    

    
