from sqlalchemy import Column, Float, Integer, String, DateTime
from base import Base


class Stats(Base):
    """ Processing Statistics """
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True)
    num_movies = Column(Integer, nullable=False)
    max_movie_runtime = Column(Integer, nullable=False)
    num_reviews = Column(Integer, nullable=True)
    avg_rating = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=False)

    def __init__(self, num_movies, max_movie_runtime,
                 num_reviews, avg_rating,
                 last_updated):
        """ Initializes a processing statistics object """
        self.num_movies = num_movies
        self.max_movie_runtime = max_movie_runtime
        self.num_reviews = num_reviews
        self.avg_rating = avg_rating
        self.last_updated = last_updated

    def to_dict(self):
        """ Dictionary Representation of a statistics """
        dict = {}
        dict['num_movies'] = self.num_movies
        dict['max_movie_runtime'] = self.max_movie_runtime
        dict['num_reviews'] = self.num_reviews
        dict['avg_rating'] = self.avg_rating
        dict['last_updated'] = self.last_updated.strftime("%Y-%m-%dT%H:%M:%S")
        
        return dict
    

