import threading
from client import Client

class Miner(Client):
    def __init__(self, name=None, password=None, net=None, starting_block=None, key_pair=None, mining_rounds=None):
        from blockchain import Blockchain
        super().__init__(name, password, net, starting_block, key_pair)
        self.mining_rounds = mining_rounds
        self.transactions = set()

    def initialize(self):
        from blockchain import Blockchain
        self.start_new_search()
        threading.Timer(0, self.emit, args=(Blockchain.START_MINING,)).start()

    def start_new_search(self, tx_set=None):
        from blockchain import Blockchain
        tx_set = tx_set or set()
        self.current_block = Blockchain.make_block(self.address, self.last_block)

        for tx in tx_set:
            self.transactions.add(tx)

        for tx in self.transactions:
            self.current_block.add_transaction(tx, self)
        self.transactions.clear()
        self.current_block.proof = 0

    def find_proof(self, one_and_done=False):
        from blockchain import Blockchain
        pause_point = self.current_block.proof + self.mining_rounds
        while self.current_block.proof < pause_point:
            if self.current_block.has_valid_proof():
                self.log(f"found proof for block {self.current_block.chain_length}: {self.current_block.proof}")
                self.announce_proof()
                self.receive_block(self.current_block)
                break
            self.current_block.proof += 1
        if not one_and_done:
            threading.Timer(0, self.emit, args=(Blockchain.START_MINING,)).start()

    def announce_proof(self):
        from blockchain import Blockchain
        self.net.broadcast(Blockchain.PROOF_FOUND, self.current_block)

    def receive_block(self, s):
        b = super().receive_block(s)
        if b is None:
            return None

        if self.current_block and b.chain_length >= self.current_block.chain_length:
            self.log("cutting over to new chain.")
            tx_set = self.sync_transactions(b)
            self.start_new_search(tx_set)

        return b

    def sync_transactions(self, nb):
        cb = self.current_block
        cb_txs = set()
        nb_txs = set()

        while nb.chain_length > cb.chain_length:
            for tx in nb.transactions:
                nb_txs.add(tx)
            nb = self.blocks.get(nb.prev_block_hash)

        while cb and cb.id != nb.id:
            for tx in cb.transactions:
                cb_txs.add(tx)
            for tx in nb.transactions:
                nb_txs.add(tx)

            cb = self.blocks.get(cb.prev_block_hash)
            nb = self.blocks.get(nb.prev_block_hash)

        return cb_txs - nb_txs

    def add_transaction(self, tx):
        from blockchain import Blockchain
        tx = Blockchain.make_transaction(tx)
        self.transactions.add(tx)

    def post_transaction(self, *args):
        tx = super().post_transaction(*args)
        return self.add_transaction(tx)

    def log(self, message):
        print(f"{self.name}: {message}")
