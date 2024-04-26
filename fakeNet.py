import random
import json
from threading import Timer

class FakeNet:
    def __init__(self, chance_message_fails=0, message_delay=0):
        self.clients = {}
        self.chance_message_fails = chance_message_fails
        self.message_delay_max = message_delay

    def register(self, client):
        self.clients[client.address] = client

    def broadcast(self, msg, o):
        for address in self.clients:
            self.send_message(address, msg, o)

    def send_message(self, address, msg, o):
        if random.random() > self.chance_message_fails:
            delay = random.random() * self.message_delay_max
            Timer(delay / 1000, self.deliver_message, [address, msg, o]).start()

    def deliver_message(self, address, msg, o):
        client = self.clients.get(address)
        if client:
            client.receive_message(msg, o)

    def recognizes(self, client):
        return client.address in self.clients

