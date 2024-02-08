import mysql.connector

db_conn = mysql.connector.connect(
    host="localhost",
    user="python",
    password="python",
    database="events"
)

db_cursor = db_conn.cursor()
db_cursor.execute('''
          DELETE FROM movie_item
          ''')
db_cursor.execute('''
          DELETE FROM review
          ''')
db_conn.commit()
db_conn.close()