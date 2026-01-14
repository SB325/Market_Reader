from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
SystemMetricsInstrumentor().instrument() # Automatically collects CPU, memory, etc.

# Traces, Metrics
import time
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter # For OTLP/gRPC
# Logs
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from enum import Enum

class otel_tracer():
    # Configure the service name and other resource attributes
    resource = Resource() # service name should already be set by OTEL_SERVICE_NAME
    # Set the global tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    # Configure the OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True) 
    # Add a span processor to the provider
    provider.add_span_processor(BatchExportSpanProcessor(otlp_exporter))
    # Acquire a tracer for use in your application
    tracer = trace.get_tracer(__name__)

    def set_span(self, span_name: str):
        print(f"Tracing span: {span_name}.")
        return tracer.start_as_current_span(span_name)

# ===============================
class meterType(Enum):
    counter = "AsynchronousCounter"
    upDownCounter = "AsynchronousUpDownCounter"
    gauge = "ObservableGauge"
    histogram = "Histogram"
    
class otel_metrics():
    # https://opentelemetry-python.readthedocs.io/en/latest/api/metrics.html
    # 1. Configure the MeterProvider with a Console Exporter (not necessary)
    # The ConsoleMetricExporter prints metrics to the console for demonstration purposes.
    metric_reader = PeriodicExportingMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    # Sets the global default meter provider
    metrics.set_meter_provider(meter_provider)
    meter_objects = {
                'counters': [], 
                'upDownCounters': [], 
                'gauges': [],
                'histograms': [],
            }
    
    def create_meter(self, 
            meter_name : str, 
            meter_id: str,
            meter_type: meterType,
            description: str):
        # 2. Acquire a meter
        # A meter is associated with a specific name (e.g., application/library name) and version.
        meter = metrics.get_meter(meter_name, version="1.0.0")

        if meterType.counter
            # 3. Create a synchronous instrument (Counter)
            # Counters are used for values that only increase, like the number of requests or errors.
            self.meter_objects['counters'].append(
                meter.create_counter(
                    meter_id,  # ex: "http.server.requests.total",
                    unit="1",
                    description=description,
                )
            )
        if meterType.upDownCounter:
            pass
            self.meter_objects['upDownCounters'].append(
                meter.create_up_down_counter(
                    meter_id,  # ex: "http.server.requests.total",
                    unit="1",
                    description=description,
                )
            )
        # if meterType.gauge:
        #     pass
        #     self.meter_objects['gauges'].append(
        #         meter.create_gauge(
        #             meter_id,  # ex: "http.server.requests.total",
        #             unit="1",
        #             description=description,
        #         )
        #     )
        if meterType.histogram:
            pass
            self.meter_objects['histograms'].append(
                meter.create_histogram(
                    meter_id,  # ex: "http.server.requests.total",
                    unit="1",
                    description=description,
                )
            )
    
    def update_counter(self, increase_by: int = 1, counter_name, attributes: dict = None):
        counter = [val for val in self.meter_objects['counters']
                if counter_name in val.name]
        if not counter:
            print(f"Counter name {counter_name} not found.")

        counter[0].add(increase_by, attributes)

    def update_up_down_counter(self, change_by: int = 1, counter_name, attributes: dict = None):
        upDownCounter = [val for val in self.meter_objects['upDownCounters']
                if counter_name in val.name]

        if not upDownCounter:
            print(f"UpDownCounter name {counter_name} not found.")

        counter[0].add(change_by, attributes)

    # def update_gauge(self,):
    #     gauge = [val for val in self.meter_objects['gauges']
    #             if counter_name in val.name]
    
    #     if not gauge:
    #         print(f"Gauge name {counter_name} not found.")

    def update_histogram(self, ammount: int, counter_name, attributes: dict=None, context=None):
        histogram = [val for val in self.meter_objects['histograms']
                if counter_name in val.name]
        
        if not histogram:
            print(f"Histogram name {counter_name} not found.")
        
        histogram[0].record(ammount, attributes, context)

# =======================================================================
class otel_logger():
    resource = Resource.create({ "service.instance.id": "instance-1"})
    # 2. Configure the Logger Provider
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    # 3. Configure the exporter (e.g., OTLP to a collector running on localhost:4317)
    # Use insecure=True if your collector does not have TLS configured
    log_exporter = OTLPLogExporter(endpoint="localhost:4317", insecure=True)
    # 4. Add a processor to the provider
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    # 5. Attach OTLP handler to the Python standard logging
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().setLevel(logging.NOTSET) # Ensure all levels are captured
    logging.getLogger().addHandler(handler)
    # 6. Use standard Python logging
    logger = logging.getLogger(__name__)

    def info(self, msg):
        logger.info(msg)

    def message(self, msg):
        logger.message(msg)

    def debug(self, msg):
        logger.debug(msg)

    def warning(self, msg):
        logger.warning(msg)
    
    def error(self, msg, attributes: dict = None):
        logger.error(msg, extra={"attributes": attributes})

    def critical(self, msg):
        logger.critical(msg, exc_info=True)
    
    def exception(self, msg):
        logger.exception(msg)
