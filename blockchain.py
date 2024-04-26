"""
Notes:

Python didn't support static field, so we used class methods and properties to achieve similar behavior
Class Structure: The Blockchain class is implemented as a singleton to maintain a single instance across the application
Type Annotations: Added to improve readability and maintenance
Dataclass: Used for cleaner constructor definitions and to automatically generate __init__, __repr__, and other methods.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, ClassVar, Optional

@dataclass
class Blockchain:
    block_class: Any
    transaction_class: Any
    client_class: Any
    miner_class: Any
    pow_leading_zeroes: int = 15
    coinbase_reward: int = 25
    default_tx_fee: int = 1
    confirmed_depth: int = 6
    clients: list = field(default_factory=list)
    miners: list = field(default_factory=list)
    client_address_map: Dict[str, Any] = field(default_factory=dict)
    client_name_map: Dict[str, Any] = field(default_factory=dict)
    pow_target: int = field(init=False)
    initial_balances: Dict[str, int] = field(default_factory=dict)

    instance: ClassVar[Optional['Blockchain']] = None

    def __post_init__(self):
        if Blockchain.instance is not None:
            raise ValueError("The blockchain has already been initialized.")
        self.pow_target = (2**256 - 1) >> self.pow_leading_zeroes
        Blockchain.instance = self

    @classmethod
    def create_instance(cls, config: Dict) -> 'Blockchain':
        return cls(**config)

    @classmethod
    def get_instance(cls) -> 'Blockchain':
        if cls.instance is None:
            raise ValueError("The blockchain has not been initialized.")
        return cls.instance

    @classmethod
    def make_genesis(cls):
        g = cls.get_instance().block_class()
        for client in cls.get_instance().clients:
            client.set_genesis_block(g)
        return g

    @staticmethod
    def serialize_block(block) -> str:
        # Serialization logic here
        pass

    @staticmethod
    def deserialize_block(data: str) -> Any:
        # Deserialization logic here
        pass

    def add_client(self, client_config: Dict):
        client = self.client_class(**client_config)
        self.clients.append(client)
        self.client_address_map[client.address] = client
        self.client_name_map[client.name] = client
        if isinstance(client, self.miner_class):
            self.miners.append(client)

    def show_balances(self, name: Optional[str] = None):
        client = self.client_name_map.get(name, self.clients[0])
        if client:
            print(client.get_all_balances())

    def start_mining(self, duration: Optional[int] = None, callback: Optional[callable] = None):
        for miner in self.miners:
            miner.start_mining()
        if duration:
            time.sleep(duration / 1000)
            if callback:
                callback()
