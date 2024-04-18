import datetime
import os
import logging
import logging.config
from operator import and_
import sqlite3
import time
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import yaml
import json
from pykafka import KafkaClient 
from pykafka.common import OffsetType 
from threading import Thread
from anomaly import Anomaly
from base import Base


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

logger.info(f"Movie anomaly threshold: {app_config['threshold']['movie']}" )
logger.info(f"Review anomaly threshold: {app_config['threshold']['review']}" )


if not os.path.isfile(app_config["datastore"]["filename"]):
    logger.info("DB not found, creating SQLite database")
    conn = sqlite3.connect(app_config["datastore"]["filename"])
    c = conn.cursor()

    c.execute('''
            CREATE TABLE anomaly
                (id INTEGER PRIMARY KEY ASC, 
                event_id VARCHAR(250) NOT NULL,
                trace_id VARCHAR(250) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                anomaly_type VARCHAR(100) NOT NULL,
                description VARCHAR(250) NOT NULL,
                date_created VARCHAR(100) NOT NULL)
    ''')

    conn.commit()
    conn.close()

DB_ENGINE = create_engine("sqlite:///%s" %
app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

def process_messages():
    current_retry = 0
    # Initialize KafkaClient with your Kafka server details
    while (current_retry < app_config['events']['max_retry']):
        logger.info("Attempting to connect to Kafka. Attempt #: %s", current_retry)
        try:
            client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
            topic = client.topics[str.encode(app_config['events']['topic'])]
            break
        except Exception as e:
            logger.error("Failed to connect to Kafka on attempt #:%s, error: %s", current_retry, e)
            time.sleep(10)
            current_retry += 1
    else:
        logger.error("Exceeded maximum number of retries (%s) for Kafka connection", app_config['events']['max_retry'])
        
    consumer = topic.get_simple_consumer(
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST,)
    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg = json.loads(msg_str)
        logger.info(f"Message: {msg}")

        if msg["type"] == "movie" and msg["payload"]["runtime"] > app_config["threshold"]["movie"]:
                movie_body = msg["payload"]
                logger.info(f"Movie Anomaly detected, value: {movie_body['runtime']} Threshold of {app_config['threshold']['movie']} exceeded")
                session = DB_SESSION()
                anomaly = Anomaly(
                            movie_body['movie_id'],
                            movie_body['trace_id'],
                            msg["type"],
                            "tooHigh"
                            f"Movie Anomaly detected, value: {movie_body['runtime']} Threshold of {app_config['threshold']['movie']} exceeded",
                )
                session.add(anomaly)
                session.commit()
                session.close()
                logger.debug(f"Stored <Movie> anomaly with a trace id of {movie_body['trace_id']}")
                
        if msg["type"] == "review" and msg["payload"]["rating"] < app_config["threshold"]["review"]:
                review_body = msg["payload"]
                logger.info(f"Review Anomaly detected, value: {review_body['runtime']} Threshold of {app_config['threshold']['movie']} exceeded")
                session = DB_SESSION()
                anomaly = Anomaly(
                            review_body['movie_id'],
                            review_body['trace_id'],
                            msg["type"],
                            "tooLow",
                            f"Movie Anomaly detected, value: {review_body['runtime']} Threshold of {app_config['threshold']['movie']} exceeded",
                )
                session.add(anomaly)
                session.commit()
                session.close()
                logger.debug(f"Stored <Review> anomaly with a trace id of {review_body['trace_id']}")
def get_anomaly_stats(anomaly_type):
    session = DB_SESSION()
    objs = session.query( 
            func.count(Anomaly.anomaly_type).label('count')
    ).filter(Anomaly.anomaly_type == anomaly_type).group_by(Anomaly.anomaly_type).all()
    obj2 = session.query(Anomaly.description, Anomaly.date_created).filter(Anomaly.anomaly_type == anomaly_type).order_by(Anomaly.date_created.desc()).first()
    if objs and obj2 is not None:
        result = {
                "num_anomalies": objs["count"],
                "most_recent_desc": obj2["description"],
                "most_recent_datetime": obj2["date_created"]}
    else:
        result = {}
        logger.error("No anomalies found")
    session.close()
    return result, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type' 

app.add_api("openapi.yaml", base_path="/anomaly_detector",strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8150, host='0.0.0.0')