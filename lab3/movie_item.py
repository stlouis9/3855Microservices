from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql.functions import now
from base import Base

class MovieItem(Base):
    """ Movie Item """

    __tablename__ = "movie_item"

    id = Column(Integer, primary_key=True)
    movie_id = Column(String(250), nullable=False)
    trace_id = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    releaseDate = Column(String(100), nullable=False)
    cast = Column(String(250), nullable=False)
    description = Column(String(500), nullable=False)
    genres = Column(String(250), nullable=False)
    runtime = Column(Integer, nullable=False)
    image = Column(String(250), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, movie_id, trace_id, name, releaseDate, cast, description, genres, runtime, image):
        """ Initializes a movie item """
        self.movie_id = movie_id
        self.trace_id = trace_id
        self.name = name
        self.releaseDate = releaseDate
        self.cast = cast
        self.description = description
        self.genres = genres
        self.runtime = runtime
        self.image = image
        self.date_created = now()

    def to_dict(self):
        """ Dictionary Representation of a movie item """
        dict = {}
        dict['id'] = self.id
        dict['movie_id'] = self.movie_id
        dict['trace_id'] = self.trace_id
        dict['name'] = self.name
        dict['releaseDate'] = self.releaseDate
        dict['cast'] = self.cast
        dict['description'] = self.description
        dict['genres'] = self.genres
        dict['runtime'] = self.runtime
        dict['image'] = self.image
        dict['date_created'] = self.date_created

        return dict
