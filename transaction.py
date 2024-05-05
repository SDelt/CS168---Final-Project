import json
from cryptography.hazmat.primitives import serialization
from utils import hash, sign, verify_signature, address_matches_key

class Transaction:
    def __init__(self, from_address, nonce, pub_key, sig=None, outputs=None, fee=0, data=None):
        self.from_address = from_address
        self.nonce = nonce
        self.pub_key = pub_key
        self.sig = sig
        self.fee = fee
        self.outputs = outputs if outputs is not None else []
        self.data = data if data is not None else {}

    @property
    def id(self):
        transaction_data = {
            'from': self.from_address,
            'nonce': self.nonce,
            'pub_key': self.pub_key.decode('utf-8'),  # Convert bytes to string
            'outputs': self.outputs,
            'fee': self.fee,
            'data': self.data
        }
        return hash('TX' + json.dumps(transaction_data, sort_keys=True))

    def sign(self, priv_key):
        try:
            self.sig = sign(priv_key, self.id)
        except Exception as e:
            print("Error occurred while signing the transaction:", e)

    def valid_signature(self):
        if not self.sig or not address_matches_key(self.from_address, self.pub_key):
            return False
        return verify_signature(self.pub_key, self.id, self.sig)


    def sufficient_funds(self, block):
        available_balance = block.balance_of(self.from_address)
        return self.total_output() <= available_balance

    def total_output(self):
        return sum(output['amount'] for output in self.outputs) + self.fee
