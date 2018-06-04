import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random


KEY_PASSWORD = b'EsTa_3s-L4_P4SsW0rD____$1n_3ll4-N0-S3_Pu3d3-Desencriptar---@#$@#$'  # <<<----- Poner una clave y anotar :D

def encrypt(source, encode=True):
    key = SHA256.new(KEY_PASSWORD).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
    source += bytes([padding]) * padding  # Python 2.x: source += chr(padding) * padding
    data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
    return base64.b64encode(data).decode("ascii") if encode else data

def decrypt(source, decode=True):
    if decode:
        source = base64.b64decode(source.encode("ascii"))
    key = SHA256.new(KEY_PASSWORD).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[:AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])  # decrypt
    padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
    if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
        raise ValueError("Invalid padding...")
    return data[:-padding]  # remove the padding