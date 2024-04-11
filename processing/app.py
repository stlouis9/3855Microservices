import datetime
import json
import os
import logging
import logging.config
import sqlite3
import time
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from pykafka import KafkaClient 
from pykafka.common import OffsetType
import requests
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from stats import Stats

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
            num_movies INTEGER NOT NULL,
            max_movie_runtime INTEGER,
            num_reviews INTEGER  NOT NULL,
            avg_rating FLOAT,
            last_updated VARCHAR(100) NOT NULL)
    ''')

    conn.commit()
    conn.close()

current_retry = 0
# Initialize KafkaClient with your Kafka server details
while (current_retry < app_config['events']['max_retry']):
    logger.info("Attempting to connect to Kafka. Attempt #: %s", current_retry)
    try:
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        log_topic = client.topics[str.encode('event_log')]
        log_producer = log_topic.get_sync_producer()
        
        msg = { "type": "0003",
                "datetime" :
                    datetime.datetime.now().strftime(
                        "%Y-%m-%dT%H:%M:%S"),
                "payload": f"0003 - Successfully connected to Kafka on attempt #: {current_retry}" }
        msg_str = json.dumps(msg)
        
        log_producer.produce(msg_str.encode('utf-8'))
        break
    except Exception as e:
        logger.error("Failed to connect to Kafka on attempt #:%s, error: %s", current_retry, e)
        time.sleep(10)
        current_retry += 1
else:
    logger.error("Exceeded maximum number of retries (%s) for Kafka connection", app_config['events']['max_retry'])


DB_ENGINE = create_engine("sqlite:///%s" %
app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

def populate_stats():

    # Get the current datetime
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # Periodically update stats 
    logger.info("start periodic processing")
    # Read in the current statistics from the SQLite database
    session = DB_SESSION()
    result = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    
    session.close()
    
    if result is None:
        result = Stats(0, 0, 0, 0.0, (datetime.datetime.now() - datetime.timedelta(days=1)))



    movieItemList = requests.get(app_config['eventstore']['url'] + '/movies/movieItem', params={'start_timestamp': result.last_updated.strftime("%Y-%m-%dT%H:%M:%S"), 'end_timestamp': current_datetime})
    movieReviewList = requests.get(app_config['eventstore']['url'] + '/movies/review', params={'start_timestamp': result.last_updated.strftime("%Y-%m-%dT%H:%M:%S"), 'end_timestamp': current_datetime})
    
    

    # Log an ERROR message if the response code is not 200
    if movieItemList.status_code != 200 or movieReviewList.status_code != 200:
        logger.error("Failed to get events from Data Store Service")
    
    movieItemJSON = movieItemList.json()
    movieReviewJSON = movieReviewList.json()

    # Log the number of events received
    logger.info(f"Received {len(movieItemJSON)} movie item and {len(movieReviewJSON)} review events")
    
    checkempty = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    
    if checkempty is None and len(movieItemJSON) == 0 and len(movieReviewJSON) == 0:
        logger.info("No events found, committing empty stats")
        session = DB_SESSION()
        session.add(result)
        session.commit()
        session.close()
        
         
    
    if len(movieItemJSON) == 0 and len(movieReviewJSON) == 0:
        logger.info("No new events, nothing to process. Exiting...")
        exit()
    try:
        if (len(movieItemJSON) + len(movieReviewJSON)) > app_config['events']['message_limit']:
            msg = { "type": "0004",
                    "datetime" :
                        datetime.datetime.now().strftime(
                            "%Y-%m-%dT%H:%M:%S"),
                    "payload": f"0004 - received {len(movieItemJSON) + len(movieReviewJSON)} events, exceeding message limit of {app_config['events']['message_limit']} " }
            msg_str = json.dumps(msg)
            
            log_producer.produce(msg_str.encode('utf-8'))
    except Exception as e:
        logger.error("Error in sending message: %s" % e)

    max_runtime = result.max_movie_runtime
    avg_rating = 0.0
    

    for event in movieItemJSON:
        # Log a DEBUG message with the trace_id
        logger.debug(f"Processing event with trace_id: {event['trace_id']}")

        # Calculate updated statistics
            
        if event["runtime"] > max_runtime:
            max_runtime = event["runtime"]
            
       
 
    for event in movieReviewJSON:
        logger.debug(f"Processing event with trace_id: {event['trace_id']}")
        avg_rating += event["rating"]
    
    
    avg_rating = ((result.avg_rating*result.num_reviews) + avg_rating)/(result.num_reviews+len(movieReviewJSON))
    
    
    statsToBeAdded = {}
    statsToBeAdded["num_movies"] = len(movieItemJSON) + result.num_movies
    statsToBeAdded["max_movie_runtime"] = max_runtime
    statsToBeAdded["num_reviews"] = len(movieReviewJSON) + result.num_reviews
    statsToBeAdded["avg_rating"] = avg_rating
    statsToBeAdded["last_updated"] = current_datetime


    
    session = DB_SESSION()
    stats = Stats(statsToBeAdded["num_movies"],
                statsToBeAdded["max_movie_runtime"],
                statsToBeAdded["num_reviews"],
                statsToBeAdded["avg_rating"],
                datetime.datetime.strptime(statsToBeAdded["last_updated"], "%Y-%m-%dT%H:%M:%S"))
    session.add(stats)
    session.commit()
    # Log a DEBUG message with the updated statistics values
    logger.debug(f"Updated statistics: {stats.to_dict()}") 
    # Log an INFO message indicating period processing has ended
    logger.info("Periodic processing has ended")
    session.close()


    
    


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

def get_stats():
    logger.info("Retrieving stats...")
    session = DB_SESSION()
    stats = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    if stats is None:
        logger.error("Statistics do not exist")
        return NoContent, 404
    
    logger.debug(f"Retrieved stats: {stats.to_dict()}")
    results = {}
    results["num_movies"] = stats.num_movies
    results["max_movie_runtime"] = stats.max_movie_runtime
    results["num_reviews"] = stats.num_reviews
    results["avg_rating"] = round(stats.avg_rating, 2)
    results["last_updated"] = stats.last_updated.strftime("%Y-%m-%dT%H:%M:%S")
    
    logger.info("request successful")
    
    return results, 200
    


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
    init_scheduler()
    app.run(port=8100, host='0.0.0.0')
