import logging
import logging.config
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

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def add_movie(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event <MovieItem> request with a trace id of {trace_id}")

    body["trace_id"] = trace_id

    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()
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

    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()
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
app.add_api("openapi.yaml", scrict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0')
