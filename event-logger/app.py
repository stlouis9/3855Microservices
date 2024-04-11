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
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import yaml
import json
from pykafka import KafkaClient 
from pykafka.common import OffsetType 
from threading import Thread
from stats import Statistics
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


if not os.path.isfile(app_config["datastore"]["filename"]):
    logger.info("DB not found, creating SQLite database")
    conn = sqlite3.connect(app_config["datastore"]["filename"])
    c = conn.cursor()

    c.execute('''
        CREATE TABLE stats (
            id INTEGER PRIMARY KEY ASC,
            message TEXT NOT NULL,
            code TEXT NOT NULL,
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
            log_topic = client.topics[str.encode('event_log')]
            break
        except Exception as e:
            logger.error("Failed to connect to Kafka on attempt #:%s, error: %s", current_retry, e)
            time.sleep(10)
            current_retry += 1
    else:
        logger.error("Exceeded maximum number of retries (%s) for Kafka connection", app_config['events']['max_retry'])
        
    consumer = log_topic.get_simple_consumer(
        consumer_group=b"event_group",
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST,
    )
    
    # Process messages
    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg = json.loads(msg_str)
        logger.info(f"Message: {msg}")
    
 
        session = DB_SESSION()
        stats = Statistics(
            message=msg["payload"],
            code=msg["type"],
            date_created=msg["datetime"]
        )

        session.add(stats)
        session.commit()
        session.close()
    
def get_event_stats():
    session = DB_SESSION()
    objs = session.query(
            Statistics.code, 
            func.count(Statistics.code).label('count')
    ).group_by(Statistics.code).all()
    

    if objs is not None:
        objs = {code: count for code, count in objs}
        logger.info("Query for statistics successful")
    else:
        objs = {}
        logger.error("No statistics found")
    session.close()
    
    
    return objs, 200

    

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
                   
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8120, host='0.0.0.0')