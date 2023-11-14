import os
import requests
from cryptography.fernet import Fernet

#HTTP server to send to (flask)
server_url = 'http://localhost:5000'

#Cryptography initialization
key = Fernet.generate_key()
cipher_suite = Fernet(key)

#Encrypt file using Fernet
def encrypt_file(file):
    encrypted_data = cipher_suite.encrypt(file.read())
    return encrypted_data

def main():

    folder_path = 'files'
    files = os.listdir(folder_path)
    for filename in files: # Get files in folder and send to server
        with open(os.path.join(folder_path, filename), 'rb') as file:

            encrypted_data = encrypt_file(file)
            response = send_file(filename, encrypted_data)
            print(f'Sent {filename}, Response: {response.status_code}')

#Send files with encryption key to server
def send_file(filename, file):

    f = {

        'file': (filename, file)
       
        }

    data = {

        'encryption_key': key
        
        }


    response = requests.post(f'{server_url}/upload', files=f, data=data)
    return response

if __name__ == '__main__':
    main()
