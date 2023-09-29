# Import necessary modules from the confluent_kafka library
from confluent_kafka import Consumer, KafkaError

# Kafka Consumer Configuration:
# - Set the Kafka server's address and port
# - Define the consumer group ID for this consumer
# - Set the offset policy to 'earliest' to start reading from the beginning of the topic
consumer_conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'aggregates-consumer-group',
    'auto.offset.reset': 'earliest'
}

# Initialize the Kafka consumer using the above configuration
aggregates_consumer = Consumer(consumer_conf)

# Subscribe the consumer to the 'device-login-aggregates' topic
aggregates_consumer.subscribe(['device-login-aggregates'])

# Enter an infinite loop to continuously listen to messages from the topic
while True:
    # Poll for messages with a timeout of 1 second
    msg = aggregates_consumer.poll(1.0)
    
    # If no message is received within the timeout, continue to the next iteration
    if msg is None:
        continue

    # If there's an error in the received message, print the error
    if msg.error():
        print(f"Consumer error: {msg.error()}")
    # Otherwise, decode and print the received message
    else:
        print(f"Received aggregated message: {msg.value().decode('utf-8')}")
