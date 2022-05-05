import os

def make_random_password(length=12, symbols='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@$^_+&'):
    password = []
    for i in map(lambda x: int(len(symbols)*x/255.0), os.urandom(length)):
        password.append(symbols[i])
    return ''.join(password)