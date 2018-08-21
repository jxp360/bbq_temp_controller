#!/usr/bin/env python

import os, sys, time
import bbq_controller
import logging

if __name__ == "__main__":

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    bbq = bbq_controller.BBQController(log=log)
    bbq.enable_logging = True 
    log.info("Just testing")
    bbq.start()
    log.info("Waiting for sleep")
    time.sleep(30)
 
    bbq.stop()
    bbq.fan.setDutyCycle(0)

