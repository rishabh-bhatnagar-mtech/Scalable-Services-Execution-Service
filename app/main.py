import ast
import datetime
import json
import logging
import os

from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer
from kafka.consumer.subscription_state import ConsumerRebalanceListener

from runner import run_code

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS")
SUBMISSION_TOPIC = os.getenv("SUBMISSION_TOPIC")
RESULT_TOPIC = os.getenv("RESULT_TOPIC")
SUPPORTED_LANGUAGES = {"python", "golang"}

print(f"KAFKA_BROKERS: {KAFKA_BROKERS}")
print(f"SUBMISSION_TOPIC: {SUBMISSION_TOPIC}")
print(f"RESULT_TOPIC: {RESULT_TOPIC}")

logging.basicConfig(filename='app.log', level=logging.INFO, filemode='w',
                    format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


class RebalanceListener(ConsumerRebalanceListener):
    def __init__(self, consumer):
        self.consumer = consumer

    def on_partitions_revoked(self, revoked):
        # You can commit offsets here if needed before rebalance
        pass

    def on_partitions_assigned(self, assigned):
        print(f"Partitions assigned: {assigned}")
        # Seek to beginning of each assigned partition to consume from start
        for partition in assigned:
            self.consumer.seek_to_beginning(partition)


consumer = KafkaConsumer(
    SUBMISSION_TOPIC,
    bootstrap_servers=KAFKA_BROKERS,
    group_id='execution-service',
    auto_offset_reset='earliest',  # fallback if no committed offsets
    enable_auto_commit=True,
    value_deserializer=lambda m: m.decode('utf-8'),
    max_poll_interval_ms=5000,
    max_poll_records=1
)

# Attach rebalance listener to seek to beginning on partition assignment
consumer.subscribe([SUBMISSION_TOPIC], listener=RebalanceListener(consumer))

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS.split(","),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def process_submission(msg):
    data = ast.literal_eval(msg.value)
    code = data['code']
    language = data.get('language')
    submission_id = data.get('submission_id')
    test_cases = data.get('test_cases', [])

    if language not in SUPPORTED_LANGUAGES:
        result_msg = {
            "submission_id": submission_id,
            "error": f"Unsupported language: {language}"
        }
        producer.send(RESULT_TOPIC, value=result_msg, key=submission_id.encode())
        producer.flush()
        return

    results = []
    for case in test_cases:
        try:
            output = run_code(code, case['input'], language)
            passed = output.strip() == case['output'].strip()
        except Exception as e:
            output = str(e)
            passed = False
        results.append({
            "input": case['input'],
            "expected": case['output'],
            "actual": output.strip(),
            "passed": passed
        })
    result_msg = {
        "submission_id": submission_id,
        "results": results
    }
    producer.send(RESULT_TOPIC, value=result_msg, key=submission_id.encode())
    producer.flush()


def main():
    print(f"Starting Execution Service and subscribing to {SUBMISSION_TOPIC}....", flush=True)
    print("Execution Service is running...")
    for msg in consumer:
        print(datetime.datetime.now(), "Received message....", flush=True)
        process_submission(msg)


if __name__ == "__main__":
    main()
