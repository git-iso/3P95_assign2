from flask import Flask, request
import os
import multiprocessing
import hashlib

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

#Verify checksum of file by comparing SHA-256 hashes
def verify_checksum(file, checksum):

    with tracer.start_as_current_span("verify-checksum"):
        # Verify the checksum of the received file
        sha256_hash = hashlib.sha256()
        while True:
            data = file.read(65536)
            if not data:
                break
            sha256_hash.update(data)
        calculated_checksum = sha256_hash.hexdigest()
        return calculated_checksum == checksum

#Write uploaded file to directory
def save_file(filename, file):

    with tracer.start_as_current_span("save-file"):
    
        file.save(os.path.join('received_files', filename))
        file_counter.add(1)

#Upload path for Flash
@app.route('/upload', methods=['POST'])
#Upload files to server
def upload_file():

    with tracer.start_as_current_span("upload-file"):
        
        file = request.files['file'] #Get file from client
        read = request.form['checksum']
    
        if file:

            filename = file.filename

            if verify_checksum(file, read):
                # Create a new process to handle the file save operation
                process = multiprocessing.Process(target=save_file, args=(filename, file))
                process.start()
                process.join()  # Wait for the process to complete
                print(f'FILE CHECKSUM MATCHES: {read}')
                return 'Y'
            else:
                print(f'FILE CHECKSUM DOES NOT MATCH: {read}')
                return 'N'
        else:
            return 'N'

#Make directory to store files if needed
if __name__ == '__main__':
    os.makedirs('received_files', exist_ok=True)
    
