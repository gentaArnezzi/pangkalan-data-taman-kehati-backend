#!/usr/bin/env python3
"""
Test script to verify the password truncation fix for bcrypt errors.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_password_truncation():
    """Test that password truncation works properly"""
    from app.auth.utils import get_password_hash, verify_password
    
    print("Testing password truncation fix...")
    
    # Test with a long password that exceeds 72 bytes
    long_password = "a" * 80  # This will exceed bcrypt's 72-byte limit
    short_password = "short_password"
    
    print(f"Testing with long password (length: {len(long_password)})")
    try:
        # Hash the long password - this should not raise an error after the fix
        hashed_long = get_password_hash(long_password)
        print("✓ Successfully hashed long password")
        
        # Verify the long password
        is_valid = verify_password(long_password, hashed_long)
        print(f"✓ Password verification for long password: {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            print("✗ ERROR: Password verification failed for long password")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: Failed to hash or verify long password: {e}")
        return False
    
    print(f"Testing with short password (length: {len(short_password)})")
    try:
        # Hash the short password
        hashed_short = get_password_hash(short_password)
        print("✓ Successfully hashed short password")
        
        # Verify the short password
        is_valid = verify_password(short_password, hashed_short)
        print(f"✓ Password verification for short password: {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            print("✗ ERROR: Password verification failed for short password")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: Failed to hash or verify short password: {e}")
        return False
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_password_truncation()
    if not success:
        print("\n✗ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✓ All tests passed successfully!")