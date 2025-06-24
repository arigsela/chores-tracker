#!/usr/bin/env python3
"""
Script to check if a password matches a given bcrypt hash.
"""
import sys
import getpass
from passlib.context import CryptContext

# Create a CryptContext instance with bcrypt scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    return pwd_context.verify(plain_password, hashed_password)

def main():
    # The hash to check against
    bcrypt_hash = "$2b$12$SJgOhdLQVNseF.FiQeeCpOVhR9zGZR72iy.DCAhFXce4tF7/V9pvq"
    
    if len(sys.argv) > 1:
        # Password provided as command line argument
        password = sys.argv[1]
    else:
        # Prompt for password securely (without showing it on screen)
        password = getpass.getpass("Enter password to check: ")
    
    # Check if the password matches the hash
    result = verify_password(password, bcrypt_hash)
    
    if result:
        print("✅ Password matches!")
    else:
        print("❌ Password does not match.")

if __name__ == "__main__":
    main()
