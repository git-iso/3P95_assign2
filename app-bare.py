from flask import Flask, request
import os
import multiprocessing

app = Flask(__name__)

#Write uploaded file to directory
def save_file(filename, file):
    file.save(os.path.join('received_files', filename))

#Upload path for Flash
@app.route('/upload', methods=['POST'])
#Upload files to server
def upload_file():
    file = request.files['file'] #Get file from client
    if file:
        filename = file.filename
        # Create a new process to handle the file save operation
        process = multiprocessing.Process(target=save_file, args=(filename, file))
        process.start()
        process.join()  # Wait for the process to complete
        return 'Y'
    else:
        return 'N'

#Make directory to store files if needed
if __name__ == '__main__':
    os.makedirs('received_files', exist_ok=True)
    
