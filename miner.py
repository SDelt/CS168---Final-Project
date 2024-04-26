"""
Notes:
Concurrency and Event Handling: simplifies concurrency handling by using time.sleep(0)
Transaction and Block Management: The methods sync_transactions, find_common_ancestor, and collect_transactions_to_common_ancestor manage the synchronization of transactions when new blocks are received
Broadcast and Receive: Methods for broadcasting proofs and receiving blocks are simplified to assume that there's a net interface with a broadcast
"""

import time
from client import Client
from blockchain import Blockchain

class Miner(Client):
    def __init__(self, name, password, net, starting_block=None, key_pair=None, mining_rounds=None):
        super().__init__(name, password, net, starting_block, key_pair)
        self.mining_rounds = mining_rounds if mining_rounds is not None else Blockchain.NUM_ROUNDS_MINING
        self.transactions = set()
        self.current_block = None

    def initialize(self):
        self.start_new_search()
        self.find_proof()

    def start_new_search(self, tx_set=None):
        if tx_set is None:
            tx_set = set()
        self.current_block = Blockchain.make_block(self.address, self.last_block)
        tx_set.update(self.transactions)
        for tx in tx_set:
            self.current_block.add_transaction(tx, self)
        self.transactions.clear()
        self.current_block.proof = 0

    def find_proof(self, one_and_done=False):
        pause_point = self.current_block.proof + self.mining_rounds
        while self.current_block.proof < pause_point:
            if self.current_block.has_valid_proof():
                print(f'Found proof for block {self.current_block.chain_length}: {self.current_block.proof}')
                self.announce_proof()
                self.receive_block(self.current_block)
                if one_and_done:
                    break
            self.current_block.proof += 1
        if not one_and_done:
            time.sleep(0)  # Simulating asynchronous operation with a timeout
            self.find_proof()

    def announce_proof(self):
        self.net.broadcast(Blockchain.PROOF_FOUND, self.current_block)

    def receive_block(self, block):
        if self.current_block and block.chain_length >= self.current_block.chain_length:
            print('Cutting over to new chain.')
            tx_set = self.sync_transactions(block)
            self.start_new_search(tx_set)
        super().receive_block(block)

    def sync_transactions(self, new_block):
        common_block = self.find_common_ancestor(self.current_block, new_block)
        old_transactions = self.collect_transactions_to_common_ancestor(self.current_block, common_block)
        new_transactions = self.collect_transactions_to_common_ancestor(new_block, common_block)
        return old_transactions - new_transactions

    def find_common_ancestor(self, block_a, block_b):
        ancestors_a = set()
        while block_a:
            ancestors_a.add(block_a.id)
            block_a = self.blocks.get(block_a.prev_block_hash)
        while block_b and block_b.id not in ancestors_a:
            block_b = self.blocks.get(block_b.prev_block_hash)
        return block_b

    def collect_transactions_to_common_ancestor(self, block, ancestor):
        transactions = set()
        while block and block != ancestor:
            transactions.update(tx.id for tx in block.transactions)
            block = self.blocks.get(block.prev_block_hash)
        return transactions

    def add_transaction(self, tx):
        tx = Blockchain.make_transaction(tx)
        self.transactions.add(tx)
        return True

