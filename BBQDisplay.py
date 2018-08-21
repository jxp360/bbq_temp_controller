#!/usr/bin/env python

import os, time, sys
import logging
import OLEDDisplay
import threading

from wifi import Cell, Scheme

class EditableOption(object):
    TIMEOUT = 5.0
    def __init__(self, log, cb=None):
        self.log = log
        self.cursor_location = -1
        self.callback = cb

    def upArrow(self):
        pass

    def downArrow(self):
        pass

    def rightArrow(self):
        pass

    def leftArrow(self):
        pass

    def enter(self):
        pass

    def back(self):
        pass

    def editValue(self):
        pass

    def getDisplay(self):
        pass

class EnumeratedEditableField(EditableOption):
    def __init__(self, log, values, default_value, callback=None):
        super(EnumeratedEditableField, self).__init__(log, callback)
        self.value = default_value
        self.values = values
        
    def _getStringRep(self):
        return str(self.value)

    def editValue(self):
        if self.cursor_location == -1:
             self.cursor_locations = 0
        else:
             self.log.warn("editValue called but cursor already not equal to -1")

    def upArrow(self):
        old_val = self._getStringRep()
        old_val_idx = self.values.find(old_val)
        new_val_idx = old_val_idx + 1
        if new_val_idx >= len(self.values):
            new_val_idx = 0
        new_val = self.values[new_val_idx]
        self.temp_value = new_val
        if self.cb:
            self.cb()

    def downArrow(self):
        old_val = self._getStringRep()
        old_val_idx = self.values.find(old_val)
        new_val_idx = old_val_idx - 1
        if new_val_idx <= 0:
            new_val_idx = len(self.values) - 1
        new_val = self.values[new_val_idx]
        self.temp_value = new_val
        if self.cb:
            self.cb()

    def enter(self):
        if self.temp_value != self.value:
            self.log.debug("Setting new value from %s to %s" % (self.value, self.temp_value))
            self.value = self.temp_value
            self.temp_value = None
        self.cursor_location = -1

    def back(self):
        self.log.debug("Throwing away temp value %s" % self.temp_value)
        self.temp_value = None
        self.cursor_location = -1

    def getDisplay(self):
        return (str(self.value), None)


class IntegerEditableField(EditableOption):
    def __init__(self, log, default_value, max_digits=3, callback=None):
        super(IntegerEditableField, self).__init__(log, callback)
        self.value = default_value
        self.max_digits = max_digits
        
    def _getStringRep(self):
        return str(self.value).zfill(max_digits)

    def _checkValid(self, value):
        return value > 0 and value < (10^self.max_digits)

    def editValue(self):
        if self.cursor_location == -1:
             self.cursor_locations = 0
        else:
             self.log.warn("editValue called but cursor already not equal to -1")

    def upArrow(self):
        old_val = self._getStringRep()
        if self.cursor_location < 0:
            self.log.error("editValue was not called before upArrow called; returning")
            return
        elif self.cursor_location > self.max_digits:
            self.log.error("upArrow cannot be called on position %d which is greater then max digits" % self.cursor_location)
            return
        new_int = int(old_val[self.cursor_location])
        new_int += 1
        if new_int > 9:
            new_int = 9
        new_val = old_val
        new_val[self.cursor_location] = str(new_int)
        if self._checkValue(int(new_val)):
            self.temp_value = int(new_val)
            if self.cb:
                self.cb()

    def downArrow(self):
        old_val = self._getStringRep()
        if self.cursor_location < 0:
            self.log.error("editValue was not called before downArrow called; returning")
            return
        elif self.cursor_location > self.max_digits:
            self.log.error("downArrow cannot be called on position %d which is greater then max digits" % self.cursor_location)
            return
        new_int = int(old_val[self.cursor_location])
        new_int -= 1
        if new_int < 0:
            new_int = 0
        new_val = old_val
        new_val[self.cursor_location] = str(new_int)
        if self._checkValue(int(new_val)):
            self.temp_value = int(new_val)
            if self.cb:
                self.cb()

    def leftArrow(self):
        curpos = self.cursor_location
        curpos -= 1
        if curpos < 0:
            curpos = 0
        if curpos != self.cursor_location:
            if self.cb:
                self.cb()

    def rightArrow(self):
        curpos = self.cursor_location
        curpos += 1
        if curpos >= self.max_digits:
            curpos = self.max_digits
        if curpos != self.cursor_location:
            if self.cb:
                self.cb()

    def enter(self):
        if self.temp_value != self.value:
            self.log.debug("Setting new value from %d to %d" % (self.value, self.temp_value))
            self.value = self.temp_value
            self.temp_value = None
        self.cursor_location = -1

    def back(self):
        self.log.debug("Throwing away temp value %d" % self.temp_value)
        self.temp_value = None
        self.cursor_location = -1

    def getDisplay(self):
        if self.cursor_location < 0:
            return (str(self.value).rjust(self.max_digits), None)
        else:
            return (str(self.temp_value).zfill(self.max_digits), self.cursor_location) 

class CallbackField(object):
    def __init__(self, log, callback):
        self.log = log
        self.cb = callback

    def getDisplay(self):
        pass

class FloatCallbackField(CallbackField):
    def __init__(self, log, callback, decimal_places=1):
        super(FloatCallbackField, self).__init__(log, callback)
        self.dp = decimal_places
        self.value = float(self.cb())

    def getDisplay(self):
        return ("{:.{}f}".format(self.value, self.dp), None)


