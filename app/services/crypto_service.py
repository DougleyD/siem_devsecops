from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

def encrypt_data(plaintext):
    """Criptografa dados usando AES-256-GCM"""
    key = os.environ.get('ENCRYPTION_KEY').encode()  # Chave mestra deve estar nas variáveis de ambiente
    nonce = os.urandom(12)  # Gera um nonce seguro
    
    # Configura o cifrador
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Aplica padding aos dados se necessário
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    
    # Criptografa os dados
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return ciphertext, nonce

def decrypt_data(ciphertext, nonce):
    """Descriptografa dados usando AES-256-GCM"""
    key = os.environ.get('ENCRYPTION_KEY').encode()
    
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    # Descriptografa os dados
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove o padding
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    
    return plaintext