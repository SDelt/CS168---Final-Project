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

    @property
    def confirmed_balance(self):
        return self.last_confirmed_block.balance_of(self.address)

    @property
    def available_gold(self):
        pending_spent = sum(tx.total_output() for tx in self.pending_outgoing_transactions.values())
        return self.confirmed_balance - pending_spent
        
    def post_transaction(self, outputs, fee=None):
    
        print("")
        print("Outputs: ", outputs)
        print("")
    
        from blockchain import Blockchain
        if fee is None:
            fee = Blockchain.get_default_tx_fee()
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
        
        print("HERE")
        self.net.broadcast(Blockchain.POST_TRANSACTION, tx_dict)
        return tx
    
    # Here we need to figure out a function to deduct the total_payments from the clients self.available_gold
    # then once subtracting that amount, total_payments - fee should then be payed to the address it is meant to be sent to
    # fakeNet shoul call here if address type is of client and msg is POST_TRANSACTION

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
        self.blocks[block.id] = block  # Assign the block to the dictionary using its ID as the key

    def set_last_confirmed(self):
        self.last_confirmed_block = self.last_block    
        
    def receive_block(self, block):
        from blockchain import Blockchain  # Import locally to prevent circular imports
        block = Blockchain.deserialize_block(block)

        if block.id in self.blocks:
            return None

        if not block.has_valid_proof() and not block.is_genesis_block():
            self.log(f"Block {block.id} does not have a valid proof.")
            return None

        prev_block = self.blocks.get(block.prev_block_hash)
        if not prev_block and not block.is_genesis_block():
            stuck_blocks = self.pending_blocks.get(block.prev_block_hash, set())

            if not stuck_blocks:
                self.request_missing_block(block)
            stuck_blocks.add(block)
            self.pending_blocks[block.prev_block_hash] = stuck_blocks
            return None

        if not block.is_genesis_block():
            success = block.rerun(prev_block)
            if not success:
                return None

        self.blocks[block.id] = block

        if self.last_block.chain_length < block.chain_length:
            self.last_block = block
            self.set_last_confirmed()

        unstuck_blocks = self.pending_blocks.pop(block.id, [])
        for b in unstuck_blocks:
            self.log(f"Processing unstuck block {b.id}")
            self.receive_block(b)

        return block



