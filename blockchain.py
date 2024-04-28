"""
Authors: Elijah Carter & Johnson Bao
Date: 4/25/2024
Last modified:  4/26/2024
Version: 1.0

Modifications from node.js:
- Python didn't support static field, so we used class methods and properties to achieve similar behavior
- Class Structure: The Blockchain class is implemented as a singleton to maintain a single instance across the application
- Type Annotations: Added to improve readability and maintenance
- Dataclass: Used for cleaner constructor definitions and to automatically generate __init__, __repr__, and other methods.

How to test:
- must have cryptography and mnemonic installed
- add the tester stubs and config to the file
- run pythong blockchain.py

Average runtime:
Days              : 0
Hours             : 0
Minutes           : 0
Seconds           : 0
Milliseconds      : 143
Ticks             : 1430658
TotalDays         : 1.65585416666667E-06
TotalHours        : 3.97405E-05
TotalMinutes      : 0.00238443
TotalSeconds      : 0.1430658
TotalMilliseconds : 143.0658
"""

from typing import Any, Dict, List, Type
import time

# Network message constants
MISSING_BLOCK = "MISSING_BLOCK"
POST_TRANSACTION = "POST_TRANSACTION"
PROOF_FOUND = "PROOF_FOUND"
START_MINING = "START_MINING"

# Constants for mining
NUM_ROUNDS_MINING = 2000

# Constants related to proof-of-work target
POW_BASE_TARGET = 2**256 - 1
POW_LEADING_ZEROES = 15

# Constants for mining rewards and default transaction fees
COINBASE_AMT_ALLOWED = 25
DEFAULT_TX_FEE = 1

# If a block is 6 blocks older than the current block, it is considered
# confirmed, for no better reason than that is what Bitcoin does.
# Note that the genesis block is always considered to be confirmed.
CONFIRMED_DEPTH = 6


class Blockchain:
    instance = None

    @classmethod
    def get_MISSING_BLOCK(cls):
        return MISSING_BLOCK

    @classmethod
    def get_POST_TRANSACTION(cls):
        return POST_TRANSACTION

    @classmethod
    def get_PROOF_FOUND(cls):
        return PROOF_FOUND

    @classmethod
    def get_START_MINING(cls):
        return START_MINING

    @classmethod
    def get_NUM_ROUNDS_MINING(cls):
        return NUM_ROUNDS_MINING

    @classmethod
    def get_POW_TARGET(cls):
        bc = cls.get_instance()
        return bc.pow_target

    @classmethod
    def get_COINBASE_AMT_ALLOWED(cls):
        bc = cls.get_instance()
        return bc.coinbase_reward

    @classmethod
    def get_DEFAULT_TX_FEE(cls):
        bc = cls.get_instance()
        return bc.default_tx_fee

    @classmethod
    def get_CONFIRMED_DEPTH(cls):
        bc = cls.get_instance()
        return bc.confirmed_depth

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            raise ValueError("The blockchain has not been initialized.")
        return cls.instance

    @classmethod
    def has_instance(cls):
        return cls.instance is not None

    @classmethod
    def make_genesis(cls):
        g = cls.make_block()

        bc = cls.get_instance()

        g.balances = dict(bc.initial_balances)

        for client in bc.clients:
            client.set_genesis_block(g)

        return g

    @classmethod
    def deserialize_block(cls, o):
        if isinstance(o, cls.instance.block_class):
            return o

        b = cls.instance.block_class()
        b.chain_length = int(o['chain_length'])
        b.timestamp = o['timestamp']

        if b.is_genesis_block():
            b.balances = {client_id: amount for client_id, amount in o['balances']}
        else:
            b.prev_block_hash = o['prev_block_hash']
            b.proof = o['proof']
            b.reward_addr = o['reward_addr']
            b.transactions = {tx_id: cls.make_transaction(tx_json) for tx_id, tx_json in o['transactions'].items()}

        return b

    @classmethod
    def make_block(cls, *args):
        bc = cls.get_instance()
        return bc.make_block(*args)

    @classmethod
    def make_transaction(cls, *args):
        bc = cls.get_instance()
        return bc.make_transaction(*args)

    @classmethod
    def create_instance(cls, cfg):
        cls.instance = Blockchain(**cfg)
        cls.instance.genesis = cls.make_genesis()
        return cls.instance

    def __init__(self, block_class, transaction_class, client_class, miner_class, pow_leading_zeroes=POW_LEADING_ZEROES, coinbase_reward=COINBASE_AMT_ALLOWED, default_tx_fee=DEFAULT_TX_FEE, confirmed_depth=CONFIRMED_DEPTH, clients=None, mnemonic=None, net=None):
        if Blockchain.instance is not None:
            raise ValueError("The blockchain has already been initialized.")

        self.block_class = block_class
        self.transaction_class = transaction_class
        self.client_class = client_class
        self.miner_class = miner_class

        self.clients = []
        self.miners = []
        self.client_address_map = {}
        self.client_name_map = {}
        self.net = net

        self.pow_leading_zeroes = pow_leading_zeroes
        self.coinbase_reward = coinbase_reward
        self.default_tx_fee = default_tx_fee
        self.confirmed_depth = confirmed_depth

        self.pow_target = POW_BASE_TARGET >> pow_leading_zeroes

        self.initial_balances = {}

        if mnemonic is None:
            from bip39 import generate_mnemonic
            self.mnemonic = generate_mnemonic(256)
        else:
            self.mnemonic = mnemonic

        for client_cfg in clients:
            print(f"Adding client {client_cfg['name']}")
            
            if client_cfg.get('mining'):
                client = self.miner_class(name=client_cfg['name'], password=client_cfg.get('password', f"{client_cfg['name']}_pswd"), net=self.net, mining_rounds=client_cfg['mining_rounds'])
                client.generate_address(self.mnemonic)
                self.miners.append(client)
            else:
                print("Error is here in blockchain.py line 197, the following HERE does not print")
                client = self.client_class(name=client_cfg['name'], password=client_cfg.get('password', f"{client_cfg['name']}_pswd"), net=self.net)
                print("HERE")
                client.generate_address(self.mnemonic)

            self.client_address_map[client.address] = client
            if client.name:
                self.client_name_map[client.name] = client

            self.clients.append(client)
            self.net.register(client)

            self.initial_balances[client.address] = client_cfg['amount']




