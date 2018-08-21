#!/usr/bin/env python

import os, time, sys
import logging
import wiringpi
import RPi.GPIO as GPIO

class PWMFanController(object):
    POWER_PIN = 27
    PWM_PIN = 18
    TACH_PIN = 23
    
    def __init__(self, logger):
        self.log = logger

        self.log.info("Initializeing PWM Controller")

        self.duty_cycle = 0
        self.pwm_range = 128
        self.pwm_clock = 6
        self.tach_last_time = 0.0
        self.power_state = 0
        self.enable_power_control = True
        self.min_pwm_val = -1
        self.tach_speed_calc = 0 

        #Check we are a Raspberry PI
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PWMFanController.TACH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(PWMFanController.TACH_PIN, GPIO.FALLING, callback=self.tachCallback, bouncetime=1)
            wiringpi.pwmSetMode(wiringpi.PWM_MODE_MS)
            wiringpi.wiringPiSetupGpio()
            wiringpi.pinMode(PWMFanController.POWER_PIN, wiringpi.OUTPUT)
            self.setPowerState(False)
            wiringpi.pinMode(PWMFanController.PWM_PIN,2)
            wiringpi.pwmSetRange(self.pwm_range)
            wiringpi.pwmSetClock(self.pwm_clock) # Equals 19200000 / PWM_CLOCK / PWM_RANGE
            
            self.enabled = True
        except Exception, e:
            self.log.error(e)
            self.log.error("Could not initialize PWM controller")
            self.enabled = False

    def setPowerState(self, state):
        #If there is a relay, turn it on and off
        if state:
            self.power_state = 1
        else:
            self.power_state = 0
        if self.enable_power_control:
            wiringpi.digitalWrite(PWMFanController.POWER_PIN, self.power_state) # Active Low
    
    def tachCallback(self):
        if self.tach_last_time == 0.0:
            self.tach_last_time = time.time()
        else:
            tmptime = time.time()
            self.tach_speed_calc = 1.0/(4.0 * (tmptime-self.tach_last_time))
            self.tach_last_time = tmptime

    def setDutyCycle(self, value):
        if self.enabled:
            #Check validity
            if value < 0 or value > 100:
                self.log.error("Invalid duty cycle setting %f; keeping value at current level of %f" % (value, self.duty_cycle))
                return False
            new_dc = int(float(value*self.pwm_range)/100.0)
            if new_dc > self.min_pwm_val:
                self.setPowerState(True)
            else:
                self.setPowerState(False)
            if new_dc == self.duty_cycle:
                self.log.info("Current duty is already the same")
            else:
                self.log.debug("Setting PWM Duty Cycle to %f" % (float(value)))
                wiringpi.pwmWrite(PWMFanController.PWM_PIN, new_dc)
                self.duty_cycle = value
                self.log.info("Successfully set PWM Duty Cycle to %d" % (self.duty_cycle))
            return True
        else:
            self.log.error("Cannot set duty cycle since fan was not initialized")
            return False

    def getDutyCycle(self):
        return self.duty_cycle

if __name__ == "__main__":

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    fc = PWMFanController(log)

    try:
        while True:
            try:
                dc = int(input("Enter PWM Duty Cycle: "))
                if dc < 0 or dc > 100:
                    raise ValueError("Not inside range of [0,100]")
                fc.setDutyCycle(dc)
            except ValueError, e:
                log.error("Value must be between 0 and 100 and must be an integer")
            time.sleep(1)
            log.info("Measured tach speed is %f" % (fc.tach_speed_calc))
    except KeyboardInterrupt:
        log.info("Exiting program")
        #fc.setDutyCycle(0)