class BBQDisplay(threading.Thread):
    ENTER_BUTTON = 24
    BACK_BUTTON = 25
    UP_BUTTON = 26
    DOWN_BUTTON = 27
    
    def __init__(self, log=None):
        '''
        Main Menu
        Header -> Time Date Connected to Wifi Alert
        Menu
        Current Temp ->
        Target Temp ->
        Fan Duty/Speed ->
        Options

        Set Temp Options
        Target Temp
        Max Temp Alarm
        Min Temp Alarm

        Set Network Options
        Wifi Status: Connected
        Wifi Network: Name
        Edit Wifi Network

        Set Logging Options
        Username
        Password
        IFFT Account
        '''
        self.header_state = {"datetime": time.gmtime(),
                             "wifi":  None,
                             "alert": False
                             }

        self.display = OLEDDisplay.OLEDDisplay()

        self.target_temp = 215

        if log == None:
             self.log = logging.getLogger(__name__)
        else:
             self.log = log

        self.current_amb_temp = FloatCallbackField(self.log, self.getCurrentAmbientTemp)
        self.current_meat_temp = FloatCallbackField(self.log, self.getCurrentMeatTemp)
        self.target_amb_temp = IntegerEditableField(self.log, 235, max_digits=3) 
        self.duty_cycle = 100
                          
        self.max_amb_temp_alarm = IntegerEditableField(self.log, 260, max_digits=3)
        self.min_amb_temp_alarm = IntegerEditableField(self.log, 200, max_digits=3)
        self.enable_controller = EnumeratedEditableField(self.log, ["On", "Off"], "Off")
        self.refreshTempMenu()

        self.options_menu = [{"name": "Temp Options", "value": self.temp_menu, "type":"submenu"}]
                             #{"name": "Network Options", "value": self.net_menu, "type":"submenu"},
                             #{"name": "Logging Options", "value": self.log_menu, "type":"submenu"}]
                            
        self.state = "main"
        self.selector = 0
        self.timeout_value = 3.0
        self.selector_time = -1.0
        self.editting = False
        self.editting_last_time = time.time()
        self.last_update_time = time.time()

    def getCurrentTemp(self):
        return "98.3"
    def getCurrentAmbientTemp(self):
        return "98.3"
    def getCurrentMeatTemp(self):
        return "98.3"

    def refreshMainMenu(self):
        self.main_menu = [{"name": "Current Temp", "value": self.current_amb_temp, "type": "variable"}, 
                          {"name": "Target Temp", "value": self.target_amb_temp, "type": "variable"}, 
                          {"name": "Enable", "value": self.enable_controller, "type":"variable"},
                          {"name": "Options", "value": self.options_menu, "type":"submenu"}]

    def refreshTempMenu(self):
        self.temp_menu =  [{"name": "Target Temp", "value": self.target_amb_temp, "callback": self.setTargetTemp, "type":"variable", "mode": "rw"},
                           {"name": "Fan Duty Cyc", "value": self.duty_cycle, "type": "fixed"},
                           {"name": "Max Temp Alarm", "value": self.max_amb_temp_alarm, "type":"variable", "mode": "rw"},
                           {"name": "Min Temp Alarm", "value": self.min_amb_temp_alarm, "type":"variable", "mode": "rw"}]

    def checkWifiState(self):
        Cell.all("wlan0")
        self.header_state["wifi"] = True
        self.header_state["wifi_power"] = 90

    def checkAlerts(self):
        alerts = False

    def setTargetTemp(self, val):
        self.target_temp = val

    def updateHeader(self):
        self.header_state["datetime"] = time.gmtime()
        #self.checkWifiState()
        self.checkAlerts()

        #timestr = time.strftime("%m/%d/%Y %H:%M:%S") 
        timestr = time.strftime("%H:%M:%S") 

        self.display.writeHeader(timestr + " " + "Good")

    def _updateInternalTime(self):
        now = time.time()
        td = now - self.last_update_time
        if self.selector_time != -1.0:
            self.selector_time -= td
            if self.selector_time < 0:
                 self.selector_time = -1.0

    def updateBody(self):
        if self.state == "main":
            lines = []
            for idx,x in enumerate(self.main_menu):
                if self.selector_time > 0.0 and idx == self.selector:
                    first_char = "*"
                else:
                    first_char = " "
                if x["type"] == "variable": 
                    dispstr, cursor = x["value"].getDisplay()
                    if not cursor:
                        lines.append(first_char+ " " + x["name"] + ": " + dispstr)
                    else:
                        lines.append(first_char+ " " + x["name"] + ": " + dispstr)
                if x["type"] == "fixed": 
                    dispstr, cursor = x["value"], None
                    lines.append(first_char+ " " + x["name"] + ": " + str(dispstr))

                elif x["type"] == "submenu":
                    lines.append(first_char+ " " +x["name"])
        self._updateInternalTime()
        self.display.writeMenu(lines)

    def upArrowCB(self):
        '''
        if self.if in menu
            find all things you can do, submenu and callback variables
            move to next idx (with gaps)
        if editting
        '''
        pass

    def downArrowCB(self):
        pass

    def leftArrowCB(self):
        pass

    def rightArrowCB(self):
        pass

    def enterCB(self):
        pass
        

    def backCB(self):
        pass

if __name__ == "__main__":

    disp = BBQDisplay()
    runs = 5
    for x in xrange(runs):
        disp.updateHeader()
        disp.refreshMainMenu()
        disp.updateBody()
        time.sleep(1)

