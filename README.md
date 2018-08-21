Requirements:
  - PWM Fan on Pin 18 on Raspberry Pi 3
  - 1-wire Temperature Control
  - IFFT Account

Installation:
  - Install RPIO
    * sudo apt-get install python-setuptools
    * sudo easy_install -U RPIO

For Therm:
  - Check /boot/config.txt
  - Add line at bottom 
    *  dtoverlay=w1-gpio,gpiopin=17
  - Orange Stripe = VCC, White = Ground, Blue Stripe = Pull-up output
  - Run test_therm.py 

For Display:
  - Connect up pins 3 and 5 for i2c
  - run sudo raspi-config, go to intefaces, i2c, enable loading of modules
  - pip install Adafruit-SSD1306
  - Go get the newest version using wget
  wget https://raw.githubusercontent.com/adafruit/Adafruit_Python_SSD1306/master/Adafruit_SSD1306/SSD1306.py
  - Cp SDD1306.py /usr/local/lib/python2.7/dist-utils/Adafruit-SSD1306
  - run test_disp.py
 

For wifi:
  - sudo pip install wifi
