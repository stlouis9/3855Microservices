from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql.functions import now
from base import Base

class Review(Base):
    """ Review """

    __tablename__ = "review"

    id = Column(Integer, primary_key=True)
    movie_id = Column(String(250), nullable=False)
    trace_id = Column(String(250), nullable=False)
    review_id = Column(String(250), nullable=False)
    username = Column(String(250), nullable=False)
    rating = Column(Float, nullable=False)
    review_text = Column(String(500), nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, movie_id, trace_id, username, rating, review_text, timestamp, review_id):
        """ Initializes a review """
        self.movie_id = movie_id
        self.trace_id = trace_id
        self.review_id = review_id
        self.username = username
        self.rating = rating
        self.review_text = review_text
        self.timestamp = timestamp
        self.date_created = now()

    def to_dict(self):
        """ Dictionary Representation of a review """
        dict = {}
        dict['id'] = self.id
        dict['movie_id'] = self.movie_id
        dict['trace_id'] = self.trace_id
        dict['username'] = self.username
        dict['rating'] = self.rating
        dict['review_text'] = self.review_text
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created
        dict['review_id'] = self.review_id

        return dict