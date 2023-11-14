import os
import requests
from cryptography.fernet import Fernet
import hashlib
import tempfile
import shutil

#HTTP server to send to (flask)
server_url = 'http://localhost:5000'

#Cryptography initialization
key = Fernet.generate_key()
cipher_suite = Fernet(key)

#Get SHA-256 checksum of file
def calculate_checksum(file):
    # Calculate the checksum of the file using SHA-256 (you can choose a different hash algorithm if needed)
    sha256_hash = hashlib.sha256()
    while True:
        data = file.read(65536)  # Read the file in chunks for large files
        if not data:
            break
        sha256_hash.update(data)
    return sha256_hash.hexdigest()

#Encrypt file using Fernet
def encrypt_file(file):
    encrypted_data = cipher_suite.encrypt(file.read())
    return encrypted_data

#Create copy of file for unencypted copy 
def create_temporary_copy(path):
    tmp = tempfile.NamedTemporaryFile(delete=True)
    shutil.copy2(path, tmp.name)
    return tmp

def main():

    folder_path = 'files'
    files = os.listdir(folder_path)
    for filename in files: # Get files in folder, eecrypt and send to server with checksum
        with open(os.path.join(folder_path, filename), 'rb') as file:

            checksum = calculate_checksum(file)
            file.seek(0)
            file2 = create_temporary_copy(os.path.join(folder_path, filename))
            encrypted_data = encrypt_file(file2)
            response = send_file(filename, file, encrypted_data, checksum)

            print(f'Sent {filename}, Response: {response.status_code},Hash: {checksum}')

#Send encrypted files to server alongside encryption key and unecrypted file checksum
def send_file(filename, file, encrypted_data, checksum):

    f = {

        'file': (filename, file),
        'encrypt': (encrypted_data)
       
        }

    data = {

        'encryption_key': key,
        'checksum': (checksum)
        
        }


    response = requests.post(f'{server_url}/upload', files=f, data=data)
    return response

if __name__ == '__main__':
    main()
