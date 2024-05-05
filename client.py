# Python, did not have a direct equivalent of EventEmitter, we mimiced its behavior using Python's standard libraries

import logging
import base64
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
        self.blocks = []
        self.pending_blocks = {}
        self.last_confirmed_block = None
        self.last_block = None
        self.key_pair = None
        self.address = None
        
        if mnemonic:
            self.generate_address(mnemonic)

        if starting_block:
            self.set_genesis_block(starting_block)

    @property
    def confirmed_balance(self):
        return self.last_confirmed_block.balance_of(self.address)

    @property
    def available_gold(self):
        pending_spent = sum(tx.total_output() for tx in self.pending_outgoing_transactions.values())
        return self.confirmed_balance - pending_spent
        
    def post_transaction(self, outputs, fee=None):
        from blockchain import Blockchain  # Import locally to prevent circular imports
        if fee is None:
            # fee = Blockchain.DEFAULT_TX_FEE
            fee = 1 # value should come from blockchain class, but is not importing correclty, so we harded coded here
        total_payments = sum(output['amount'] for output in outputs) + fee
        if total_payments > self.available_gold:
            raise Exception(f"Requested {total_payments}, but account only has {self.available_gold}.")
        return self.post_generic_transaction({'outputs': outputs, 'fee': fee})

    def post_generic_transaction(self, tx_data):
        from blockchain import Blockchain
        tx = Blockchain.make_transaction({
            'from': self.address,
            'nonce': self.nonce,
            'pub_key': self.key_pair['public'],
            **tx_data
        })
        tx.sign(self.key_pair['private'])
        self.pending_outgoing_transactions[tx.id] = tx
        self.nonce += 1
        tx_dict = {
            'from': tx.from_address,
            'nonce': tx.nonce,
            'pub_key': tx.pub_key,
            'sig': tx.sig,
            'fee': tx.fee,
            'outputs': tx.outputs,
            'data': tx.data
        }
        self.net.broadcast(Blockchain.POST_TRANSACTION, tx_dict)
        return tx

    def generate_address(self, mnemonic):
        if not mnemonic:
            raise Exception("Mnemonic not set")
        key_pair = generate_keypair_from_mnemonic(mnemonic, self.password)
        self.key_pair = key_pair
        self.address = calc_address(self.key_pair['public'])
        logging.info(f"{self.name}'s address is: {self.address}")

    def show_all_balances(self):
        from blockchain import Blockchain  # Import locally to prevent circular imports
        if not self.blocks:
            print("No blocks available yet.")
            return

        last_block = self.last_confirmed_block
        blockchain = Blockchain.get_instance()
        for client in blockchain.clients:
            balance = last_block.balance_of(client.address)
            print(f"Name: {client.name}, Balance: {balance}")

    def receive_message(self, msg, data):
        print(f"Received {msg} for {self.name}")

    def emit(self, event, data):
        self.net.send_message(self.address, event, data)
     
    def set_genesis_block(self, block):
        self.last_confirmed_block = block
        self.last_block = block
        self.blocks.append(block)


