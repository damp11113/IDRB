from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
import numpy as np

def CV22DPG(cv2_array):
    try:
        if cv2_array is None or len(cv2_array.shape) < 3:
            print("Invalid or empty array received.")
            return None

        if len(cv2_array.shape) == 2:
            cv2_array = cv2_array[:, :, np.newaxis]

        data = np.flip(cv2_array, 2)
        data = data.ravel()
        data = np.asfarray(data, dtype='f')
        return np.true_divide(data, 255.0)
    except Exception as e:
        print("Error in CV22DPG:", e)
        return None

def calculate_speed(start_time, end_time, data_size):
    elapsed_time = end_time - start_time
    speed_kbps = (data_size / elapsed_time) / 1024  # Convert bytes to kilobytes
    return speed_kbps

def calculate_throughput(start_time, end_time, total_bytes):
    duration = end_time - start_time
    throughput_kbps = (total_bytes * 8) / (duration * 1000)
    return throughput_kbps

def limit_string_in_line(text, limit):
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        words = line.split()
        new_line = ''

        for word in words:
            if len(new_line) + len(word) <= limit:
                new_line += word + ' '
            else:
                new_lines.append(new_line.strip())
                new_line = word + ' '

        if new_line:
            new_lines.append(new_line.strip())

    return '\n'.join(new_lines)

def unpad_message(padded_message):
    padding_length = padded_message[-1]
    return padded_message[:-padding_length]

def decrypt_data(encrypted_message, password, salt, iv):
    # Derive the key from the password and salt
    key = scrypt(password, salt, key_len=32, N=2 ** 14, r=8, p=1)

    # Initialize AES cipher in CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt the message
    decrypted_message = cipher.decrypt(encrypted_message)

    # Unpad the decrypted message
    unpadded_message = unpad_message(decrypted_message)

    return unpadded_message