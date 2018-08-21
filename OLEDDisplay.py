#!/usr/bin/env python

import os, sys
import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess
import threading
import logging

class OLEDDisplay(object):
    RST = None
    DC = 23
    SPI_PORT = 0
    SPI_DEVICE = 0

    def __init__(self, log=None, address=0x3C):
        self.log = log
        if self.log == None:
            self.log = logging.getLogger("OLEDDisplay")

        # Note you can change the I2C address by passing an i2c_address parameter like:
        self.log.info("Initializing OLED Display with address %s" % str(address))
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=OLEDDisplay.RST, i2c_address=address)

        # Initialize library.
        self.disp.begin()
        self.display_lock = threading.Lock()
        self.clearDisplay()

        self.image = Image.new('1', (self.disp.width, self.disp.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
        self.x_offset = 0
        self.y_offset = 0

        self.blankImage()

        self.header = None
        self.menu = None
        self.cursor_position = None
        self.cursor_position = (3,8)
        self.cursor_blink_interval = 0.2

        self._debug_image = True
        
        self.cursor_thread = None
        self.startCursor()

    def startCursor(self):
        if not self.cursor_position:
            print "Enter cursor_position before starting cursor"
            self.log.error("Enter cursor_position before starting cursor")
        if self.cursor_thread != None:
            print "Cursor already enabled"
            self.log.warn("Cursor already enabled")
            return
        self._enableCursor = True
        self._cursorState = False
        self.cursor_thread = threading.Thread(target=self.checkCursor)
        self.cursor_thread.start()

    def stopCursor(self):
        self._enableCursor = False
        self.cursor_thread.join(2)
        self.cursor_thread = None

    def checkCursor(self):
        self._cursorState = False
        print "Checking cursor"
        while self._enableCursor:
            if not self.cursor_position:
                time.sleep(0.5)
                continue
            if self._cursorState:
                self._cursorState = False
                print "Cursor off"
            else:
                self._cursorState = True
                print "Cursor on"
            with self.display_lock:
                self.updateDisplay()
            time.sleep(self.cursor_blink_interval)

    def drawCursor(self, row, col, fill=255):
        pixels_per_row = 8
        pixels_per_char = 6
        #self.draw.line([((row+1)*pixels_per_row-1, col*pixels_per_char), ((row+1)*pixels_per_row-1, (col+1)*pixels_per_char-1)], fill=255, width=1)  
        self.draw.line([(col*pixels_per_char, (row+1)*pixels_per_row+1), ((col+1)*pixels_per_char-1, (row+1)*pixels_per_row+1)], fill=fill, width=1)  

    def clearDisplay(self):
        self.log.info("Clearing display")
        with self.display_lock:
            self.disp.clear()
            self.disp.display()

    def blankImage(self):
        self.blankHeader()
        self.blankMenu()

    def blankHeader(self):
        self.draw.rectangle((0,0,self.disp.width,16), outline=0, fill=0)

    def blankMenu(self):
        self.draw.rectangle((0,16,self.disp.width, self.disp.height-16), outline=0, fill=0)

    def writeHeader(self, txt):
        self.header = txt
        with self.display_lock:
            self.blankHeader()
            self.draw.text((self.x_offset, self.y_offset), self.header, font=self.font, fill=255)
            self.updateDisplay()

    def writeMenu(self, lines=None):
        if lines != None:
            self.menu = lines
        if self.menu == None:
            print "Nothing to write"
            return
        with self.display_lock:
            self.blankMenu()
            for idx, txt in enumerate(self.menu):
                self.draw.text((self.x_offset, self.y_offset+(idx)*8+ 16), txt, font=self.font, fill=255)
            self.updateDisplay()

    def updateDisplay(self):
        if self._cursorState:
            self.drawCursor(self.cursor_position[0], self.cursor_position[1])
        else:
            self.drawCursor(self.cursor_position[0], self.cursor_position[1], fill=0)
        self.disp.image(self.image)
        self.disp.display()
        if self._debug_image:
            self.image.save("/tmp/%s.jpg" % str(time.time()), "JPEG")

if __name__ == "__main__":

    disp = OLEDDisplay()

    while True:

        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell = True )
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell = True )
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell = True )
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        Disk = subprocess.check_output(cmd, shell = True )

        # Write two lines of text.

        disp.writeHeader("IP: " + str(IP))
        menu = [str(CPU), str(MemUsage), str(Disk)]
        disp.writeMenu(menu)
        disp.cursor_position = (4,13)
        time.sleep(0.3)

