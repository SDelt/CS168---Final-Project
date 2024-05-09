import json
import datetime
from utils import hash as utils_hash
from collections import defaultdict

class Block:
    def __init__(self, reward_addr, prev_block, target=None, coinbase_reward=None):
        from blockchain import Blockchain
        self.prev_block_hash = prev_block.hash_val() if prev_block else None
        
        self.target = target if target is not None else Blockchain.POW_TARGET()
        self.coinbase_reward = coinbase_reward if coinbase_reward is not None else Blockchain.coinbase_amt_allowed()
        
        self.balances = defaultdict(int, prev_block.balances if prev_block else {})
        self.next_nonce = defaultdict(int, prev_block.next_nonce if prev_block else {})
        self.transactions = {}
        self.chain_length = prev_block.chain_length + 1 if prev_block else 0
        self.timestamp = datetime.datetime.now().timestamp()
        self.reward_addr = reward_addr

        if prev_block and prev_block.reward_addr:
            winner_balance = self.balances[prev_block.reward_addr]
            self.balances[prev_block.reward_addr] = winner_balance + self.total_rewards()


    def is_genesis_block(self):
        return self.chain_length == 0

    def has_valid_proof(self):
        h = utils_hash(self.serialize())
        n = int('0x' + h, 16)
        return n < self.target

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def hash_val(self):
        return utils_hash(self.serialize())

    @property
    def id(self):
        return self.hash_val()

    def add_transaction(self, tx, client=None):
        if tx.id in self.transactions:
            if client:
                client.log(f"Duplicate transaction {tx.id}.")
            return False
        elif tx.sig is None:
            if client:
                client.log(f"Unsigned transaction {tx.id}.")
            return False
        elif not tx.valid_signature():
            if client:
                client.log(f"Invalid signature for transaction {tx.id}.")
            return False
        elif not tx.sufficient_funds(self):
            if client:
                client.log(f"Insufficient gold for transaction {tx.id}.")
            return False

        nonce = self.next_nonce[tx.from_addr]
        if tx.nonce < nonce:
            if client:
                client.log(f"Replayed transaction {tx.id}.")
            return False
        elif tx.nonce > nonce:
            if client:
                client.log(f"Out of order transaction {tx.id}.")
            return False
        else:
            self.next_nonce[tx.from_addr] = nonce + 1

        self.transactions[tx.id] = tx
        self.balances[tx.from_addr] -= tx.total_output()

        for output in tx.outputs:
            self.balances[output.address] += output.amount

        return True

    def rerun(self, prev_block):
        self.balances = defaultdict(int, prev_block.balances)
        self.next_nonce = defaultdict(int, prev_block.next_nonce)
        if prev_block.reward_addr:
            winner_balance = self.balances[prev_block.reward_addr]
            self.balances[prev_block.reward_addr] = winner_balance + self.total_rewards()

        success = True
        for tx in self.transactions.values():
            if not self.add_transaction(tx):
                success = False
                break
        return success

    def balance_of(self, addr):
        return self.balances.get(addr, 0)

    def total_rewards(self):
        total_fees = sum(tx.fee for tx in self.transactions.values())
        coinbase_reward = self.coinbase_reward
        total_rewards = total_fees + coinbase_reward
        return total_rewards

    def contains(self, tx):
        return tx.id in self.transactions
        
    def deduct_balance(self, addr, amount):
        self.balances[addr] -= amount
    
    def add_to_balance(self, addr, amount):
        self.balances[addr] += amount
