#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import mfrc522
import signal
from time import sleep

RFID1 = [195, 226, 46, 149, 154]
RFID2 = [38, 60, 249, 41, 202]
blueRFID = [166, 51, 127, 165, 79]

continue_reading = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print ("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
lectorRFID = mfrc522.MFRC522()

# Welcome message
print ("Lector RFID | TransMED - PTIN 2023")

# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:

    # Scan for cards    
    status, TagType = lectorRFID.MFRC522_Request(lectorRFID.PICC_REQIDL)

    # Get the UID of the card
    status, uid = lectorRFID.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == lectorRFID.MI_OK:

        # Print UID
        UID = [uid[0], uid[1], uid[2], uid[3], uid[4]]
        print("UID: ", UID)

        # Select the scanned tag
        # lectorRFID.MFRC522_SelectTag(uid)

        #Check to see if card UID read matches your card UID
        if UID == blueRFID:                
            print("Access Granted")
            # Comanda
        # else:                       
            # print("Access Denied")