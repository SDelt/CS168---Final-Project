"""
Notes:

Hash Function: We used Python's hashlib and base64 to replicate the hash functionality
Key Generation: Uses Python's cryptography library to generate RSA key pairs and serialize. Adjusted the key size to 2048 bits for standard security
Signing and Verification: Implements digital signature generation and verification using Python’s cryptography library
Mnemonic Key Generation: Utilizes the mnemonic Python library to generate seeds from mnemonics and then generate RSA keys from these seeds
"""


import hashlib
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from mnemonic import Mnemonic
from cryptography.exceptions import InvalidSignature

# CRYPTO settings
HASH_ALG = hashlib.sha256
SIG_ALG = 'sha256'

def hash(s, encoding='hex'):
    hash_obj = HASH_ALG()
    hash_obj.update(s.encode())
    if encoding == 'hex':
        return hash_obj.hexdigest()
    elif encoding == 'base64':
        return hash_obj.digest().encode('base64').decode()

def generate_keypair_from_mnemonic(mnemonic, password):
    mnemonic_obj = Mnemonic("english")
    seed = mnemonic_obj.to_seed(mnemonic, passphrase=password)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=512,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return {
        'public': pem_public_key.decode(),
        'private': pem_private_key.decode()
    }

def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=512,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return {
        'public': pem_public_key.decode(),
        'private': pem_private_key.decode()
    }

def sign(priv_key_pem, msg):
    private_key = serialization.load_pem_private_key(
        priv_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    signer = private_key.sign(
        json.dumps(msg).encode() if isinstance(msg, dict) else str(msg).encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signer.finalize().hex()

def verify_signature(pub_key_pem, msg, sig):
    public_key = serialization.load_pem_public_key(
        pub_key_pem.encode(),
        backend=default_backend()
    )
    verifier = public_key.verify(
        bytes.fromhex(sig),
        json.dumps(msg).encode() if isinstance(msg, dict) else str(msg).encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    try:
        verifier.verify()
        return True
    except InvalidSignature:
        return False

def calc_address(key):
    addr = hash(key, 'base64')
    return addr

def address_matches_key(addr, pub_key):
    return addr == calc_address(pub_key)
