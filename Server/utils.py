"""
This file is part of IDRB Project.

IDRB Project is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDRB Project is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDRB Project.  If not, see <https://www.gnu.org/licenses/>.
"""

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

def pad_message(message_bytes):
    block_size = AES.block_size
    padding_length = block_size - (len(message_bytes) % block_size)
    padding = bytes([padding_length] * padding_length)
    return message_bytes + padding

def encrypt_data(message_bytes, password):
    # Derive a key from the password
    salt = get_random_bytes(50)
    key = scrypt(password, salt, key_len=32, N=2 ** 14, r=8, p=1)

    # Generate an IV (Initialization Vector)
    iv = get_random_bytes(AES.block_size)

    # Pad the message
    padded_message = pad_message(message_bytes)

    # Initialize AES cipher in CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Encrypt the padded message
    encrypted_message = cipher.encrypt(padded_message)

    # Return the encrypted message, salt, and IV (for decryption)
    return encrypted_message, salt, iv
