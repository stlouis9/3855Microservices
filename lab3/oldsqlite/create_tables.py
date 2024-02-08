import sqlite3

conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          CREATE TABLE movie_item
          (id INTEGER PRIMARY KEY ASC, 
           movie_id VARCHAR(250) NOT NULL,
           trace_id VARCHAR(250) NOT NULL,
           name VARCHAR(250) NOT NULL,
           releaseDate VARCHAR(250) NOT NULL,
           cast VARCHAR(250) NOT NULL,
           description VARCHAR(250) NOT NULL,
           genres VARCHAR(250) NOT NULL,
           runtime INTEGER NOT NULL,
           image VARCHAR(250) NOT NULL,
           date_created VARCHAR(100) NOT NULL)
          ''')

c.execute('''
          CREATE TABLE review
          (id INTEGER PRIMARY KEY ASC, 
           review_id VARCHAR(250) NOT NULL,
           trace_id VARCHAR(250) NOT NULL,
           username VARCHAR(250) NOT NULL,
           movie_id VARCHAR(250) NOT NULL,
           review_text VARCHAR(250) NOT NULL,
           rating FLOAT NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL)
          ''')

conn.commit()
conn.close()
