import datetime
import logging
import logging.config
from operator import and_
import connexion
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml
import json
from pykafka import KafkaClient 
from pykafka.common import OffsetType 
from threading import Thread
from base import Base
from movie_item import MovieItem
from review import Review


with open('db_conf.yml', 'r') as f:
    db_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

DB_ENGINE = create_engine(f"mysql+pymysql://"
                          f"{db_config['datastore']['user']}:"
                          f"{db_config['datastore']['password']}@"
                          f"{db_config['datastore']['hostname']}:"
                          f"{db_config['datastore']['port']}/"
                          f"{db_config['datastore']['db']}"
                          , future=True)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(f"Connecting to DB. Hostname: {db_config['datastore']['hostname']}, Port: {db_config['datastore']['port']}")


def get_movies(start_timestamp, end_timestamp):
    """ Returns all movies between the start and end timestamp """
    session = DB_SESSION()
    try:
        start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
        end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")
        results = session.query(MovieItem).filter(
            and_(MovieItem.date_created >= start_timestamp_datetime,
                    MovieItem.date_created < end_timestamp_datetime))
        results_list = []
        
        for reading in results:
            results_list.append(reading.to_dict())
            
        session.close()
        
        logger.info("Query for Movie Items after %s returns %d results" %
                (start_timestamp, len(results_list)))
    except Exception as e:
        logger.error("Error in get movies: %s" % e)
        return NoContent, 404
    return results_list, 200

def get_reviews(start_timestamp, end_timestamp):
    """ Returns all reviews between the start and end timestamp """
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")
    
    results = session.query(Review).filter(
        and_(Review.date_created >= start_timestamp_datetime,
                Review.date_created < end_timestamp_datetime))
    results_list = []
    
    for result in results:
        results_list.append(result.to_dict())
        
    session.close()
    
    logger.info("Query for Reviews after %s returns %d results" %
            (start_timestamp, len(results_list)))

    
    return results_list, 200

def process_messages():
    """Process event messages."""

    # Configure Kafka client
    hostname = f"{db_config['events']['hostname']}" \
                f":{db_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(db_config["events"]["topic"])]

    # Create consumer
    consumer = topic.get_simple_consumer(
        consumer_group=b"event_group",
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST,
    )

    # Process messages
    for msg in consumer:
        msg_str = msg.value.decode("utf-8")
        msg = json.loads(msg_str)
        logger.info(f"Message: {msg}")

        payload = msg["payload"]

        if msg["type"] == "movie":
                movie_body = msg["payload"]
                session = DB_SESSION()
                mi = MovieItem(movie_body['movie_id'],
                            movie_body['trace_id'],
                            movie_body['name'],
                            movie_body['releaseDate'],
                            movie_body['cast'],
                            movie_body['description'],
                            movie_body['genres'],
                            movie_body['runtime'],
                            movie_body['image'])

                session.add(mi)
                session.commit()
                session.close()
                logger.debug(f"Stored event <MovieItem> request with a trace id of {movie_body['trace_id']}")
        elif msg["type"] == "review":
                review_body = msg["payload"]
                session = DB_SESSION()
                r = Review(review_body['movie_id'],
                        review_body['trace_id'],
                        review_body['username'],
                        review_body['rating'],
                        review_body['review_text'],
                        review_body['timestamp'],
                        review_body['review_id'])

                session.add(r)
                session.commit()
                session.close()
                logger.debug(f"Stored event <Review> request with a trace id of {review_body['trace_id']}")
        # Commit offset after processing
        consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090)
