import datetime
import logging
import logging.config
from operator import and_
import connexion
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml
from base import Base
from movie_item import MovieItem
from review import Review


with open('db_conf.yml', 'r') as f:
    db_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

DB_ENGINE = create_engine(f"mysql+pymysql://"
                          f"{db_config['datastore']['user']}:"
                          f"{db_config['datastore']['password']}@"
                          f"{db_config['datastore']['hostname']}:"
                          f"{db_config['datastore']['port']}/"
                          f"{db_config['datastore']['db']}"
                          , future=True)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


logger = logging.getLogger('basicLogger')

def add_movie(body):
    """ Receives a movie item """
    session = DB_SESSION()
    mi = MovieItem(body['movie_id'],
                body['trace_id'],
                body['name'],
                body['releaseDate'],
                body['cast'],
                body['description'],
                body['genres'],
                body['runtime'],
                body['image'])

    session.add(mi)

    session.commit()
    
    session.close()

    logger.debug(f"Stored event <MovieItem> request with a trace id of {body['trace_id']}")
    return NoContent, 201

def add_movie_review(body):
    """ Receives a review """

    session = DB_SESSION()

    r = Review(body['movie_id'],
               body['trace_id'],
               body['username'],
               body['rating'],
               body['review_text'],
               body['timestamp'],
               body['review_id'])

    session.add(r)

    session.commit()
    session.close()
    logger.debug(f"Stored event <Review> request with a trace id of {body['trace_id']}")
    return NoContent, 201

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

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)
