import sqlite3, os

conn = sqlite3.connect('Mills1860.mbtiles')

results=conn.execute('select * from tiles').fetchall()

for result in results:
    zoom, column, row, png= result
    try:
        os.makedirs('%s/%s/' % (zoom, row))
    except:
        pass
    tile_out=open('%s/%s/%s.png' % (zoom, row, column), 'wb')
    tile_out.write(png)
    tile_out.close()