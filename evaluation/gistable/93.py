import mailbox
from email.header import decode_header
import re
import itertools

regex = re.compile('[^a-zA-Z0-9]')
words = []
for message in mailbox.mbox('Inbox.mbox'):
    subject, encoding = decode_header(message['subject'])[0]

    if subject:
        if (encoding is None):
            sentence = subject.split()
        else:
            sentence = subject.decode('ascii', 'ignore').split()

        for b in sentence:
            words.append(regex.sub('',b).lower())

    froms, encoding = decode_header(message['from'])[0]

    if froms:
        if (encoding is None):
            sender = froms.split()
        else:
            sender = froms.decode('ascii', 'ignore').split()

        for b in sender:
            words.append(regex.sub('',b).lower())

freq =  [(len(list(v)), key) for (key, v) in itertools.groupby(sorted(words))]

freq.sort(key=lambda tup: tup[0], reverse=True)

for a in freq:
    print (a)