# isprime uses probabilistic test like Miller-Rabin, which is suitable for large primes
from sympy import isprime
# generate cryptographically secure random numbers
import secrets
import math
import hashlib
import os

def get_random_prime(bits=2048):
    while True:
        num = secrets.randbits(bits)
        if isprime(num):
            return num
#euclidean extended algorithm
# extended_gcd(a, b) returns (gcd, x, y) such that: a * x + b * y = gcd(a, b)
def extended_gcd(a,b):
    if b == 0:
        return a, 1, 0
    gcd , x1 , y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b)* y1
    return gcd,x,y
# modular inverse
def modinv(a,m):
    gcd, x, _ = extended_gcd(a,m)
    if gcd != 1:
        raise Exception("No Modular Inverse")
    return x % m

# Option to enter values or generate random primes
choice = input("Generate random primes? (y/n): ").lower()

if choice == 'y':
    # Generate random primes with enough bits to ensure n > 256 bits
    while True:
        p = get_random_prime()  
        q = get_random_prime()  
        n = p * q
        if n.bit_length() > 256:
            break
        print("Generated n too small, regenerating...")
    
    print("Generated p:", p)
    print("Generated q:", q)
else:
    # Manual entry
    while True:
        while True:
            p = int(input("Enter the p value: "))
            if isprime(p):
                break
            print("Error: p must be a prime number.")
            
        while True:
            q = int(input("Enter the q value: "))
            if isprime(q):
                break
            print("Error: q must be a prime number.")
        
        n = p * q
        if n.bit_length() >= 256:
            break
        print(f"Error: n is only {n.bit_length()} bits (less than 256 bits). Please enter larger primes.")

print(f"Success: n is {n.bit_length()} bits (≥ 256 bits)")
print(f"n = {n}","\n")


phi = (p - 1) * (q - 1)
print(f"φ(n) = ", phi,"\n")

e = 65537
if math.gcd(e, phi) != 1:
    raise ValueError("e and phi(n) are not coprime.")

d = modinv(e,phi)
print("d = ",d,"\n")


def mgf1(seed: bytes, length: int):
    counter = 0
    output = b""
    #looping to get desired random length output
    while len(output) < length:
        C = counter.to_bytes(4, byteorder='big')
        output += hashlib.sha256(seed + C).digest()
        counter += 1
    #This return format handles cases where the last hash append made the output longer than needed
    return output[:length]

def oaep_encode(message: bytes, k:int,label: bytes = b'') -> bytes:
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
    hLen = hashlib.sha256().digest_size

    if len(encoded) != k:
        raise ValueError("Decryption error: encoded length mismatch")

    if k < 2 * hLen + 2:
        raise ValueError("Decryption error: k too small")

    Y = encoded[0]
    maskedSeed = encoded[1:hLen + 1]
    maskedDB = encoded[hLen + 1:]

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

def RSA_OAEPencrypt(message, n, e=65537):
    k = (n.bit_length() + 7) // 8  
    encoded = oaep_encode(message.encode('utf-8'), k)  
    m = int.from_bytes(encoded, 'big')
    ciphertext = pow(m, e, n)
    return ciphertext

def RSA_OAEPdecrypt(ciphertext, n, d):
    k = (n.bit_length() + 7) // 8
    m = pow(ciphertext, d, n)
    message_bytes = m.to_bytes(k, byteorder='big') 
    decoded = oaep_decode(message_bytes, k)  
    return decoded.decode('utf-8')



message = "Hello Fawzy"
ciphertext = RSA_OAEPencrypt(message, n)
print("Encrypted:", ciphertext)

plaintext = RSA_OAEPdecrypt(ciphertext, n, d)
print("Decrypted:", plaintext)