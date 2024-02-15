import sqlite3

conn = sqlite3.connect('stats.sqlite')
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