import hashlib
from dilithium_py.ml_dsa import ML_DSA_65

class MLDSA:
    """ML-DSA-65 Digital Signature Algorithm
    This is a replacement for the DSA class in Hyperion.
    """
    
    def __init__(self, curve=None):
        self.curve = curve  # Kept ONLY for API compatibility
    
    def keygen(self):
        """Generates an ML-DSA-65 keypair."""
        public_key, secret_key = ML_DSA_65.keygen()
        signing_key = MLDSASigningKey(secret_key, public_key)
        verification_key = MLDSAVerificationKey(public_key)
        return signing_key, verification_key
    
    def sign(self, signing_key, message):
        """Signs a message using ML-DSA-65."""
        message_bytes = self._to_bytes(message)
        signature = ML_DSA_65.sign(signing_key.secret_key, message_bytes)
        return signature
    
    def verify(self, verification_key, signature, message):
        """Verifies an ML-DSA-65 signature. Returns 1 if valid, 0 otherwise."""
        message_bytes = self._to_bytes(message)
        try:
            is_valid = ML_DSA_65.verify(verification_key.public_key, message_bytes, signature)
            return 1 if is_valid else 0
        except Exception as e:
            print(f"[PQC] Verification error: {e}")
            return 0
    
    def _to_bytes(self, message):
        """Convert message types to bytes."""
        if hasattr(message, '__int__'):
            message = str(int(message))
        if isinstance(message, str):
            message = message.encode('UTF-8')
        if not isinstance(message, bytes):
            message = str(message).encode('UTF-8')
        return message


class MLDSASigningKey:
    """Wrapper for ML-DSA signing key (secret key + public key).
    This mimics the interface of PyCryptodome's ECC key objects.
    """
    
    def __init__(self, secret_key, public_key):
        self.secret_key = secret_key
        self._public_key = public_key
    
    def public_key(self):
        return MLDSAVerificationKey(self._public_key)


class MLDSAVerificationKey:
    """Wrapper for ML-DSA verification key (public key only)."""
    
    def __init__(self, public_key):
        self.public_key = public_key
    
    @property
    def pointQ(self):
        return _PointWrapper(self.public_key)


class _PointWrapper:  
    def __init__(self, public_key):
        self._public_key = public_key
    
    @property
    def xy(self):
        h = hashlib.sha256(self._public_key).digest()
        x = int.from_bytes(h[:16], 'big')
        y = int.from_bytes(h[16:], 'big')
        return (x, y)


__all__ = ['MLDSA', 'MLDSASigningKey', 'MLDSAVerificationKey']
