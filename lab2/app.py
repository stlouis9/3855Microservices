import logging
import logging.config
import requests
import connexion
from connexion import NoContent
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

    response = requests.post(app_config["eventstore1"]["url"], json=body, headers={"Content-Type": "application/json"})

    logger.info(f"Returned event <MovieItem> response (Id: {trace_id}) with status {response.status_code}")
    return NoContent, response.status_code

def add_movie_review(body):
    trace_id = str(uuid.uuid4())
    logger.info(f"Received event <Review> request with a trace id of {trace_id}")

    body["trace_id"] = trace_id

    response = requests.post(app_config["eventstore2"]["url"], json=body, headers={"Content-Type": "application/json"})

    logger.info(f"Returned event <Review> response (Id: {trace_id}) with status {response.status_code}")
    return NoContent, response.status_code


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", scrict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8080)
