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
        
    def broadcast(self, msg, o):
        for address in self.clients:
            self.send_message(address, msg, o)

    def send_message(self, address, msg, o):
    
        # Convert bytes data to string
        if isinstance(o, bytes):
            o = o.decode('utf-8')

        # Convert non-dict objects to dictionary
        if not isinstance(o, dict):
            o_dict = o.__dict__
        else:
            o_dict = o

        # Convert bytes data in pub_key to string (assuming it's in PEM format)
        if 'pub_key' in o_dict and isinstance(o_dict['pub_key'], bytes):
            o_dict['pub_key'] = o_dict['pub_key'].decode('utf-8')

        # Serializing/deserializing the object to prevent cheating in single threaded mode.
        o2 = json.loads(json.dumps(o_dict))

        client = self.clients.get(address)

        def deliver():
            if client:
                client.receive_message(msg, o2)

        delay = random.random() * self.message_delay_max
        if random.random() > self.chance_message_fails:
            Timer(delay / 1000, deliver).start()



    def recognizes(self, client):
        return client.address in self.clients