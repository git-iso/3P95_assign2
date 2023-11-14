from flask import Flask, request
import os
import multiprocessing
from cryptography.fernet import Fernet

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "app"
})

#Create tracer provider using OTLP gRPC
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

#Create meter provider using OTLP gRPC
reader = PeriodicExportingMetricReader(OTLPMetricExporter())
provider2 = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider2)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

#Track number of files uploaded
file_counter = meter.create_counter(
    "app.files",
    description="The number of files uploaded",
)

app = Flask(__name__)

#Decrypt file using Fernet
def decrypt_file(encrypted_data, key):
    with tracer.start_as_current_span("decrypt-file"):
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return decrypted_data


#Write uploaded file to directory
def save_file(filename, decrypted_data):

    with tracer.start_as_current_span("save-file"):

        with open(os.path.join('received_files', filename), 'wb') as received_file:
            
            received_file.write(decrypted_data)
            file_counter.add(1)

#Upload path for Flash
@app.route('/upload', methods=['POST'])
#Upload files to server
def upload_file():
    file = request.files['file'] #Get file from client
    encryption_key = request.form['encryption_key']
    if file:
        with tracer.start_as_current_span("upload-file"):
            filename = file.filename
            decrypted_data = decrypt_file(file.read(), encryption_key)
            # Create a new process to handle the file save operation
            process = multiprocessing.Process(target=save_file, args=(filename, decrypted_data))
            process.start()
            process.join()  # Wait for the process to complete
            print(f'FILE DECRYPTED SUCCESSFULLY')
        return 'Y'
    else:
        return 'N'

#Make directory to store files if needed
if __name__ == '__main__':
    os.makedirs('received_files', exist_ok=True)
    
