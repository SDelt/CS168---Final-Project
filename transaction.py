"""
Notes:

Transaction ID Calculation: Uses a combination of transaction attributes to generate a unique hash
Signature Handling: The sign method signs the transaction using a private key, and the valid_signature method checks if the signature is valid with the corresponding public key
Funds Verification: The sufficient_funds method checks if the transaction amount, including the fee, can be covered by the current balance in the provided block
Total Output Calculation: Computes the sum of all outputs plus the transaction fee, which represents the total gold going out in the transaction
"""


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
            'pubKey': self.pub_key,
            'outputs': self.outputs,
            'fee': self.fee,
            'data': self.data
        }
        return hash('TX' + json.dumps(transaction_data, sort_keys=True))

    def sign(self, priv_key):
        try:
            print("Self: ", self)
            print("Private key: ", priv_key)
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

# Example Usage
# transaction = Transaction(
    # from_address='1234567890abcdef',
    # nonce=1,
    # pub_key='abcdef1234567890',
    # outputs=[{'amount': 100, 'address': 'fedcba0987654321'}],
    # fee=10
# )

# transaction.sign('private_key_example')
# print("Transaction ID:", transaction.id)
# print("Is signature valid?", transaction.valid_signature())
# print("Total output:", transaction.total_output())

