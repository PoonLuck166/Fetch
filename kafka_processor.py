import logging
from confluent_kafka import Consumer, Producer, KafkaError
import time
import threading

# Initialize the logging system for diagnostics and debugging purposes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka Consumer Configuration: Establishing the necessary parameters for the consumer
consumer_conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'user-login-group',
    'auto.offset.reset': 'earliest'
}

# Kafka Producer Configuration: Defining the parameters for the producer
producer_conf = {
    'bootstrap.servers': 'localhost:29092',
}

# Instantiate the Kafka Consumer using the above configuration
consumer = Consumer(consumer_conf)

# Instantiate the Kafka Producer using the above configuration
producer = Producer(producer_conf)

# Subscribe the consumer to the 'user-login' topic
consumer.subscribe(['user-login'])

# Aggregation Data Structures: Used to maintain and compute aggregates on the fly
device_counts = {'android': 0, 'iOS': 0, 'unknown': 0}
locale_counts = {}
unique_devices = set()
app_version_by_device = {'android': {}, 'iOS': {}, 'unknown': {}}
unique_ips = set()
ip_counts = {}
AGGREGATION_INTERVAL = 30  # Time window for aggregating data before sending

# Define default values for potential missing fields in incoming data
DEFAULT_VALUES = {
    "device_type": "unknown",
    "locale": "unknown",
    "device_id": "unknown",
    "app_version": "unknown",
    "ip": "unknown"
}

# Thread synchronization mechanism to ensure data consistency
data_lock = threading.Lock()

def send_aggregated_data():
    """
    Periodically sends aggregated data to the specified Kafka topic.
    This function runs in its own thread to ensure timely data delivery.
    """
    global device_counts, locale_counts, unique_devices, app_version_by_device, unique_ips, ip_counts

    while True:
        time.sleep(AGGREGATION_INTERVAL)

        with data_lock:
            aggregates = {
                'device_counts': device_counts,
                'locale_counts': locale_counts,
                'unique_device_count': len(unique_devices),
                'app_version_by_device': app_version_by_device,
                'unique_ip_count': len(unique_ips),
                'frequent_ips': [ip for ip, count in ip_counts.items() if count > 5]
            }

            producer.produce('device-login-aggregates', str(aggregates))
            producer.flush()

            # Resetting the aggregates after sending
            device_counts = {'android': 0, 'iOS': 0, 'unknown': 0}
            locale_counts = {}
            unique_devices = set()
            app_version_by_device = {'android': {}, 'iOS': {}, 'unknown': {}}
            unique_ips = set()
            ip_counts = {}

# Launching the data sender in a separate thread
timer_thread = threading.Thread(target=send_aggregated_data)
timer_thread.daemon = True  
timer_thread.start()

def process_message(msg):
    """
    Processes an individual message from the Kafka topic.
    Computes aggregates and handles potential issues with the incoming data.
    """
    global device_counts, locale_counts, unique_devices, app_version_by_device, unique_ips, ip_counts

    try:
        message = msg.value().decode('utf-8')
        data = eval(message)

        # Handling missing fields by substituting with default values
        missing_fields = [key for key in DEFAULT_VALUES if key not in data]
        for key in missing_fields:
            data[key] = DEFAULT_VALUES[key]
        
        if missing_fields:
            logging.warning(f"Substituted missing fields {missing_fields} in data: {data}")

        # Computing aggregates
        with data_lock:
            device_type = data["device_type"]
            device_counts[device_type] = device_counts.get(device_type, 0) + 1

            locale = data["locale"]
            locale_counts[locale] = locale_counts.get(locale, 0) + 1

            device_id = data["device_id"]
            unique_devices.add(device_id)

            app_version = data["app_version"]
            app_version_by_device[device_type][app_version] = app_version_by_device[device_type].get(app_version, 0) + 1

            ip = data["ip"]
            unique_ips.add(ip)
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

    except Exception as e:
        logging.error(f"Error processing message: {e}. Data: {msg.value().decode('utf-8')}")

# Main loop to continuously poll for messages from the Kafka topic
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        logging.error(f"Consumer error: {msg.error()}")
    else:
        process_message(msg)

# Gracefully close the consumer upon termination
consumer.close()
