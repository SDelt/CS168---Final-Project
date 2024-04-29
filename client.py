# Python, did not have a direct equivalent of EventEmitter, we mimiced its behavior using Python's standard libraries

import logging
from utils import generate_keypair_from_mnemonic, calc_address
import importlib

class Client:
    def __init__(self, name, password, net, starting_block=None, mnemonic=None):
        self.net = net
        self.name = name
        self.password = password if password else f"{self.name}_pswd"
        self.nonce = 0
        self.pending_outgoing_transactions = {}
        self.pending_received_transactions = {}
        self.blocks = {}
        self.pending_blocks = {}
        self.last_confirmed_block = None
        self.last_block = None
        self.key_pair = None
        self.address = None
        
        if mnemonic:
            self.generate_address(mnemonic)

        if starting_block:
            self.set_genesis_block(starting_block)

        self.net.register(self)  # Register with the network

    @property
    def confirmed_balance(self):
        return self.last_confirmed_block.balance_of(self.address)

    @property
    def available_gold(self):
        pending_spent = sum(tx.total_output() for tx in self.pending_outgoing_transactions.values())
        return self.confirmed_balance - pending_spent

    def post_transaction(self, outputs, fee=None):
        Blockchain = importlib.import_module('blockchain').Blockchain  # Dynamic import
        if fee is None:
            fee = Blockchain.DEFAULT_TX_FEE
        total_payments = sum(amount for _, amount in outputs) + fee
        if total_payments > self.available_gold:
            raise Exception(f"Requested {total_payments}, but account only has {self.available_gold}.")
        return self.post_generic_transaction({'outputs': outputs, 'fee': fee})

    def post_generic_transaction(self, tx_data):
        Blockchain = importlib.import_module('blockchain').Blockchain  # Dynamic import
        tx = Blockchain.make_transaction({
            'from': self.address,
            'nonce': self.nonce,
            'pub_key': self.key_pair.public,
            **tx_data
        })
        tx.sign(self.key_pair.private)
        self.pending_outgoing_transactions[tx.id] = tx
        self.nonce += 1
        self.net.broadcast(Blockchain.POST_TRANSACTION, tx)
        return tx

    def generate_address(self, mnemonic):
        if not mnemonic:
            raise Exception("Mnemonic not set")
        key_pair = generate_keypair_from_mnemonic(mnemonic, self.password)
        self.key_pair = key_pair
        self.address = calc_address(key_pair['public'])
        logging.info(f"{self.name}'s address is: {self.address}")

    def show_all_balances(self):
        print(f"Balances for {self.name}:")
        for address, balance in self.blocks[-1].balances.items():
            print(f"Address: {address}, Balance: {balance}")

    def receive_message(self, msg, data):
        print(f"Received {msg}: {data}")

    def emit(self, event, data):
        self.net.send_message(self.address, event, data)
     
    def set_genesis_block(self, block):
        self.last_confirmed_block = block
        self.last_block = block



