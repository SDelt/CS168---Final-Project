# Python, did not have a direct equivalent of EventEmitter, we mimiced its behavior using Python's standard libraries

'''

To Do:

Event Handling: The original JavaScript class uses event handling for actions like receiving blocks. Python does not have built-in event handling similar to Node.js. If needed, you can use a package like PyPubSub or implement custom event handling.
Network Interface: I've assumed there's an interface self.net that has methods like broadcast used in the JavaScript version. You would need to define how network messaging works in your Python project.
Utility Functions: Functions like generate_keypair_from_mnemonic and calc_address should be defined in a utility module (utils), which mimics the JavaScript utility behavior.

Add methods for handling blocks, transactions, and other functionalities

'''


import logging
from blockchain import Blockchain
from utils import generate_keypair_from_mnemonic, calc_address

class Client:
    def __init__(self, name, password, net, starting_block=None, key_pair=None):
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
        self.key_pair = key_pair

        if Blockchain.has_instance():
            bc = Blockchain.get_instance()
            self.generate_address(bc.mnemonic)

        if starting_block:
            self.set_genesis_block(starting_block)

    def set_genesis_block(self, starting_block):
        if self.last_block:
            raise Exception("Cannot set genesis block for existing blockchain.")
        self.last_confirmed_block = starting_block
        self.last_block = starting_block
        self.blocks[starting_block.id] = starting_block

    def generate_address(self, mnemonic):
        if not mnemonic:
            raise Exception("Mnemonic not set")
        self.key_pair = generate_keypair_from_mnemonic(mnemonic, self.password)
        self.address = calc_address(self.key_pair.public)
        logging.info(f"{self.name}'s address is: {self.address}")

    def post_transaction(self, outputs, fee=None):
        if fee is None:
            fee = Blockchain.DEFAULT_TX_FEE
        total_payments = sum(amount for _, amount in outputs) + fee
        if total_payments > self.available_gold:
            raise Exception(f"Requested {total_payments}, but account only has {self.available_gold}.")
        # Assume post_generic_transaction is defined to create and return a transaction
        return self.post_generic_transaction({'outputs': outputs, 'fee': fee})

    def post_generic_transaction(self, tx_data):
        tx = Blockchain.make_transaction({
            'from': self.address,
            'nonce': self.nonce,
            'pub_key': self.key_pair.public,
            **tx_data
        })
        # Assume tx.sign is a method of the Transaction class
        tx.sign(self.key_pair.private)
        self.pending_outgoing_transactions[tx.id] = tx
        self.nonce += 1
        self.net.broadcast(Blockchain.POST_TRANSACTION, tx)
        return tx

