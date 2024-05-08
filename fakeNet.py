import random
import json
from threading import Timer

class FakeNet:
    def __init__(self, chance_message_fails=0, message_delay=0):
        self.clients = {}
        self.chance_message_fails = chance_message_fails
        self.message_delay_max = message_delay

    def register(self, *client_list):
        for client in client_list:
            self.clients[client.address] = client
        
    def broadcast(self, address, msg, tx=None):
        if address in self.clients:  # Check if address is in the clients map
            self.send_message(self.clients[address], msg, tx)

    def send_message(self, address, msg, tx=None):
        from client import Client
        from miner import Miner
        from blockchain import Blockchain

        def deliver():
            if isinstance(address, Miner):  # Check if address is an instance of Miner
                if msg == Blockchain.START_MINING:
                    address.find_proof()
                elif msg == Blockchain.POST_TRANSACTION:
                    # self.print_message(msg) 
                    address.add_transaction(tx)
                else:
                    print("Invalid message for Miner:", msg)
            elif isinstance(address, Client):  # Check if address is an instance of Client
                if msg == Blockchain.POST_TRANSACTION:
                    # self.print_message(msg)
                    address.makeDeductions(tx)
                else:
                    print("Invalid message for Client:", msg)
            else:
                print("Address type not recognized:", type(address))

        delay = random.random() * self.message_delay_max
        if random.random() > self.chance_message_fails:
            Timer(delay / 1000, deliver).start()

    def recognizes(self, client):
        return client.address in self.clients
    
    @staticmethod    
    def print_message(msg):
        print("")
        print("*** ", msg, " ***")
        print("")