import os
import requests
import hashlib

#HTTP server to send to (flask)
server_url = 'http://localhost:5000'

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

def main():

    folder_path = 'files'
    files = os.listdir(folder_path)
    for filename in files: #Get checksum and send with file to server
        with open(os.path.join(folder_path, filename), 'rb') as file:

            checksum = calculate_checksum(file)
            file.seek(0)
            response = send_file(filename, file, checksum)
            print(f'Sent {filename}, Response: {response.status_code}, Hash: {checksum}')

#Send files and associated checksum to server
def send_file(filename, file, checksum):

    f = {

        'file': (filename, file)
       
        }

    data = {

        'checksum': (checksum)
        
    }

    response = requests.post(f'{server_url}/upload', files=f, data=data)
    return response

if __name__ == '__main__':
    main()
