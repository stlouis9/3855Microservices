import sqlite3

conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          DROP TABLE movie_item
          ''')
c.execute('''
          DROP TABLE review
          ''')
conn.commit()
conn.close()
