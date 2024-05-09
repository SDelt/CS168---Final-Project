# Python, did not have a direct equivalent of EventEmitter, we mimiced its behavior using Python's standard libraries

import threading
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
        self.block_lock = threading.Lock()
        
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
        self.net.broadcast(self.address, Blockchain.POST_TRANSACTION, tx)
        return tx
    
    def make_deduction(self, tx):
        self.validate_transaction(tx)
        self.process_payments(tx)
        self.apply_transaction_fee(tx)

    def validate_transaction(self, tx):
        total_payments_with_fee = self.calculate_total_with_fee(tx)
        sender_balance = self.last_confirmed_block.balance_of(self.address)
        if total_payments_with_fee > sender_balance:
            raise Exception(f"Requested {total_payments_with_fee}, but account only has {sender_balance}.")

    def calculate_total_with_fee(self, tx):
        total_payments = sum(output['amount'] for output in tx.outputs)
        fee = tx.fee if hasattr(tx, 'fee') else Blockchain.get_default_tx_fee()
        return total_payments + fee

    def process_payments(self, tx):
        total_payments = sum(output['amount'] for output in tx.outputs)
        amount_to_pay = total_payments // len(tx.outputs)
        for output in tx.outputs:
            self.send_payment(output['address'], amount_to_pay)

    def apply_transaction_fee(self, tx):
        fee = tx.fee if hasattr(tx, 'fee') else Blockchain.get_default_tx_fee()
        total_payments_with_fee = sum(output['amount'] for output in tx.outputs) + fee
        self.last_confirmed_block.deduct_balance(self.address, total_payments_with_fee)

    def send_payment(self, recipient_address, amount):
        self.last_confirmed_block.add_to_balance(recipient_address, amount)
        logging.info(f"Updated {amount} gold to {recipient_address}")

    def generate_address(self, mnemonic):
        if not mnemonic:
            raise Exception("Mnemonic not set")
        key_pair = generate_keypair_from_mnemonic(mnemonic, self.password)
        self.key_pair = key_pair
        self.address = calc_address(self.key_pair['public'])
        logging.info(f"{self.name}'s address is: {self.address}")

    def show_all_balances(self):
        from blockchain import Blockchain
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
        self.blocks[block.id] = block 

    def set_last_confirmed(self):
        self.last_confirmed_block = self.last_block    
        
    def receive_block(self, block):
        from blockchain import Blockchain
        block = Blockchain.deserialize_block(block)

        with self.block_lock:
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
                self.last_confirmed_block = block

            unstuck_blocks = self.pending_blocks.pop(block.id, [])
            for b in unstuck_blocks:
                self.receive_block(b)

        return block
        
    def request_missing_block(self, block):
        from blockchain import Blockchain
        missing_block_hash = block.prev_block_hash
        self.log(f"Asking for missing block: {missing_block_hash}")

        msg = {
            'from': self.address,
            'missing': missing_block_hash
        }

        for client in self.net.clients:
            if client.address != self.address:  # Exclude self from broadcasting
                client.receive_missing_block_request(msg)
    
    def receive_missing_block_request(self, msg):
        missing_block_hash = msg['missing']
        if missing_block_hash in self.blocks:
            block = self.blocks[missing_block_hash]
            self.log(f"{self.name}: Providing missing block {missing_block_hash}")
            self.send_block(block)






