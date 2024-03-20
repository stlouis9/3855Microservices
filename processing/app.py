import datetime
import logging
import logging.config
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import requests
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from stats import Stats

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

DB_ENGINE = create_engine("sqlite:///%s" %
app_config["datastore"]["filename"])
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger = logging.getLogger('basicLogger')

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
    
    
    if len(movieItemJSON) == 0 and len(movieReviewJSON) == 0:
        logger.info("No new events, nothing to process. Exiting...")
        exit()
    

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
