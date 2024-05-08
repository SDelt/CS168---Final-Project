import time
import sys
from block import Block
from transaction import Transaction
from client import Client
from miner import Miner
from utils import generate_keypair_from_mnemonic, hash, sign, verify_signature, calc_address

class Blockchain:
    instance = None
    
    MISSING_BLOCK = "MISSING_BLOCK"
    POST_TRANSACTION = "POST_TRANSACTION"
    PROOF_FOUND = "PROOF_FOUND"
    START_MINING = "START_MINING"
    
    NUM_ROUNDS_MINING = 2000
    POW_LEADING_ZEROES = 15
    COINBASE_AMT_ALLOWED = 25
    DEFAULT_TX_FEE = 1
    CONFIRMED_DEPTH = 6
    POW_BASE_TARGET = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    
    @classmethod
    def get_missing_block(cls):
        return cls.MISSING_BLOCK

    @classmethod
    def get_post_transaction(cls):
        return cls.POST_TRANSACTION

    @classmethod
    def get_proof_found(cls):
        return cls.PROOF_FOUND

    @classmethod
    def get_start_mining(cls):
        return cls.START_MINING

    @classmethod
    def get_num_rounds_mining(cls):
        return cls.NUM_ROUNDS_MINING

    @classmethod
    def get_pow_leading_zeroes(cls):
        return cls.POW_LEADING_ZEROES

    @classmethod
    def get_default_tx_fee(cls):
        return cls.DEFAULT_TX_FEE

    @classmethod
    def get_confirmed_depth(cls):
        return cls.CONFIRMED_DEPTH
        
    @classmethod
    def coinbase_amt_allowed(cls):
        return cls.COINBASE_AMT_ALLOWED

    @classmethod
    def POW_TARGET(cls):
        return cls.POW_BASE_TARGET >> cls.POW_LEADING_ZEROES

    @classmethod
    def create_instance(cls, cfg):
        cls.instance = cls(**cfg)
        cls.instance.genesis = cls.make_genesis()
        return cls.instance
    
    @staticmethod
    def deserialize_block(o):
        if isinstance(o, Blockchain.instance.block_class):
            return o

        b = Blockchain.instance.block_class()
        b.chain_length = int(o['chainLength'])
        b.timestamp = o['timestamp']

        if b.is_genesis_block():
            # Balances need to be recreated and restored in a map.
            for client_id, amount in o['balances']:
                b.balances[client_id] = amount
        else:
            b.prev_block_hash = o['prevBlockHash']
            b.proof = o['proof']
            b.reward_addr = o['rewardAddr']
            # Likewise, transactions need to be recreated and restored in a map.
            b.transactions = {}
            if 'transactions' in o:
                for tx_id, tx_json in o['transactions']:
                    tx = Blockchain.make_transaction(tx_json)
                    b.transactions[tx_id] = tx

        return b
    
    @staticmethod
    def make_genesis():
        g = Blockchain.instance.make_block('some_reward_address', None)  
        g.balances = Blockchain.instance.initial_balances.copy()
        for client in Blockchain.instance.clients:
            client.set_genesis_block(g)
        return g
        
    @staticmethod
    def make_block(*args):
        bc = Blockchain.get_instance()
        return bc.block_class(*args)

    @staticmethod
    def get_instance():
        if Blockchain.instance is None:
            Blockchain.instance = Blockchain()  # Create a new instance if not already created
        return Blockchain.instance

    @staticmethod
    def has_instance():
        return Blockchain.instance is not None
    
    @staticmethod
    def make_transaction(*args): # Get the arguments from the client and make an instance of the blockchain
        bc = Blockchain.get_instance()
        return bc._make_transaction(*args)
        
    def __init__(self, block_class=Block, transaction_class=Transaction, client_class=Client, miner_class=Miner,
                 pow_leading_zeroes=POW_LEADING_ZEROES, coinbase_reward=COINBASE_AMT_ALLOWED,
                 default_tx_fee=DEFAULT_TX_FEE, confirmed_depth=CONFIRMED_DEPTH, clients=[], mnemonic=None, net=None):
        if Blockchain.instance is not None:
            raise Exception("The blockchain has already been initialized.")
        Blockchain.instance = self
        self.block_class = block_class
        self.transaction_class = transaction_class
        self.client_class = client_class
        self.miner_class = miner_class
        self.net = net
        self.clients = []
        self.miners = []
        self.client_address_map = {}
        self.client_name_map = {}
        self.coinbase_reward = coinbase_reward
        self.default_tx_fee = default_tx_fee
        self.confirmed_depth = confirmed_depth
        self.initial_balances = {}
        self.mnemonic = mnemonic
        self.initialize_clients(clients)

    def _make_transaction(self, *args): # Hanlde the creation of the transaction
        transaction_data = args[0]  # Extracting the transaction data dictionary from args
        from_address = transaction_data.get('from')
        nonce = transaction_data.get('nonce')
        pub_key = transaction_data.get('pub_key')
        sig = transaction_data.get('sig')
        outputs = transaction_data.get('outputs')
        fee = transaction_data.get('fee', 0)  # Default fee is 0 if not provided
        data = transaction_data.get('data')
        
        if from_address is None or nonce is None or pub_key is None:
            raise ValueError("Required transaction data is missing.")
        
        return self.transaction_class(from_address, nonce, pub_key, sig=sig, outputs=outputs, fee=fee, data=data)

    def get_clients(self, *names):
        clients = []
        for name in names:
            client = self.client_name_map.get(name)
            if client:
                clients.append(client)
        return clients

    def initialize_clients(self, clients_config):
        for client_cfg in clients_config:
            if client_cfg.get('mining', False):
                client = self.miner_class(name=client_cfg['name'], password=client_cfg.get('password'),
                                          net=self.net, mining_rounds=self.NUM_ROUNDS_MINING)
            else:
                client = self.client_class(name=client_cfg['name'], password=client_cfg.get('password'), net=self.net)
            client.generate_address(self.mnemonic)
            self.register_clients(client_cfg['amount'], client)

    def register_clients(self, amount, *clients):
        for client in clients:
            self.client_address_map[client.address] = client
            if client.name:
                self.client_name_map[client.name] = client
            self.clients.append(client)
            if isinstance(client, Miner):
                self.miners.append(client)
            client.net = self.net
            self.net.register(client)
            self.initial_balances[client.address] = amount
        
    def start(self, ms=None, f=None):
    
        for miner in self.miners:
            miner.initialize()

        if ms is not None:
            time.sleep(ms / 1000)
            if f is not None:
                f()




