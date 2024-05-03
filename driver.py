import time
from blockchain import Blockchain
from miner import Miner
from fakeNet import FakeNet

print("Starting simulation.  This may take a moment...")

# Creating genesis block
bc = Blockchain.create_instance({
    "clients": [
        {"name": 'Alice', "amount": 233},
        {"name": 'Bob', "amount": 99},
        {"name": 'Charlie', "amount": 67},
        {"name": 'Minnie', "amount": 400, "mining": True},
        {"name": 'Mickey', "amount": 300, "mining": True},
    ],
    "mnemonic": "antenna dwarf settle sleep must wool ocean once banana tiger distance gate great similar chief cheap dinner dolphin picture swing twenty two file nuclear",
    "net": FakeNet()
})

# Get Alice and Bob
alice, bob = bc.get_clients('Alice', 'Bob')

# Showing the initial balances from Alice's perspective, for no particular reason.
print("Initial balances:")
alice.show_all_balances()

# The miners will start mining blocks when start is called.  After 8 seconds,
# the code will terminate and show the final balances from Alice's perspective.
bc.start(8000)

# Alice transfers some money to Bob.
print(f"Alice is transferring 40 gold to {bob.address}")
alice.post_transaction([{"amount": 40, "address": bob.address}])

time.sleep(2)

# Late miner - Donald has more mining power, represented by the miningRounds.
# (Mickey and Minnie have the default of 2000 rounds).
donald = Miner({
    "name": "Donald",
    "startingBlock": bc.genesis,
    "miningRounds": 3000,
})

print()
print("***Starting a late-to-the-party miner***")
print()
bc.register(donald)
donald.initialize()

time.sleep(9)  # Waiting for the blockchain to finish mining
print("Final balances, from Alice's perspective:")
alice.show_all_balances()