import time
import sys
from block import Block
from transaction import Transaction
from client import Client
from miner import Miner
from utils import generate_keypair_from_mnemonic, hash, sign, verify_signature, calc_address

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

class Blockchain:
    instance = None
    
    MISSING_BLOCK = "MISSING_BLOCK"
    POST_TRANSACTION = "POST_TRANSACTION"
    PROOF_FOUND = "PROOF_FOUND"
    START_MINING = "START_MINING"

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
        self.pow_target = POW_BASE_TARGET >> pow_leading_zeroes
        self.coinbase_reward = coinbase_reward
        self.default_tx_fee = default_tx_fee
        self.confirmed_depth = confirmed_depth
        self.initial_balances = {}
        self.mnemonic = mnemonic
        self.initialize_clients(clients)

    @classmethod
    def create_instance(cls, cfg):
        cls.instance = cls(**cfg)
        cls.instance.genesis = cls.make_genesis()
        return cls.instance

    @staticmethod
    def make_genesis():
        # Create a new block with appropriate arguments
        g = Blockchain.instance.make_block('some_reward_address', None)  
        g.balances = Blockchain.instance.initial_balances.copy()
        for client in Blockchain.instance.clients:
            print("file: blockchain    line: 58     msg: Genesis block: ", g)
            client.set_genesis_block(g)
        return g

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
                                          net=self.net, mining_rounds=NUM_ROUNDS_MINING)
            else:
                client = self.client_class(name=client_cfg['name'], password=client_cfg.get('password'), net=self.net)
            client.generate_address(self.mnemonic)
            self.register_client(client, client_cfg['amount'])
            
            # Print client details for debugging
            print("file: blockchain.py   line: 81/82   msg: below")
            print(f"Initialized client: {client.name}, Address: {client.address}, Amount: {client_cfg['amount']}")


    def register_client(self, client, amount):
        self.client_address_map[client.address] = client
        if client.name:
            self.client_name_map[client.name] = client
        self.clients.append(client)
        self.net.register(client)
        self.initial_balances[client.address] = amount

    def make_block(self, *args):
        return self.block_class(*args)

    @staticmethod
    def make_transaction(*args): # Get the arguments from the client and make an instance of the blockchain
        bc = Blockchain.get_instance()
        return bc._make_transaction(*args)

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


    @staticmethod
    def get_instance():
        if Blockchain.instance is None:
            Blockchain.instance = Blockchain()  # Create a new instance if not already created
        return Blockchain.instance

    def start(self, ms=None, f=None):
        for miner in self.miners:
            miner.initialize()

        if ms is not None:
            time.sleep(ms / 1000)
            if f is not None:
                f()

    @staticmethod
    def has_instance():
        return Blockchain.instance is not None




