{'AMPY_BAUD': 115200,
 'AMPY_DELAY': 0.0,
 'AMPY_PORT': 'COM1',
 'LOCAL_PATH': './',
 'REMOTE_PATH': '/flash/',
 'unused': None}
>> unused key unused in ampy.json
from m5stack import *
import utime as time

lcd.clear(lcd.BLACK)
lcd.font(lcd.FONT_DejaVu24)
lcd.print('Demo Game', 0, 0, lcd.WHITE)
time.sleep(1)

if buttonB.wasPressed()
  import examples.rps_game
else:
  lcd.clear(lcd.WHITE)
  lcd.print("void...")