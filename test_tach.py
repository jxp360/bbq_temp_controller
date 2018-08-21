#!/usr/bin/env

import os, time, sys
import RPi.GPIO as GPIO

TACH_PIN = 22

if __name__ == "__main__":

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TACH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    global revcount
    revcount = 0
    def increaserev(channel):
        global revcount
        revcount += 1
    GPIO.add_event_detect(TACH_PIN, GPIO.RISING, callback=increaserev)
    while True:
        sleeptime = 5
        time.sleep(sleeptime)
        #time sleep/num cycles = secs/cycle
        #RPM = 60 / secs/cycle
        
        print "RPM is {0}".format(60.0/(float(sleeptime)/float(revcount)))
        revcount = 0
