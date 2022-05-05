#!/usr/bin/env python3.5
import subprocess
from prettytable import PrettyTable
import json
import time

print("Gegevens ophalen...")
party_ids = ['x'] * 2000
party_ids[1078] = 'VVD'
party_ids[1079] = 'PvdA'
party_ids[1084] = 'PVV'
party_ids[1085] = 'SP'
party_ids[1080] = 'CDA'
party_ids[1081] = 'D66'
party_ids[1083] = 'ChristenUnie'
party_ids[1114] = 'GroenLinks'
party_ids[1082] = 'SGP'
party_ids[1086] = 'Partij voor de Dieren'
party_ids[1087] = '50Plus'
party_ids[1097] = 'OndernemersPartij'
party_ids[1089] = 'VNL'
party_ids[1088] = 'DENK'
party_ids[1108] = 'Nieuwe Wegen'
party_ids[1112] = 'Forum voor Democratie'
party_ids[1096] = 'De Burger Beweging'
party_ids[933] = 'Vrijzinnige Partij'
party_ids[1115] = 'GeenPeil'
party_ids[628] = 'Piratenpartij'
party_ids[1119] = 'Artikel 1'
party_ids[1094] = 'Niet Stemmers'
party_ids[1093] = 'Libertarische Partij'
party_ids[1100] = 'Lokaal in de Kamer'

# Jsond bevat een bytestring van wat je in de devtools ziet
jsond = subprocess.check_output('./curl_van_results_php.sh')

jsonobj = json.loads(str(jsond, 'utf-8'))

parties = jsonobj['response']['result']['parties']

t = PrettyTable(['PartyID', 'Partij', 'Telling'])
t.align['PartyID'] = "r"
t.align['Partij'] = "l"
t.align['Telling'] = "r"
for party in parties:
    t.add_row([party['partyID'], party_ids[party['partyID']], party['count']])
print("Stand per " + time.strftime("%d-%m-%Y %H:%M") + ":")
print(t)
