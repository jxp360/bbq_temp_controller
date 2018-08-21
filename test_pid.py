#!/usr/bin/env python

import os, time, sys

import pid_controller
import random
import math

minDC = 20
maxDC = 100

def generateRandomTemp(x):
    random_variance = 5 #+/-
    rand = random.random() * random_variance - (random_variance/2)
    return x + rand
    
def normalizeDutyCycle(x):
    if x < 0:
        return 0
    elif x < minDC:
        return 0
    elif x > 100:
        return maxDC
    else:
        #Normalize to nearest 5
        #return int(round(x/5)*5)
        return int(round(x))
        

if __name__ == "__main__":
    #pc = pid_controller.PID(P=6, I=0.02, D=0.0)
    pc = pid_controller.PID(P=6, I=0.02, D=0.0)
    target_temp = 225
    pc.SetPoint = target_temp
    max_temp = 240
    start_temp = 100
    num_temps = 100
    input_temps = [start_temp + (x* (max_temp-start_temp)/num_temps) for x in xrange(num_temps)]
    input_temps += [target_temp] * num_temps
    rand_input_temps = [generateRandomTemp(x) for x in input_temps] 

    for x in rand_input_temps:
        pc.update(x)
        dc = normalizeDutyCycle(pc.output)
        print "For Input Temp: %f PWMDC: %d Output: %f" % (x, dc, pc.output)

