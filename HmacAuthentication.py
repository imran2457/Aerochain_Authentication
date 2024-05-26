import hashlib
import hmac
import time
import os

def generate_nonce():
    return os.urandom(16)  # Generate a 16-byte nonce

def hmac_hash(key, message, hash_func=hashlib.sha256):
    return hmac.new(key, message, hash_func).digest()

def read_secret_key_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as f:
        secret_key = f.read().strip()
    
    return secret_key

def authenticate_node(secretKeydirectory):
    #key = b'secret_key'  # Shared secret key between Device A and Device B

    secret_key = read_secret_key_from_file(secretKeydirectory + "/secret_key.txt")

    print("Authentication begins...")
    sk = input("Enter the secret key: " )

    if sk == secret_key :            
            key = secret_key.encode()
            # Step 1: Device A to Device B Request
            device_a = b"ExistingNode"
            nonce_a = generate_nonce()
            timestamp_a = int(time.time())
            message_a = device_a + nonce_a + str(timestamp_a).encode()
            hmac_a = hmac_hash(key, message_a)
            device_a_message = (device_a, nonce_a, timestamp_a, hmac_a)

            print(f"Existing device to Incoming device: {device_a_message}")

            # Step 2: Device B Response
            received_device, received_nonce, received_timestamp, received_hmac = device_a_message

            # Verify HMAC and timestamp
            expected_hmac = hmac_hash(key, received_device + received_nonce + str(received_timestamp).encode())
            if received_hmac == expected_hmac and abs(int(time.time()) - received_timestamp) < 60:
                nonce_b = generate_nonce()
                timestamp_b = int(time.time())
                message_b = b"IncomingNode" + nonce_b + str(timestamp_b).encode()
                hmac_b = hmac_hash(key, message_b)
                device_b_message = (b"IncomingNode", nonce_b, timestamp_b, hmac_b)

                print(f"Incoming device to Existing device: {device_b_message}")
            else:
                print("Incoming device: Verification failed")
                return

            # Step 3: Device A Verification and Acknowledgment
            received_device, received_nonce_b, received_timestamp_b, received_hmac_b = device_b_message

            # Verify HMAC and timestamp
            expected_hmac_b = hmac_hash(key, received_device + received_nonce_b + str(received_timestamp_b).encode())
            if received_hmac_b == expected_hmac_b and abs(int(time.time()) - received_timestamp_b) < 60:
                final_message = device_a + received_nonce_b + nonce_a + str(timestamp_a).encode() + str(received_timestamp_b).encode()
                final_hmac = hmac_hash(key, final_message)
                final_message_a = final_hmac

                print(f"Existing device to Incoming device Final: {final_message_a}")
            else:
                print("Existing device: Verification failed")
                return

            # Step 4: Device B Final Verification
            expected_final_hmac = hmac_hash(key, device_a + received_nonce_b + nonce_a + str(timestamp_a).encode() + str(received_timestamp_b).encode())
            if final_message_a == expected_final_hmac:
                print("\nIncoming device: Final authentication successful, mutual authentication achieved")
                return True
            else:
                print("Incoming device: Final verification failed")
                return False

    else:
        print("Secret key missmatched: authentication failed")
        return False


if __name__ == "__main__":
    isTrue = authenticate_node("secrec_key")
