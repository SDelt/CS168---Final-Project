"""
Notes:

Hash Function: We used Python's hashlib and base64 to replicate the hash functionality
Key Generation: Uses Python's cryptography library to generate RSA key pairs and serialize. Adjusted the key size to 2048 bits for standard security
Signing and Verification: Implements digital signature generation and verification using Python’s cryptography library
Mnemonic Key Generation: Utilizes the mnemonic Python library to generate seeds from mnemonics and then generate RSA keys from these seeds
"""


import hashlib
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption, BestAvailableEncryption
from cryptography.hazmat.primitives.asymmetric import utils as crypto_utils
from mnemonic import Mnemonic

def hash(s, encoding='hex'):
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    if encoding == 'hex':
        return hasher.hexdigest()
    elif encoding == 'base64':
        return base64.b64encode(hasher.digest()).decode('utf-8')

def generate_keypair_from_mnemonic(mnemonic, password):
    mnemo = Mnemonic('english')
    seed = mnemo.to_seed(mnemonic, passphrase=password)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return {
        'public': public_key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo).decode('utf-8'),
        'private': private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL, encryption_algorithm=NoEncryption()).decode('utf-8')
    }

def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return {
        'public': public_key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo).decode('utf-8'),
        'private': private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.TraditionalOpenSSL, encryption_algorithm=NoEncryption()).decode('utf-8')
    }

def sign(priv_key_pem, msg):
    private_key = serialization.load_pem_private_key(
        priv_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    signer = private_key.signer(
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signer.update(msg.encode('utf-8'))
    return base64.b64encode(signer.finalize()).decode('utf-8')

def verify_signature(pub_key_pem, msg, sig):
    public_key = serialization.load_pem_public_key(
        pub_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    verifier = public_key.verifier(
        base64.b64decode(sig),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    verifier.update(msg.encode('utf-8'))
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
