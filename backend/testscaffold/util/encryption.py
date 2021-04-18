from cryptography.fernet import Fernet

ENCRYPTION_SECRET = None


def encrypt_fernet(value):
    f = Fernet(ENCRYPTION_SECRET)
    return "fernet${}".format(f.encrypt(value))


def decrypt_fernet(value):
    f = Fernet(ENCRYPTION_SECRET)
    decrypted_data = f.decrypt(value[7:])
    return decrypted_data
