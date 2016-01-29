import json
import sys
import math

from plaid import Client
from plaid import errors as plaid_errors

class Reporter(object):
    def __init__(self, history):
        self.history = history

class TransactionProcessor(object):
    def __init__(self, transactions):
        self.transactions = transactions

    def roundup_potential(self):
        diffs = []
        map(lambda tx : diffs.append(math.ceil(tx.amount) - tx.amount), filter(lambda tx: tx.amount > 0, self.transactions))
        return sum(diffs)

class Account(object):
    pass

class Transaction(object):
    def __init__(self, data):
        self.amount = float(data["amount"])
        self.data = data["date"]

        self.category = {}
        self.is_categorized = "category_id" in data
        if self.is_categorized:
            category_id = data["category_id"]

            self.category[0] = category_id[0:3]
            self.category[1] = category_id[3:5]
            self.category[2] = category_id[5:8]
        else:
            self.category[0] = ""
            self.category[1] = ""
            self.category[2] = ""

    def categories(self, index):
        if self.is_categorized:
            categories = []
            for i, v in enumerate(index):
                categories.append(self.category[i])
            return tuple(categories)
        else:
            return ()

    def __str__(self):
        if self.is_categorized:
            return str(self.category[0]) + "-" + str(self.category[1]) + "-" + str(self.category[1]) + ": " + str(self.amount)
        else:
            return "UNCATEGORIZED: " + str(self.amount)

class InstitutionAccountHistory(object):
    def __init__(self, json_data):
        self.data = json.loads(json_data)
        self.accounts = []
        self.transactions = []

        self._extract_accounts()
        self._extract_transactions()

    def _extract_accounts(self):
        pass

    def _extract_transactions(self):
        if "transactions" not in self.data:
            raise Exception("No transactions were found.")
        map(lambda transaction_data : self.transactions.append(Transaction(transaction_data)), self.data["transactions"])

        # recover the set of transactions
        self.transaction_table = {}

        categories = [0,1,2] # as per plaid specification
        for i, c in enumerate(categories):
            index = tuple(categories[0:(i + 1)])

            for tx in self.transactions:
                category_index = tx.categories(index)
                if category_index in self.transaction_table:
                    self.transaction_table[category_index].append(tx)
                else:
                    self.transaction_table[category_index] = [tx]


            # map(lambda tx: table[tx.categories(index)] = [tx] if tx.categories(index) not in table else table[tx.categories(index)].append(tx), self.transactions)
            # self.transaction_table[index] = filter(lambda tx : tx.in_category(index), self.transactions)

        # self.transaction_categories[0] = set()
        # map(lambda tx: self.transaction_categories[0].add(tx.category_0), filter(lambda tx: tx.is_categorized, self.transactions))
        # self.transaction_categories[1] = set()
        # map(lambda tx: self.transaction_categories[1].add(tx.category_1), filter(lambda tx: tx.is_categorized, self.transactions))
        # self.transaction_categories[2] = set()
        # map(lambda tx: self.transaction_categories[2].add(tx.category_2), filter(lambda tx: tx.is_categorized, self.transactions))

    def _index_transactions(self):
        pass
        # categorized_transactions = filter(lambda tx: tx.is_categorized, self.transactions)
        # for category in history.transaction_categories:
        #     pass

            # transactions_c0 = filter(lambda tx : tx.category_0 == c0, categorized_transactions)
            # processor = TransactionProcessor(transactions_c0)
            # roundup = processor.roundup_potential()
            #
            # print "Category-0[%s] roundup: %f" % (c0, roundup)

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
    bank = raw_input("Bank: ") # wells
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
                with open("tx.json", "w") as f:
                    f.write(json.dumps(data))
        else:
            print "Something went horribly wrong..."
            print data

    except plaid_errors.UnauthorizedError as e:
         # handle this
        print e

if len(sys.argv) > 1:
    with open(sys.argv[1], "r") as fh:
        data = fh.read()
        history = InstitutionAccountHistory(data)

        # for tx in history.transactions:
        #     print tx

        processor = TransactionProcessor(history.transactions)
        roundup = processor.roundup_potential()
        print roundup

        roundup_table = {}
        for transaction_index in history.transaction_table:
            transactions = history.transaction_table[transaction_index]
            processor = TransactionProcessor(transactions)
            roundup = processor.roundup_potential()

            print "Category(%s) roundup: %f" % (transaction_index, roundup)

            roundup_table[transaction_index] = roundup

        # TODO: group roundups by categories (start at category 0, then category 0+1, then category 0+1+2)
        for cid in range(3):
            print cid
            subset = {}
            for index in filter(lambda i : len(i) >= (cid + 1), roundup_table):
                proper_index = index[0 : (cid + 1)]
                if proper_index in subset:
                    subset[proper_index].append(roundup_table[index])
                else:
                    subset[proper_index] = [roundup_table[index]]
            print subset


        # print "UNCATEGORIZED TRANSCATIONS"
        # for tx in history.uncategorized_transactions:
        #     print tx.amount

else: # connect and get the latest history
    with open("secrets", "r") as f:
        lines = f.readlines()
        client_id = lines[0].strip()
        secret = lines[1].strip()
        public_key = lines[2].strip()

        plaid_credentials = PlaidCredentials(client_id, secret, public_key)
        print plaid_credentials.__dict__
        bank, bank_credentials = get_bank_credentials()
        connect(plaid_credentials, bank, bank_credentials)
