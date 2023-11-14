import os
import requests

#HTTP server to send to (flask)
server_url = 'http://localhost:5000'


def main():

    folder_path = 'files'
    files = os.listdir(folder_path)
    for filename in files: # Get files in folder and send to server
        with open(os.path.join(folder_path, filename), 'rb') as file:

            response = send_file(filename, file)
            print(f'Sent {filename}, Response: {response.status_code}')

#Send files to server 
def send_file(filename, file):

    f = {

        'file': (filename, file)
       
        }


    response = requests.post(f'{server_url}/upload', files=f)
    return response

if __name__ == '__main__':
    main()
