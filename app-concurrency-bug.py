from flask import Flask, request
import os
import concurrent.futures
from random import randint
from time import sleep

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

#Write uploaded file to directory
def save_file(filename, file):

    with tracer.start_as_current_span("save-file"):
        
        file.save(os.path.join('received_files', filename))
        file_counter.add(1)

#Upload path for Flash
@app.route('/upload', methods=['POST'])
#Upload files to server
def upload_file():
    file = request.files['file'] #Get file from client
    if file:
        if randint(0,10) < 3:
            sleep(2)
        filename = file.filename
        with tracer.start_as_current_span("upload-file"):
            # Create a new process to handle the file save operation
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(save_file, filename, file)
        return 'Y'
    else:
        return 'N'

#Make directory to store files if needed
if __name__ == '__main__':
    os.makedirs('received_files', exist_ok=True)
    
