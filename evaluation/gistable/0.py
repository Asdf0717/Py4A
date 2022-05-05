import mailbox
import csv

writer = csv.writer(open("mbox-output.csv", "wb"))

for message in mailbox.mbox('file.mbox/mbox'):
	writer.writerow([message['message-id'], message['subject'], message['from']])