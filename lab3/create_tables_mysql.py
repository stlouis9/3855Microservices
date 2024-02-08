import mysql.connector

db_conn = mysql.connector.connect(
    host="localhost",
    user="python",
    password="python",
    database="events"
)

db_cursor = db_conn.cursor()

db_cursor.execute('''
    CREATE TABLE movie_item
          (id INT NOT NULL AUTO_INCREMENT, 
           movie_id VARCHAR(250) NOT NULL,
           trace_id VARCHAR(250) NOT NULL,
           name VARCHAR(250) NOT NULL,
           releaseDate VARCHAR(250) NOT NULL,
           cast VARCHAR(250) NOT NULL,
           description VARCHAR(250) NOT NULL,
           genres VARCHAR(250) NOT NULL,
           runtime INTEGER NOT NULL,
           image VARCHAR(250) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT movie_item_pk PRIMARY KEY (id))
''')

db_cursor.execute('''
    CREATE TABLE review
          (id INT NOT NULL AUTO_INCREMENT, 
           review_id VARCHAR(250) NOT NULL,
           trace_id VARCHAR(250) NOT NULL,
           username VARCHAR(250) NOT NULL,
           movie_id VARCHAR(250) NOT NULL,
           review_text VARCHAR(250) NOT NULL,
           rating FLOAT NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT review_pk PRIMARY KEY (id))
''')

db_conn.commit()
db_conn.close()