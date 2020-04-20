import sys
import traceback
import argparse
import serial
from serial.tools.list_ports import comports
import tinyfpgaa

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", action="store_true", help="Silent mode.")
    parser.add_argument("-p", type=str, help="Manually specify serial device.")
    parser.add_argument("-b", action="store_true", help="Input is bitstream file.")
    parser.add_argument("jed", type=str, help="JEDEC or bitstream file to program.")
    args = parser.parse_args()

    if not args.p:
        for port in comports():
            if "1209:2101" in port[2]:
                a_port = port[0]
                break
        else:
            print("TinyFPGA A not detected! Is it plugged in?")
            sys.exit(1)
    else:
        a_port = args.p

    with serial.Serial(a_port, 12000000, timeout=10, writeTimeout=5) as ser:
        async_serial = tinyfpgaa.SyncSerial(ser)
        pins = tinyfpgaa.JtagTinyFpgaProgrammer(async_serial)
        jtag = tinyfpgaa.Jtag(pins)
        programmer = tinyfpgaa.JtagCustomProgrammer(jtag)

        if not args.q:
            if args.b:
                print("Parsing bitstream file...")
            else:
                print("Parsing JEDEC file...")

        if args.b:
            input_file = tinyfpgaa.BitstreamFile(open(args.jed, 'rb'))
        else:
            input_file = tinyfpgaa.JedecFile(open(args.jed, 'r'))

        try:
            if not args.q:
                print("Programming TinyFPGA A on {}...".format(a_port))
            programmer.program(input_file)
        except:
            print("Programming Failed!")
            traceback.print_exc()
            sys.exit(2)

    print("Programming finished without error.")

if __name__ == "__main__":
    main()
