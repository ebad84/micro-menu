# micro menu

Simple MicroPython class to create simple and no-functioned menu without callbacks so you can build your own stuff. 

## Installation

just copy two files in your esp8266 or other device(mine is wemos d1 mini with OLED 0.96 128x64 ssd1306)
first the ssd1306.py lib(get it from micropython itself. ssd1306.py version 0.1.0 is used in this repo)
second the micromenu.py

## Usage

connect display to your board and replace GPIO pins for ssd1306 in line 55
then run the code!!
there is a simple menu running in your device
you can change position with typing "u" for moving to up, and "d" for moving to down. "s" for printing selected item and "q" for exit
read the code, its simple
