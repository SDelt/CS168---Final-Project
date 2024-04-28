'''
Modules needed:
- pip install cryptography
- pip install pycryptodome bip-utils 
'''

import hashlib
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator

def hash(s, encoding='hex'):
    h = hashlib.sha256(s.encode())
    if encoding == 'hex':
        return h.hexdigest()
    elif encoding == 'base64':
        return base64.b64encode(h.digest()).decode()

def generate_keypair_from_mnemonic(mnemonic, password):
    seed = Bip39SeedGenerator(mnemonic).Generate(password).ToHex()
    key = RSA.generate(512, randfunc=lambda n: seed[:n])  # Simplification
    private_key = key.export_key('PEM')
    public_key = key.publickey().export_key('PEM')
    return {'public': public_key, 'private': private_key}

def generate_keypair():
    key = RSA.generate(512)
    private_key = key.export_key('PEM')
    public_key = key.publickey().export_key('PEM')
    return {'public': public_key, 'private': private_key}

def sign(private_key, msg):
    if isinstance(msg, dict):
        msg = json.dumps(msg)
    key = RSA.import_key(private_key)
    h = SHA256.new(msg.encode())
    signature = pkcs1_15.new(key).sign(h)
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(public_key, msg, signature):
    if isinstance(msg, dict):
        msg = json.dumps(msg)
    key = RSA.import_key(public_key)
    h = SHA256.new(msg.encode())
    signature = base64.b64decode(signature)
    try:
        pkcs1_15.new(key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False

def calc_address(key):
    addr = hash(key, 'base64')
    return addr

def address_matches_key(addr, public_key):
    return addr == calc_address(public_key)
