#!/usr/bin/env python

import os, time, sys
from w1thermsensor import W1ThermSensor

if __name__ == "__main__":

    sensor = W1ThermSensor()
    
    #print W1ThermSensor.get_available_sensors()

    x = 0

    while x < 15:

        temp_in_f = sensor.get_temperature(W1ThermSensor.DEGREES_F)

        print temp_in_f
        x += 1

