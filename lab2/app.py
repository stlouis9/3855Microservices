import logging
import os
import logging.config
import time
import requests
import connexion
from connexion import NoContent
import datetime
import json
from pykafka import KafkaClient 
import yaml
import uuid


MAX_EVENTS = 5
EVENT_FILE = "events.json"

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

current_retry = 0
# Initialize KafkaClient with your Kafka server details
while (current_retry < app_config['events']['max_retry']):
    logger.info("Attempting to connect to Kafka. Attempt #: %s", current_retry)
    try:
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        topic = client.topics[str.encode(app_config['events']['topic'])]
        log_topic = client.topics[str.encode('event_log')]
        producer = topic.get_sync_producer()
        log_producer = log_topic.get_sync_producer()
        logger.info("Successfully connected to Kafka on attempt #: %s", current_retry)
        
        msg = { "type": "0001",
                "datetime" :
                    datetime.datetime.now().strftime(
                        "%Y-%m-%dT%H:%M:%S"),
                "payload": f"0001 - Successfully connected to Kafka on attempt #: {current_retry}" }
        msg_str = json.dumps(msg)
        
        log_producer.produce(msg_str.encode('utf-8'))
        break
    except Exception as e:
        logger.error("Failed to connect to Kafka on attempt #:%s, error: %s", current_retry, e)
        time.sleep(10)
        current_retry += 1
else:
    logger.error("Exceeded maximum number of retries (%s) for Kafka connection", app_config['events']['max_retry'])



def add_movie(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event <MovieItem> request with a trace id of {trace_id}")

    body["trace_id"] = trace_id

    msg = { "type": "movie",
            "datetime" :
                datetime.datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"),
            "payload": body }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    
    #response = requests.post(app_config["eventstore1"]["url"], json=body, headers={"Content-Type": "application/json"})

    logger.info(f"Returned event <MovieItem> response (Id: {trace_id}) with status 201")
    return NoContent, 201

def add_movie_review(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event <Review> request with a trace id of {trace_id}")

    body["trace_id"] = trace_id

    #response = requests.post(app_config["eventstore2"]["url"], json=body, headers={"Content-Type": "application/json"})

    msg = { "type": "review",
            "datetime" :
                datetime.datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"),
            "payload": body }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Returned event <Review> response (Id: {trace_id}) with status 201")
    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", base_path="/receiver", scrict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0')
