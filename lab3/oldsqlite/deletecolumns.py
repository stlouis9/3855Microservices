import sqlite3

conn = sqlite3.connect('readings.sqlite')

c = conn.cursor()
c.execute('''
          DELETE FROM movie_item
          ''')
c.execute('''
          DELETE FROM review
          ''')
conn.commit()
conn.close()
