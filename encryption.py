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




def sha256(data):
    return hashlib.sha256(data).digest()
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

def oaep_encode(message: bytes, label: bytes = b'') -> bytes:
    k = (n.bit_length() + 7) // 8
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
    dbMask = mgf1(seed, k - hLen - 1, hashlib.sha256)

    # Step 6: maskedDB = DB ⊕ dbMask
    maskedDB = bytes(x ^ y for x, y in zip(DB, dbMask))

    # Step 7: seedMask = MGF1(maskedDB, hLen)
    seedMask = mgf1(maskedDB, hLen, hashlib.sha256)

    # Step 8: maskedSeed = seed ⊕ seedMask
    maskedSeed = bytes(x ^ y for x, y in zip(seed, seedMask))

    # Step 9: Final encoded message EM = 0x00 || maskedSeed || maskedDB
    EncodedMessage = b'\x00' + maskedSeed + maskedDB

    return EncodedMessage


def RSAencrypt(plaintext,n,e=65537):
    # Encode the string to bytes UTF-8
    byte_message = plaintext.encode('utf-8')
    # Convert bytes to an integer
    # 'big'  means the most significant byte is at the beginning
    # m is the numerical value of the message
    m = int.from_bytes(byte_message, 'big', signed=False)
    ciphertext = pow(m, e, n)
    return ciphertext

def RSAdecrypt(ciphertext,n,d):
    m = pow(ciphertext,d,n)
    message_bytes = m.to_bytes((m.bit_length() + 7) // 8, byteorder='big')
    original_message = message_bytes.decode('utf-8')
    return original_message




message = "Hello"
encrypted = RSAencrypt(oaep_encode(message))
