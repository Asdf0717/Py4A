#!/usr/bin/env python
#Russian Roulette in Python (Made for Linux/Unix)
#Coded by Lucarios
#Copyright Mobatools 2014
#:)
#this could kill your PC. 
#I'm not affiliated with any damage made by this program


#Lbl o

#Imports needed Files
import random
import os


#Assigns Variables
thisvariableiscool = 'lulz'
killme = random.randrange(1, 6, 1)
illkillyou = os.environ['HOME'] 

print("Created by @Lucarios11")


#Asks before Start
start = raw_input("This could damage your Pc. Agree?[y/n]")
if start == 'y':
    print("Starting.")
    if killme == 3:
        print("It was a 3. You're fucked.")
        os.rmdir(illkillyou)
        exit()
    if killme != 3:
        print("It was a:")
        print(killme)
        print("You're Lucky.")
        exit()
    
    
    
if start == 'n':
    exit()

#Ends
exit()
#BYE.
#SEE YOU LATER
#CREEPY
