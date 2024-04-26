"""
Authors: Elijah Carter & Johnson Bao
Date: 4/25/2024
Last modified:  4/25/2024
Version: 1.0

Modifications from node.js:
- hash_val Method: We used Python's hashlib for hashing
- Class Definition and Constructor: Use Python's __init__ method to initialize new instances.
- Attributes: Convert properties like this.prevBlockHash to self.prev_block_hash.
- Methods: Convert functions like isGenesisBlock to is_genesis_block.
- Utility Functions: Functions from utils.js, such as hash, will need to be either implemented in Python or replaced with Python standard libraries (like hashlib).
- Serialization: Adjust the serialization approach to use Python's json module.

How to test:
- must have cryptography and mnemonic installed
- add the tester stubs and config to the file
- run pythong block.py

Average runtime:
Days              : 0
Hours             : 0
Minutes           : 0
Seconds           : 0
Milliseconds      : 281
Ticks             : 2819512
TotalDays         : 3.26332407407407E-06
TotalHours        : 7.83197777777778E-05
TotalMinutes      : 0.00469918666666667
TotalSeconds      : 0.2819512
TotalMilliseconds : 281.9512

"""

import time
import json
from blockchain import Blockchain
from collections import defaultdict
import hashlib
from utils import hash as utils_hash

class Block:
    def __init__(self, reward_addr, blockchain, prev_block=None, target=None, coinbase_reward=None):
        self.blockchain = blockchain  # Pass the instance of Blockchain
        self.prev_block_hash = prev_block.hash_val() if prev_block else None
        self.target = target if target else blockchain.pow_target  # Access pow_target from the instance
        self.balances = defaultdict(int, (prev_block.balances.copy() if prev_block else {}))
        self.next_nonce = defaultdict(int, (prev_block.next_nonce.copy() if prev_block else {}))
        self.chain_length = prev_block.chain_length + 1 if prev_block else 0
        self.timestamp = int(time.time())
        self.reward_addr = reward_addr
        self.coinbase_reward = coinbase_reward if coinbase_reward else blockchain.coinbase_reward  # Access coinbase_reward from the instance
        self.transactions = {}
        self.total_rewards = 0

    def is_genesis_block(self):
        return self.chain_length == 0

    def has_valid_proof(self):
        hashed = self.hash_val()
        return int(hashed, 16) < self.target

    def serialize(self):
        block_info = {
            "prev_block_hash": self.prev_block_hash,
            "chain_length": self.chain_length,
            "timestamp": self.timestamp,
            "transactions": list(self.transactions.values()),
            "reward_addr": self.reward_addr,
            "coinbase_reward": self.coinbase_reward
        }
        return json.dumps(block_info, default=lambda o: o.__dict__, sort_keys=True)

    def hash_val(self):
        return utils_hash(self.serialize())

    def add_transaction(self, tx, client=None):
        if tx.id in self.transactions:
            if client:
                client.log(f'Duplicate transaction {tx.id}.')
            return False
        elif not tx.valid_signature():
            if client:
                client.log(f'Invalid signature for transaction {tx.id}.')
            return False
        elif not self.sufficient_funds(tx):
            if client:
                client.log(f'Insufficient funds for transaction {tx.id}.')
            return False

        self.transactions[tx.id] = tx
        return True

    def sufficient_funds(self, tx):
        return tx.total_output() <= self.balance_of(tx.from_address)

    def balance_of(self, address):
        return self.balances.get(address, 0) + (self.coinbase_reward if address == self.reward_addr else 0)

    def rerun(self, prev_block):
        self.balances = defaultdict(int, prev_block.balances.copy())
        self.next_nonce = defaultdict(int, prev_block.next_nonce.copy())

        self.balances[self.reward_addr] += prev_block.total_rewards

        for tx in self.transactions.values():
            if not self.add_transaction(tx):
                return False
        return True

    def total_rewards(self):
        return sum(tx.fee for tx in self.transactions.values()) + self.coinbase_reward
