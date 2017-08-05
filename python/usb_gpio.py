import serial
import array
from time import sleep



class Pins(object):
    def __init__(self, ser):
        self.ser = ser
        self.pin_output_values = 0
        self.pin_input_values = 0

    def prepare_batch():
        pass

    def set(self, pin, new_value):
        if new_value:
            self.pin_output_values |= (1 << pin)
        else:
            self.pin_output_values &= ~(1 << pin)


    def update(read_back = False):
        ser.write(array.array('B', [0b11000000 | self.pin_output_values]).tostring())
        pass

    def execute_batch():
        pass



with serial.Serial("COM16", 10000000, timeout=1, writeTimeout=0.1) as ser:
  ser.write(array.array('B', [0b00111011]).tostring())
  while True:
    ser.write(array.array('B', [0b10000100]).tostring())
    sleep(0.05)
    ser.write(array.array('B', [0b10000000]).tostring())
    sleep(0.05)

  #print str(array.array('B',  ser.read(1)).tolist())

