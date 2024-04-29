from blockchain import Blockchain
from miner import Miner
from fakeNet import FakeNet
import time

print("Starting simulation. This may take a moment...")

bc = Blockchain.create_instance({
    'clients': [
        {'name': 'Alice', 'amount': 233},
        {'name': 'Bob', 'amount': 99},
        {'name': 'Charlie', 'amount': 67},
        {'name': 'Minnie', 'amount': 400, 'mining': True},
        {'name': 'Mickey', 'amount': 300, 'mining': True}
    ],
    'mnemonic': "antenna dwarf settle sleep must wool ocean once banana tiger distance gate great similar chief cheap dinner dolphin picture swing twenty two file nuclear",
    'net': FakeNet(),
})

alice, bob = bc.get_clients('Alice', 'Bob')
print("Initial balances:")
alice.show_all_balances()

def simulation_end():
    print("Final balances, from Alice's perspective:")
    alice.show_all_balances()

# Using threading to simulate setTimeout
import threading
def start_simulation():
    print(f"Alice is transferring 40 gold to {bob.address}")
    alice.post_transaction([{'amount': 40, 'address': bob.address}])

    def start_late_miner():
        donald = Miner(name="Donald", net=bc.net, starting_block=bc.genesis, mining_rounds=3000)
        print()
        print("***Starting a late-to-the-party miner***")
        print()
        bc.register(donald)
        donald.initialize()

    # Start the late miner after 2 seconds
    threading.Timer(2, start_late_miner).start()

# Main simulation runs for 8 seconds
threading.Timer(8, simulation_end).start()
threading.Timer(0, start_simulation).start()
