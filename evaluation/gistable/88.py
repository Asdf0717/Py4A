import pyodbc
import sys
import csv

conn = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\the\path\to\the.accdb;')
cursor = conn.cursor()

def output_col(col):
  if col:
    if isinstance(col, unicode):
      return col.encode('utf-8')
    else:
      return str(col)
  else:
    return ""

cursor.execute(sys.argv[1])
row = cursor.fetchone()

writer = csv.writer(open(sys.argv[2], 'wb'), delimiter='\t', quoting=csv.QUOTE_NONE)

writer.writerow([t[0] for t in row.cursor_description])
while 1:
  if not row:
    break
  writer.writerow(map(output_col, row))
  row = cursor.fetchone()
