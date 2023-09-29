# Real-time Streaming Data Pipeline with Kafka

This repository houses a real-time data processing pipeline using Kafka. The pipeline ingests streaming data, processes it in real-time, and then stores the processed data into a new Kafka topic.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Design Choices](#design-choices)
- [Prerequisites](#prerequisites)

## Prerequisites

- Docker
- Python 3.x

## Installation & Setup:
1. Clone this repository to your local machine.
2. Ensure Docker is running.
3. Navigate to the directory containing the `docker-compose.yml` file and run:
    ```bash
    docker-compose up -d
    ```
    This will set up the Kafka and Zookeeper containers along with the data generator that produces data to the `user-login` topic.


4. It's recommended to use a virtual environment: 
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```
5. Install the required packages: 
    ```
    pip3 install -r requirements.txt
    ```

## Usage:
- **Running the Kafka Consumer & Producer**:
    1. Once the Docker setup is complete, we can proceed to run the Python scripts located within the same directory.
    2. Run the Kafka data processor script:
        ```bash
        python3 kafka_processor.py
        ```
        This script will continuously consume messages from the `user-login` topic, process the data, and then produce aggregated data to the `device-login-aggregates` topic.

- **Monitoring Aggregated Data**:
    To monitor the aggregated data:
    1. In a separate terminal window, navigate to the directory containing the Python scripts.
    2. Run the following command:
    ```bash
    python3 monitor_aggregated_data.py
    ```
    This script will continuously consume messages from the `device-login-aggregates` topic and print them, allowing you to observe the aggregated data in real-time.

## Design Choices:

**Data Ingestion:**
- The data is ingested into the Kafka topic named user-login using a data generator provided in the Docker setup.

**Data Processing:**
- The `kafka_processor.py` script consumes messages from the user-login topic and aggregates the data based on several metrics such as device counts, login counts by locale, unique device counts, app version by device type, unique IP counts, and frequent IP addresses. The data is aggregated over a time window, and once this window elapses, the aggregated data is sent to a new Kafka topic named device-login-aggregate

**Concurrency and Data Integrity:**
The script employs threading to ensure that the data aggregation and data sending actions are decoupled. This allows the script to send aggregated data at a consistent interval while simultaneously processing incoming data. To ensure data integrity and avoid race conditions, a threading lock (`data_lock`) is used. This lock ensures that the data structures used for aggregation aren't modified while aggregated data is being sent, and vice versa. This design choice guarantees the correctness of the data being sent and ensures continuous and timely data delivery.

**Monitoring:**
- In order to validate the efficacy of our real-time data processing, we implemented a separate script (`monitor_aggregated_data.py`) to continuously monitor and print the aggregated data. This provides immediate feedback and ensures that the data processing pipeline is functioning as expected. Real-time monitoring is crucial in production systems to quickly identify and rectify any issues, ensuring smooth operations and maintaining data integrity.

**Aggregations**:
- **Device Counts**: By aggregating device count it can help us in understanding the distribution of user logins across different device types. Tracking the count of logins from Android, iOS, and other devices, we can perhaps get insights into which platform is more popular among users. This can guide decisions on where to invest more resources in terms of app development or marketing.
  
- **Login Counts by Locale**: y aggregating the number of logins based on the locale, we can understand better the geographical distribution of users and can help in tailoring specific features or marketing campaigns for certain regions.

- **Unique Device Count**: Counting unique devices gives an idea about the distinct number of devices accessing the service. This is a better metric than just login counts because one device can have multiple logins. A rising unique device count might indicate growing user adoption.

- **App Version by Device**: Insights into which app versions are being used on which devices.

- **Unique IP Count & Frequent IP Addresses**: Tracking unique IP addresses can give a rough estimate of the distinct number of users or networks accessing the service. Monitoring frequent IP addresses can be used for security purposes to detect any potential misuse or attacks.

**Aggregation Interval**:
A 30-second interval balances between real-time insights and computational efficiency.

**Error Handling**:
Rather than stopping the entire pipeline upon encountering an error, the design choice was made to log the error and continue processing. This ensures that isolated issues with individual messages don't disrupt the continuous data flow.

**Default Values for Missing Data**:
In cases where certain fields are missing from the incoming data, default values like "unknown" are used. This choice ensures that the data processing can continue seamlessly even if some fields are missing and a warning is logged. Any other exceptions encountered during data processing are caught, logged, and the script continues processing the next message.


## Data Flow

From the moment data is produced, it goes through a series of steps before being aggregated and monitored:
1. **Data Generation**: Using the provided data generator in the Docker setup, messages are produced to the `user-login` topic.
2. **Data Consumption**: The `kafka_processor.py` script acts as a Kafka consumer, pulling messages from the `user-login` topic.
3. **Data Processing**: As messages are consumed, they are processed and aggregated based on various metrics (device counts, login counts by locale, etc.).
4. **Data Production**: After aggregating data over a set interval, the script produces the aggregated data to a new Kafka topic named `device-login-aggregates`.
5. **Monitoring**: Using the `monitor_aggregated_data.py` script, we can continuously consume and monitor the aggregated data from the `device-login-aggregates` topic.

## Efficiency, Scalability, and Fault Tolerance

- **Efficiency**: The choice of aggregating data over intervals, as opposed to real-time aggregation for every message, ensures manageable computational load. 
  
- **Scalability**: Should the data input rate grow, we can easily add more Kafka brokers to the cluster to distribute the load and handle larger data volumes. In the current setup, data aggregation is performed in-memory using Python's native structures, suitable for modest datasets. For scalability with larger data volumes, consider integrating scalable databases, utilizing in-memory data stores, or employing distributed computation might be more appropriate. These measures ensure efficient real-time processing while optimizing memory usage and system performance as data grows.


- **Fault Tolerance**: Kafka provides built-in fault tolerance through data replication across multiple brokers. On the script's side, we've designed robust error-handling mechanisms. Even if certain messages have issues or missing fields, our pipeline continues processing subsequent messages, ensuring uninterrupted data flow.

## Importance of Real-time Monitoring

In production systems, being reactive to issues is not enough; proactive monitoring is crucial. Real-time monitoring, as facilitated by `monitor_aggregated_data.py` script, offers several advantages:
1. **Immediate Feedback**: As soon as data is aggregated and produced to the new topic, we get immediate feedback on what the aggregated data looks like.
2. **Proactive Issue Resolution**: By continuously monitoring the data, any anomalies or unexpected patterns can be detected early, allowing for proactive issue resolution before they escalate.
3. **Ensuring Data Integrity**: Continuous monitoring ensures that the data being produced to the new topic maintains its integrity and matches expected patterns and formats.

## Addressing Additional Questions

1. **Deployment in Production**: For production deployment, this application would be containerized using Docker, and coordinate using a tool like Kubernetes. Proper logging mechanisms would be integrated, and the application would be deployed across a multi-node Kafka cluster for better load distribution and fault tolerance.

2. **Production-Ready Components**: To make this production-ready, we would add:
   - **Logging**: Integration of a logging mechanism like ELK stack for better log analysis and visualization.
   - **Monitoring Tools**: Tools like Grafana would be integrated for system monitoring and alerting.
   - **Security**: Implement proper security protocols, including message encryption and secure channels for data transfer.
   - **Backup & Recovery**: Implement backup strategies for Kafka data and ensure there's a disaster recovery plan in place.

3. **Scalability with Growing Dataset**: With a growing dataset, more brokers can be added to the Kafka cluster. Additionally, the consumer groups feature of Kafka can be used to allow multiple instances of our script to consume and process data in parallel, thereby distributing the load and ensuring efficient processing even with large data volumes.
