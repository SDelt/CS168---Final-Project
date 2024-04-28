import random
import json
from threading import Timer

class FakeNet:
    def __init__(self, chance_message_fails=0, message_delay=0):
        self.clients = {}
        self.chance_message_fails = chance_message_fails
        self.message_delay_max = message_delay

    def register(self, *clients):
        for client in clients:
            self.clients[client.address] = client

    def broadcast(self, msg, o):
        for address in self.clients:
            self.send_message(address, msg, o)

    def send_message(self, address, msg, o):
        if not isinstance(o, dict):
            raise ValueError(f"Expecting a dictionary, but got a {type(o).__name__}")
        
        # Serializing/deserializing the object to prevent cheating in single threaded mode.
        o2 = json.loads(json.dumps(o))
        
        client = self.clients.get(address)
        
        def deliver():
            if client:
                client.receive_message(msg, o2)

        delay = random.random() * self.message_delay_max
        if random.random() > self.chance_message_fails:
            Timer(delay / 1000, deliver).start()

    def recognizes(self, client):
        return client.address in self.clients
