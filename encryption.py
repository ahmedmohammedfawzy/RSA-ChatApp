import secrets
import random
import hashlib
import os

def is_prime(n, k=5):
    """Miller-Rabin primality test (probabilistic)"""
    if n <= 1:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as d*2^r
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Witness loop
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_prime(bit_length):
    """Generate large prime number"""
    while True:
        num = secrets.randbits(bit_length)
        num |= (1 << bit_length - 1) | 1  # Ensure high bit set and odd
        if is_prime(num):
            return num

def gcd(a, b):
    """Euclidean algorithm for GCD"""
    while b:
        a, b = b, a % b
    return a

def mod_inverse(e, phi):
    """Extended Euclidean algorithm for modular inverse"""
    # d*e ≡ 1 mod phi
    old_r, r = e, phi
    old_s, s = 1, 0
    old_t, t = 0, 1

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    if old_r != 1:
        return None  # Inverse doesn't exist
    return old_s % phi

def generate_keys(bit_length=1024, _p=None, _q=None):
    """Generate RSA public and private keys"""
    # Step 1: Generate two large primes
    p = generate_prime(bit_length // 2)
    q = generate_prime(bit_length // 2)
    while p == q:
        q = generate_prime(bit_length // 2)

    if _p != None and _q != None:
        p = _p
        q = _q

    # Step 2: Compute modulus n
    n = p * q

    # Step 3: Compute Euler's totient
    phi = (p - 1) * (q - 1)

    # Step 4: Choose public exponent e
    e = 65537
    while gcd(e, phi) != 1:
        e = random.randint(2, phi - 1)

    # Step 5: Compute private exponent d
    d = mod_inverse(e, phi)

    return (e, n), (d, n)  # Public key, Private key

def mgf1(seed: bytes, length: int):
    """Mask Generation Function 1 based on SHA-256"""
    counter = 0
    output = b""
    #looping to get desired random length output
    while len(output) < length:
        C = counter.to_bytes(4, byteorder='big')
        output += hashlib.sha256(seed + C).digest()
        counter += 1
    #This return format handles cases where the last hash append made the output longer than needed
    return output[:length]

def oaep_encode(message: bytes, k: int, label: bytes = b'') -> bytes:
    """OAEP encoding with SHA-256"""
    hLen = hashlib.sha256().digest_size
    mLen = len(message)

    if mLen > k - 2 * hLen - 2:
        raise ValueError("Message too long")

    # Hash the label
    lHash = hashlib.sha256(label).digest()

    # Generate padding string (PS)
    ps_len = k - mLen - 2 * hLen - 2
    PS = b'\x00' * ps_len

    # Concatenate DB = lHash || PS || 0x01 || message
    DB = lHash + PS + b'\x01' + message

    # Step 4: Generate random seed
    seed = os.urandom(hLen)

    # Step 5: dbMask = MGF1(seed, len(DB))
    dbMask = mgf1(seed, k - hLen - 1)

    # Step 6: maskedDB = DB ⊕ dbMask
    maskedDB = bytes(x ^ y for x, y in zip(DB, dbMask))

    # Step 7: seedMask = MGF1(maskedDB, hLen)
    seedMask = mgf1(maskedDB, hLen)

    # Step 8: maskedSeed = seed ⊕ seedMask
    maskedSeed = bytes(x ^ y for x, y in zip(seed, seedMask))

    # Step 9: Final encoded message EM = 0x00 || maskedSeed || maskedDB
    EncodedMessage = b'\x00' + maskedSeed + maskedDB

    return EncodedMessage

def oaep_decode(encoded: bytes, k: int, label: bytes = b'') -> bytes:
    """OAEP decoding with SHA-256"""
    hLen = hashlib.sha256().digest_size

    if len(encoded) != k:
        raise ValueError("Decryption error: encoded length mismatch")

    if k < 2 * hLen + 2:
        raise ValueError("Decryption error: k too small")

    Y = encoded[0]
    maskedSeed = encoded[1:hLen + 1]
    maskedDB = encoded[hLen + 1:]

    # Validate Y byte (should be 0x00)
    if Y != 0x00:
        raise ValueError("Decryption error: invalid format byte")

    # Step 1: seedMask = MGF1(maskedDB, hLen)
    seedMask = mgf1(maskedDB, hLen)

    # Step 2: seed = maskedSeed ⊕ seedMask
    seed = bytes(x ^ y for x, y in zip(maskedSeed, seedMask))

    # Step 3: dbMask = MGF1(seed, k - hLen - 1)
    dbMask = mgf1(seed, k - hLen - 1)

    # Step 4: DB = maskedDB ⊕ dbMask
    DB = bytes(x ^ y for x, y in zip(maskedDB, dbMask))

    # Step 5: Separate DB into lHash', PS, 0x01, M
    lHash = hashlib.sha256(label).digest()
    lHash_prime = DB[:hLen]

    if lHash != lHash_prime:
        raise ValueError("Decryption error: label hash mismatch")

    # Step 6: Find the position of the 0x01 byte separating PS and M
    i = hLen
    while i < len(DB):
        if DB[i] == 0x01:
            break
        elif DB[i] != 0x00:
            raise ValueError("Decryption error: invalid padding")
        i += 1
    else:
        raise ValueError("Decryption error: 0x01 not found")

    # Step 7: Return the message after 0x01
    return DB[i + 1:]

def encrypt_oaep(message: str, public_key, label: bytes = b''):
    """Encrypt message using RSA-OAEP"""
    e, n = public_key

    # Calculate key size in bytes
    k = (n.bit_length() + 7) // 8
    
    # Convert message to bytes
    message_bytes = message.encode('utf-8')
    
    # Apply OAEP padding
    padded = oaep_encode(message_bytes, k, label)
    
    # Convert padded message to integer
    m_int = int.from_bytes(padded, 'big')
    
    # RSA encryption: c ≡ m^e mod n
    c = pow(m_int, e, n)
    
    return c

def decrypt_oaep(ciphertext, private_key, label: bytes = b''):
    """Decrypt ciphertext using RSA-OAEP"""
    d, n = private_key
    
    # Calculate key size in bytes
    k = (n.bit_length() + 7) // 8
    
    # RSA decryption: m ≡ c^d mod n
    m_int = pow(ciphertext, d, n)
    
    # Convert integer back to bytes with proper padding
    padded = m_int.to_bytes(k, 'big')
    
    # Remove OAEP padding
    message_bytes = oaep_decode(padded, k, label)
    
    # Convert back to string
    return message_bytes.decode('utf-8')

# Legacy functions (without OAEP) - kept for compatibility
def encrypt(message, public_key):
    """Encrypt message using basic RSA (without OAEP)"""
    e, n = public_key
    # Convert message to integer
    m_int = int.from_bytes(message.encode(), 'big')

    # Check message length
    if m_int >= n:
        raise ValueError("Message too long for key size")

    # Encrypt: c ≡ m^e mod n
    c = pow(m_int, e, n)
    return c

def decrypt(ciphertext, private_key):
    """Decrypt ciphertext using basic RSA (without OAEP)"""
    d, n = private_key
    # Decrypt: m ≡ c^d mod n
    m_int = pow(ciphertext, d, n)

    # Convert integer back to string
    byte_length = (m_int.bit_length() + 7) // 8
    return m_int.to_bytes(byte_length, 'big').decode()

def demo():
    """Comprehensive demo of RSA with and without OAEP"""
    print("=== RSA with OAEP Demo ===\n")

    # Generate keys
    print("1. Generating RSA key pair (1024-bit)...")
    public_key, private_key = generate_keys(1024)
    e, n = public_key
    d, _ = private_key

    print(f"   Public key (e, n): ({e}, {n})")
    print(f"   Private key (d, n): ({d}, {n})")
    print(f"   Key size: {n.bit_length()} bits\n")

    # Test message
    original_message = "Hello, RSA with OAEP! This is a secure message. 🔐"
    print(f"2. Original message: '{original_message}'")
    print(f"   Message length: {len(original_message)} characters\n")

    # Test RSA with OAEP
    print("3. Testing RSA-OAEP encryption/decryption...")
    try:
        # Encrypt with OAEP
        ciphertext_oaep = encrypt_oaep(original_message, public_key)
        print(f"   Encrypted (OAEP): {ciphertext_oaep}")

        # Decrypt with OAEP
        decrypted_oaep = decrypt_oaep(ciphertext_oaep, private_key)
        print(f"   Decrypted (OAEP): '{decrypted_oaep}'")

        # Verify
        oaep_success = original_message == decrypted_oaep
        print(f"   OAEP Success: {oaep_success}\n")

    except Exception as e:
        print(f"   OAEP Error: {e}\n")
        oaep_success = False

    # Test basic RSA (for comparison)
    print("4. Testing basic RSA encryption/decryption...")
    try:
        # Encrypt without OAEP
        ciphertext_basic = encrypt(original_message, public_key)
        print(f"   Encrypted (basic): {ciphertext_basic}")

        # Decrypt without OAEP
        decrypted_basic = decrypt(ciphertext_basic, private_key)
        print(f"   Decrypted (basic): '{decrypted_basic}'")

        # Verify
        basic_success = original_message == decrypted_basic
        print(f"   Basic RSA Success: {basic_success}\n")

    except Exception as e:
        print(f"   Basic RSA Error: {e}\n")
        basic_success = False

    # Test with custom label
    print("5. Testing RSA-OAEP with custom label...")
    try:
        custom_label = b"MySecretLabel"
        ciphertext_labeled = encrypt_oaep(original_message, public_key, custom_label)
        decrypted_labeled = decrypt_oaep(ciphertext_labeled, private_key, custom_label)

        labeled_success = original_message == decrypted_labeled
        print(f"   Custom label success: {labeled_success}")
        print(f"   Label used: {custom_label}\n")

        # Test wrong label (should fail)
        try:
            wrong_decrypt = decrypt_oaep(ciphertext_labeled, private_key, b"WrongLabel")
            print("   WARNING: Wrong label should have failed!")
        except ValueError as e:
            print(f"   Correctly failed with wrong label: {e}\n")

    except Exception as e:
        print(f"   Labeled encryption error: {e}\n")

    # Test message size limits
    print("6. Testing message size limits...")
    e, n = public_key
    k = (n.bit_length() + 7) // 8  # Key size in bytes
    hLen = hashlib.sha256().digest_size  # Hash length
    max_message_length = k - 2 * hLen - 2  # Maximum message length for OAEP

    print(f"   Key size: {k} bytes ({k * 8} bits)")
    print(f"   Maximum message length (OAEP): {max_message_length} bytes")

    # Test with maximum size message
    long_message = "A" * (max_message_length - 10)  # Leave some margin
    try:
        long_cipher = encrypt_oaep(long_message, public_key)
        long_decrypt = decrypt_oaep(long_cipher, private_key)
        long_success = long_message == long_decrypt
        print(f"   Long message test ({len(long_message)} bytes): {long_success}")
    except Exception as e:
        print(f"   Long message error: {e}")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    demo()
