# TinyFPGA Programmer
The TinyFPGA Programmer is a very simple USB-JTAB bridge designed to 
program bitstreams onto TinyFPGA A1 and A2 boards.  

## Serial Protocol
The programmer firmware appears as a generic USB serial port when you connect it
to a computer.  Control of the GPIO pins on the programmer is through this simple
serial interface.  

### Command Format
Commands are encoded as 8-bit bytes with a command type field and data payload.
The payload is typically a 6-bit bitmap representing the GPIO pins of the programmer.

|      7:6     | 5 | 4 | 3 | 2 | 1 | 0 |
|--------------|---|---|---|---|---|---|
| Command Type |TMS|TCK|TDI|TDO|RC1|RC0|

### Commands

|Opcode |             Command           |
|-------|-------------------------------|
|   0   | Configure Input/Output        |
|   1   | Extended Command (Unused)     |
|   2   | Set Outputs                   |
|   3   | Set Outputs and Sample Inputs |

#### Configure Input/Output
For each of the GPIO pins, set the direction of the pin.  
* 1: Set GPIO pin n to INPUT
* 0: Set GPIO pin n to OUTPUT

#### Extended Command
Reserved for future command expansion.

#### Set Outputs
Set each of the output pins to the given values.

#### Set Outputs and Sample Inputs
Set each of the output pins to the given values and return a byte representing
the current values of the input pins.  

### General Usage
For serial interfaces like JTAG this protocol divides the maximum possible bandwidth
by 8 from the USB to JTAG interface.  This means we might get 0.5MHz JTAG programming speed.
That speed is actually fast enough to transfer all the data to the FPGA in a few seconds.  However
the configuration flash on the FPGA actually needs a fair bit of time after erase and write operations
that will slow down the programming operatuon.

What can really slow down programming is the turnaround time for reading back data from the FPGA.  
For the most part data is going in one direction from the host computer to the programmer to the FPGA.  
For these cases we can  use the `Set Outputs` command and not wait for any data to return.  However 
there are times when we may  need to poll a status bit to see if the FPGA has finished an erase or 
write operation.  In this cases we will want to also sample the inputs and check the status.  These 
should not be timing sensitive because the FPGA is already busy.

Verifying the configuration data on the other hand could take a long time if not done carefully.  The
application talking to the programmer should make sure to write as many commands as it can before attempting
to read back the data from the serial interface.  Rather than paying a penalty for the turnaround time on
every read bit, we pay for it after reading dozens of bytes.  This should allow read-back of the configuration
data to be relatively quick and painless.

## Status
The project is currently in progress.  Initial schematic and PCBs have
been designed along with firmware for the USB microcontroller.  The PCBs
have been received from OSH Park and programmed with the firwmware.

The biggest task left is still developing the Python libraries for interfacing 
with the firmware and driving the JTAG interface and is currently in progress.
