#!/usr/bin/env python

import os, time, sys
import logging
import threading
from w1thermsensor import W1ThermSensor
from fan_controller import PWMFanController
from pid_controller import PID

class BBQController(object):
    def __init__ (self, log=None):
        #Setup Logging
        if log != None:
            self.log = log
        else:
            self.log = logging.getLogger()
        #Check for vital pieces
        try:
            self.log.info("Checking for 1-Wire Thermometer")
            self.ambient_therm = W1ThermSensor() 
            #self.meat_therm = W1ThermSensor()
        except w1thermsensor.NoThermFound:
            self.log.error("Could not find any thermometers")

        #Set simulator flag (No fan, no temp sensor)
        self.simulator = False
        self.status_lock = threading.Lock()
       

        #Check for connection to internet
        noInternet = True
        if noInternet == True:
            self.local_status = True

        #Set Alg. Variables
        self.temp_loop_time = 2.0
        self.p_gain = 6 
        self.i_gain = 0.02
        self.d_gain = 0.0
        self.pid = PID(self.p_gain, self.i_gain, self.d_gain)
        
        self.fan = PWMFanController(self.log)

        #Setup Default Values
        self.enable_logging = False
        self.enable_pid = False
        self.status = {}

        self.target_ambient_temp = 235
        self.max_duty_cycle = 100
        self.min_duty_cycle = 25
        self.max_ambient_temp = 265
        self.min_ambient_temp = 205
        self.run_id = None
        self.pid.SetPoint = self.target_ambient_temp

        #Setup External Values
        self.value_lock = threading.Lock()

        #Setup Status Thread
        self.status_thread = None
        self.status_sleep_time = 1

        #Setup PID Controll Thread
        self.pid_thread = None
        self.pid_sleep_time = 1

        self.log.info("Initialization complete")

    def start(self):
        if self.status_thread:
            self.log.warn("Status thread already started; skipping")
        else:
            self.status_enable = True
            self.status_thread = threading.Thread(target=self.status_logger)
            self.status_thread.daemon = True
            self.status_thread.start()
        if self.pid_thread:
            self.log.warn("Temperature and PID thread already started; skipping")
        else:
            self.pid_enable = True
            self.pid_thread = threading.Thread(target=self.run_pid)
            self.pid_thread.daemon = True
            self.pid_thread.start()

    def stop(self):
        if not self.status_thread:
            self.log.warn("Status thread already stopped; skipping")
        else:
            self.status_enable = False
            self.status_thread.join(2)
            self.status_thread = None
        if not self.pid_thread:
            self.log.warn("Temp and PID thread already stopped; skipping")
        else:
            self.pid_enable = False
            self.pid_thread.join(2)
            self.pid_thread = None

    def set_target_ambient_temp(self, val):
        with self.value_lock.acquire():
            self.target_ambient_temp = val
            self.pid.SetPoint = val

    def convertPIDOutput(self, x):
        if x < 0:
            return 0
        elif x < self.min_duty_cycle:
            return 0
        elif x > self.max_duty_cycle:
            return self.max_duty_cycle
        else:
            return int(round(x))

    def log_data(self):
        self.log.info("Current Temp: %f F  Target Temp: %f  Tach Speed: %f" % (self.status["ambient_temp"], self.status["target_ambient_temp"], self.status["fan_speed"]))

    def run_pid(self):
        while self.pid_enable:
            try:
                self.status_lock.acquire()
                self.pid.update(self.status["ambient_temp"])
                self.fan.setDutyCycle(self.convertPIDOutput(self.pid.output))
            finally:
                self.status_lock.release()
            time.sleep(self.pid_sleep_time)

    def update_status(self):
        try:
            self.status_lock.acquire()
            self.status = {"timestamp": time.time(),
                           "ambient_temp": self.ambient_therm.get_temperature(W1ThermSensor.DEGREES_F),
                           "meat_temp": 0.0, 
                           "fan_duty_cycle": self.fan.getDutyCycle(),
                           "max_ambient_temp": self.max_ambient_temp,
                           "min_ambient_temp": self.min_ambient_temp,
                           "target_ambient_temp": self.target_ambient_temp,
                           "fan_speed": self.get_tach()
                          }
        finally:
            self.status_lock.release()

    def status_logger(self):
        while self.status_enable:
            self.update_status()
            try:
                self.status_lock.acquire()
                if self.enable_logging:
                    self.log_data()
            finally:
                self.status_lock.release()
            time.sleep(self.status_sleep_time)

    def get_tach(self):
        #TODO Implement Later
        return 0

    def get_ambient_temperature(self):
        return self.ambient_therm.get_temperature(W1ThermSensor.DEGREES_F)
    
