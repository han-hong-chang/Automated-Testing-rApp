import os
import json
from kafka import KafkaProducer

def send_payload_to_teiv_kafka(payload_file_path: str):
    """
    Load payload JSON from file and send it to Kafka topic with configured headers.
    """

    # Load the JSON payload from file
    with open(payload_file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
        print("Payload loaded from:", payload_file_path)

    # Kafka CloudEvent Headers
    headers = [
        ("ce_specversion", b"1.0"),
        ("ce_id", b"26a2bb70-cd05-4e73-bbc9-860a17a22a"),
        ("ce_source", b"dmi-plugin:nm-1"),
        ("ce_type", b"ran-logical-topology.create"),
        ("content-type", b"application/json"),
        ("ce_time", b"2024-09-16T09:05:00Z"),
        ("ce_dataschema", b"https://ties:8080/schemas/v1/r1-topology")
    ]

    # Kafka Producer Configuration
    producer = KafkaProducer(
        bootstrap_servers=['onap-strimzi-kafka-bootstrap.onap:9092'],
        security_protocol='SASL_PLAINTEXT',
        sasl_mechanism='SCRAM-SHA-512',
        sasl_plain_username='strimzi-kafka-admin',
        sasl_plain_password='WNwEgiWt5gw4QLYVaozQIoi4OdRp4A07'
    )

    # Send message to Kafka topic
    producer.send(
        'topology-inventory-ingestion',
        value=json.dumps(payload).encode('utf-8'),
        headers=headers
    )

    producer.flush()
    print("✅ Kafka message successfully sent!")

