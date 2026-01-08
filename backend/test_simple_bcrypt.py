"""
Simple security test to isolate bcrypt issue
"""

def test_simple_bcrypt():
    try:
        import bcrypt
        
        password = "TestPass123"
        password_bytes = password.encode('utf-8')
        
        print(f"Testing password: {password}")
        print(f"Password bytes: {password_bytes}")
        print(f"Password length: {len(password_bytes)} bytes")
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        print(f"Salt generated: {salt}")
        
        hashed = bcrypt.hashpw(password_bytes, salt)
        print(f"Hash generated: {hashed}")
        
        # Verify
        is_valid = bcrypt.checkpw(password_bytes, hashed)
        print(f"Verification result: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_bcrypt()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")