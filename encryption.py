from cryptography.fernet import Fernet
import os
import base64

class DataEncryption:
    """Encrypt sensitive data before storing"""
    
    def __init__(self):
        # Get or generate encryption key
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated encryption key: {key.decode()}")
            print("Add this to your .env file as ENCRYPTION_KEY")
        else:
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt string data"""
        if not data:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt string data"""
        if not encrypted_data:
            return None
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_file(self, filepath):
        """Encrypt file contents"""
        with open(filepath, 'rb') as f:
            data = f.read()
        
        encrypted = self.cipher.encrypt(data)
        
        with open(filepath + '.enc', 'wb') as f:
            f.write(encrypted)
        
        return filepath + '.enc'
    
    def decrypt_file(self, encrypted_filepath, output_path):
        """Decrypt file contents"""
        with open(encrypted_filepath, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted = self.cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path

# Initialize global encryption instance
encryption = DataEncryption()
