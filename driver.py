from blockchain import Blockchain
from miner import Miner
from fakeNet import FakeNet
from block import Block
from transaction import Transaction
from client import Client
import time
import threading

print("Starting simulation. This may take a moment...")

# Create a Blockchain instance with all necessary classes
bc = Blockchain.create_instance({
    'block_class': Block,
    'transaction_class': Transaction,
    'client_class': Client,
    'miner_class': Miner,
    'clients': [
        {'name': 'Alice', 'amount': 233},
        {'name': 'Bob', 'amount': 99},
        {'name': 'Charlie', 'amount': 67},
        {'name': 'Minnie', 'amount': 400, 'mining': True},
        {'name': 'Mickey', 'amount': 300, 'mining': True},
    ],
    'mnemonic': "antenna dwarf settle sleep must wool ocean once banana tiger distance gate great similar chief cheap dinner dolphin picture swing twenty two file nuclear",
    'net': FakeNet(),
})

# Get Alice and Bob
alice, bob = bc.get_clients('Alice', 'Bob')

# Showing the initial balances from Alice's perspective
print("Initial balances:")
alice.show_all_balances()

# Alice transfers some gold to Bob
print(f"Alice is transferring 40 gold to {bob.address}")
alice.post_transaction([{'amount': 40, 'address': bob.address}])

# Function to start mining and handle final balances
def start_mining():
    bc.start(8000, lambda: print_final_balances(alice))

# Print final balances from Alice's perspective
def print_final_balances(alice):
    print("Final balances, from Alice's perspective:")
    alice.show_all_balances()

# Start mining in a separate thread
threading.Thread(target=start_mining).start()

# Define and start late miner after a delay
def register_late_miner():
    time.sleep(2)  # Delay before starting the late miner
    donald = Miner({
        'name': "Donald",
        'starting_block': bc.genesis,
        'mining_rounds': 3000,
    })
    print("\n***Starting a late-to-the-party miner***\n")
    bc.register(donald)
    donald.initialize()

# Start the registration of the late miner in a separate thread
threading.Thread(target=register_late_miner).start()
