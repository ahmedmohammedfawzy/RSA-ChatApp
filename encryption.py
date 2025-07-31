# isprime uses probabilistic test like Miller-Rabin, which is suitable for large primes
from sympy import isprime
# generate cryptographically secure random numbers
import secrets
import math

def get_random_prime(bits=2048):
    while True:
        num = secrets.randbits(bits)
        if isprime(num):
            return num

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
print(f"n = {n}")

phi = (p - 1) * (q - 1)
print(f"φ(n) = ", phi)
e = 65537

if math.gcd(e, phi) != 1:
    raise ValueError("e and phi(n) are not coprime.")

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

d = modinv(e,phi)
print("d = ",d)
def message_to_single_int(message):
    # Encode the string to bytes UTF-8
    byte_message = message.encode('utf-8')
    # Convert bytes to an integer
    # 'big'  means the most significant byte is at the beginning
    numerical_value = int.from_bytes(byte_message, 'big', signed=False)
    return numerical_value

#test message
m = message_to_single_int("hello")

ciphertext = pow(m,e,n)
print(ciphertext)

decrypted = pow(ciphertext,d,n)
print(decrypted)

message_bytes = decrypted.to_bytes((decrypted.bit_length() + 7) // 8, byteorder='big')
original_message = message_bytes.decode('utf-8')
print(original_message)