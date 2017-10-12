EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:pic
LIBS:tinyfpga
LIBS:TinyFPGA-A-Programmer-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "TinyFPGA Programmer"
Date "2017-10-05"
Rev "v1.1"
Comp "TinyFPGA"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L PIC16F1455-QFN16 U1
U 1 1 598405FB
P 2000 4400
F 0 "U1" H 3200 4550 60  0000 R CNN
F 1 "PIC16F1455-QFN16" H 3600 4400 60  0000 R CNN
F 2 "Housings_DFN_QFN:QFN-16-1EP_4x4mm_Pitch0.65mm" H 2000 4400 60  0001 C CNN
F 3 "" H 2000 4400 60  0001 C CNN
	1    2000 4400
	1    0    0    -1  
$EndComp
$Comp
L MIC5504-3.3YM5-TR U2
U 1 1 5984065C
P 2350 1300
F 0 "U2" H 2550 1550 60  0000 L CNN
F 1 "MIC5504-3.3YM5-TR" H 2550 1450 60  0000 L CNN
F 2 "TinyFPGA:SOT23" H 2350 1300 60  0001 C CNN
F 3 "" H 2350 1300 60  0001 C CNN
	1    2350 1300
	1    0    0    -1  
$EndComp
$Comp
L C C1
U 1 1 5984091E
P 1950 1550
F 0 "C1" H 1975 1650 50  0000 L CNN
F 1 "1uF" H 1975 1450 50  0000 L CNN
F 2 "Capacitors_SMD:C_0603" H 1988 1400 50  0001 C CNN
F 3 "" H 1950 1550 50  0001 C CNN
	1    1950 1550
	1    0    0    -1  
$EndComp
$Comp
L C C2
U 1 1 59840991
P 3900 1550
F 0 "C2" H 3925 1650 50  0000 L CNN
F 1 "1uF" H 3925 1450 50  0000 L CNN
F 2 "Capacitors_SMD:C_0603" H 3938 1400 50  0001 C CNN
F 3 "" H 3900 1550 50  0001 C CNN
	1    3900 1550
	1    0    0    -1  
$EndComp
$Comp
L C C4
U 1 1 598409EE
P 5050 4600
F 0 "C4" H 5075 4700 50  0000 L CNN
F 1 "1uF" H 5075 4500 50  0000 L CNN
F 2 "Capacitors_SMD:C_0603" H 5088 4450 50  0001 C CNN
F 3 "" H 5050 4600 50  0001 C CNN
	1    5050 4600
	0    1    1    0   
$EndComp
$Comp
L C C3
U 1 1 59840AB1
P 4300 1550
F 0 "C3" H 4325 1650 50  0000 L CNN
F 1 "100nF" H 4325 1450 50  0000 L CNN
F 2 "Capacitors_SMD:C_0603" H 4338 1400 50  0001 C CNN
F 3 "" H 4300 1550 50  0001 C CNN
	1    4300 1550
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR3
U 1 1 59840C77
P 3350 3250
F 0 "#PWR3" H 3350 3000 50  0001 C CNN
F 1 "GND" H 3350 3100 50  0000 C CNN
F 2 "" H 3350 3250 50  0001 C CNN
F 3 "" H 3350 3250 50  0001 C CNN
	1    3350 3250
	0    -1   -1   0   
$EndComp
$Comp
L +3V3 #PWR2
U 1 1 59840CA3
P 2950 3250
F 0 "#PWR2" H 2950 3100 50  0001 C CNN
F 1 "+3V3" H 2950 3390 50  0000 C CNN
F 2 "" H 2950 3250 50  0001 C CNN
F 3 "" H 2950 3250 50  0001 C CNN
	1    2950 3250
	0    -1   -1   0   
$EndComp
Wire Wire Line
	3100 3400 3100 3250
Wire Wire Line
	3100 3250 2950 3250
Wire Wire Line
	3200 3400 3200 3250
Wire Wire Line
	3200 3250 3350 3250
$Comp
L GND #PWR8
U 1 1 59840FB3
P 5400 4600
F 0 "#PWR8" H 5400 4350 50  0001 C CNN
F 1 "GND" H 5400 4450 50  0000 C CNN
F 2 "" H 5400 4600 50  0001 C CNN
F 3 "" H 5400 4600 50  0001 C CNN
	1    5400 4600
	0    -1   -1   0   
$EndComp
Wire Wire Line
	5200 4600 5400 4600
Wire Wire Line
	4900 4600 4300 4600
$Comp
L +3V3 #PWR7
U 1 1 5984106F
P 4700 1200
F 0 "#PWR7" H 4700 1050 50  0001 C CNN
F 1 "+3V3" H 4700 1340 50  0000 C CNN
F 2 "" H 4700 1200 50  0001 C CNN
F 3 "" H 4700 1200 50  0001 C CNN
	1    4700 1200
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR5
U 1 1 5984108F
P 2950 2200
F 0 "#PWR5" H 2950 1950 50  0001 C CNN
F 1 "GND" H 2950 2050 50  0000 C CNN
F 2 "" H 2950 2200 50  0001 C CNN
F 3 "" H 2950 2200 50  0001 C CNN
	1    2950 2200
	1    0    0    -1  
$EndComp
$Comp
L +5V #PWR1
U 1 1 598410AF
P 1600 1200
F 0 "#PWR1" H 1600 1050 50  0001 C CNN
F 1 "+5V" H 1600 1340 50  0000 C CNN
F 2 "" H 1600 1200 50  0001 C CNN
F 3 "" H 1600 1200 50  0001 C CNN
	1    1600 1200
	1    0    0    -1  
$EndComp
Wire Wire Line
	3550 1400 4700 1400
Connection ~ 3900 1400
Wire Wire Line
	4700 1400 4700 1200
Connection ~ 4300 1400
Wire Wire Line
	1600 1200 1600 1400
Wire Wire Line
	1600 1400 2350 1400
Connection ~ 1950 1400
Wire Wire Line
	2350 1400 2350 1300
Wire Wire Line
	2950 2000 2950 2200
Wire Wire Line
	1950 1700 1950 2100
Wire Wire Line
	1950 2100 4300 2100
Connection ~ 2950 2100
Wire Wire Line
	3900 2100 3900 1700
Wire Wire Line
	4300 2100 4300 1700
Connection ~ 3900 2100
$Comp
L CONN_01X05 J2
U 1 1 598412AC
P 3100 6550
F 0 "J2" H 3100 6850 50  0000 C CNN
F 1 "JTAG" V 3200 6550 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x05_Pitch2.54mm" H 3100 6550 50  0001 C CNN
F 3 "" H 3100 6550 50  0001 C CNN
	1    3100 6550
	0    -1   1    0   
$EndComp
$Comp
L GND #PWR4
U 1 1 59841444
P 3450 6250
F 0 "#PWR4" H 3450 6000 50  0001 C CNN
F 1 "GND" H 3450 6100 50  0000 C CNN
F 2 "" H 3450 6250 50  0001 C CNN
F 3 "" H 3450 6250 50  0001 C CNN
	1    3450 6250
	0    -1   -1   0   
$EndComp
Wire Wire Line
	2000 4700 1750 4700
Wire Wire Line
	1750 4700 1750 6050
Wire Wire Line
	1750 6050 2900 6050
Wire Wire Line
	2900 6050 2900 6350
Wire Wire Line
	3000 5700 3000 6350
Wire Wire Line
	3100 5700 3100 6350
Wire Wire Line
	3200 5700 3200 6050
Wire Wire Line
	3200 6050 3300 6050
Wire Wire Line
	3300 6050 3300 6350
Wire Wire Line
	3450 6250 3200 6250
Wire Wire Line
	3200 6250 3200 6350
$Comp
L USB_OTG J1
U 1 1 598417AF
P 5050 3700
F 0 "J1" H 4850 4150 50  0000 L CNN
F 1 "USB" H 4850 4050 50  0000 L CNN
F 2 "TinyFPGA:FCI-Micro-USB" H 5200 3650 50  0001 C CNN
F 3 "" H 5200 3650 50  0001 C CNN
	1    5050 3700
	-1   0    0    -1  
$EndComp
Wire Wire Line
	4750 3800 4450 3800
Wire Wire Line
	4450 4500 4300 4500
Wire Wire Line
	5300 4100 5300 4600
Wire Wire Line
	5050 4100 5300 4100
Connection ~ 5300 4600
Connection ~ 5150 4100
$Comp
L +5V #PWR6
U 1 1 59841909
P 4500 3300
F 0 "#PWR6" H 4500 3150 50  0001 C CNN
F 1 "+5V" H 4500 3440 50  0000 C CNN
F 2 "" H 4500 3300 50  0001 C CNN
F 3 "" H 4500 3300 50  0001 C CNN
	1    4500 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	4500 3300 4500 3500
Wire Wire Line
	4500 3500 4750 3500
$Comp
L CONN_01X06 J3
U 1 1 59841999
P 7650 4600
F 0 "J3" H 7650 4950 50  0000 C CNN
F 1 "ICSP" V 7750 4600 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x06_Pitch2.54mm" H 7650 4600 50  0001 C CNN
F 3 "" H 7650 4600 50  0001 C CNN
	1    7650 4600
	1    0    0    -1  
$EndComp
Text GLabel 4500 5000 2    60   Input ~ 0
ICSPDAT
Wire Wire Line
	4300 4700 4350 4700
Wire Wire Line
	4350 4700 4350 5000
Wire Wire Line
	4350 5000 4500 5000
Text GLabel 3500 5850 2    60   Input ~ 0
ICSPCLK
Wire Wire Line
	3300 5700 3300 5850
Wire Wire Line
	3300 5850 3500 5850
Text GLabel 1400 4600 0    60   Input ~ 0
VPP
Wire Wire Line
	2000 4600 1400 4600
$Comp
L GND #PWR13
U 1 1 598420BF
P 7300 5100
F 0 "#PWR13" H 7300 4850 50  0001 C CNN
F 1 "GND" H 7300 4950 50  0000 C CNN
F 2 "" H 7300 5100 50  0001 C CNN
F 3 "" H 7300 5100 50  0001 C CNN
	1    7300 5100
	1    0    0    -1  
$EndComp
Wire Wire Line
	7300 5100 7300 4550
Wire Wire Line
	7300 4550 7450 4550
$Comp
L +3V3 #PWR12
U 1 1 59842121
P 7300 4250
F 0 "#PWR12" H 7300 4100 50  0001 C CNN
F 1 "+3V3" H 7300 4390 50  0000 C CNN
F 2 "" H 7300 4250 50  0001 C CNN
F 3 "" H 7300 4250 50  0001 C CNN
	1    7300 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	7300 4250 7300 4450
Wire Wire Line
	7300 4450 7450 4450
Text GLabel 7050 4350 0    60   Input ~ 0
VPP
Wire Wire Line
	7050 4350 7450 4350
Text GLabel 7050 4650 0    60   Input ~ 0
ICSPDAT
Text GLabel 7050 4750 0    60   Input ~ 0
ICSPCLK
Wire Wire Line
	7050 4650 7450 4650
Wire Wire Line
	7450 4750 7050 4750
Wire Wire Line
	3550 1300 3550 1400
$Comp
L CONN_01X06 J4
U 1 1 59ADF270
P 7650 2900
F 0 "J4" H 7650 3250 50  0000 C CNN
F 1 "CONN_01X06" V 7750 2900 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x06_Pitch2.54mm" H 7650 2900 50  0001 C CNN
F 3 "" H 7650 2900 50  0001 C CNN
	1    7650 2900
	1    0    0    -1  
$EndComp
$Comp
L +3V3 #PWR10
U 1 1 59ADF4D2
P 7200 2500
F 0 "#PWR10" H 7200 2350 50  0001 C CNN
F 1 "+3V3" H 7200 2640 50  0000 C CNN
F 2 "" H 7200 2500 50  0001 C CNN
F 3 "" H 7200 2500 50  0001 C CNN
	1    7200 2500
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR11
U 1 1 59ADF4FA
P 7300 3300
F 0 "#PWR11" H 7300 3050 50  0001 C CNN
F 1 "GND" H 7300 3150 50  0000 C CNN
F 2 "" H 7300 3300 50  0001 C CNN
F 3 "" H 7300 3300 50  0001 C CNN
	1    7300 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	7300 2650 7300 3300
Text GLabel 6950 3050 0    60   Input ~ 0
ICSPDAT
Text GLabel 6950 3150 0    60   Input ~ 0
ICSPCLK
Text GLabel 6950 2950 0    60   Input ~ 0
RA4
Text GLabel 6950 2850 0    60   Input ~ 0
RA5
Wire Wire Line
	6950 2850 7450 2850
Wire Wire Line
	6950 2950 7450 2950
Wire Wire Line
	6950 3050 7450 3050
Wire Wire Line
	6950 3150 7450 3150
Text GLabel 1400 4400 0    60   Input ~ 0
RA5
Text GLabel 1400 4500 0    60   Input ~ 0
RA4
Wire Wire Line
	1400 4400 2000 4400
Wire Wire Line
	2000 4500 1400 4500
Wire Wire Line
	7300 2650 7450 2650
Wire Wire Line
	7200 2500 7200 2750
Wire Wire Line
	7200 2750 7450 2750
$Comp
L TEST TP3
U 1 1 59AE1FC1
P 1200 1550
F 0 "TP3" H 1200 1850 50  0000 C BNN
F 1 "TEST" H 1200 1800 50  0000 C CNN
F 2 "Measurement_Points:Measurement_Point_Round-SMD-Pad_Big" H 1200 1550 50  0001 C CNN
F 3 "" H 1200 1550 50  0001 C CNN
	1    1200 1550
	1    0    0    -1  
$EndComp
$Comp
L TEST TP1
U 1 1 59AE210A
P 4300 3700
F 0 "TP1" H 4300 4000 50  0000 C BNN
F 1 "TEST" H 4300 3950 50  0000 C CNN
F 2 "Measurement_Points:Measurement_Point_Round-SMD-Pad_Big" H 4300 3700 50  0001 C CNN
F 3 "" H 4300 3700 50  0001 C CNN
	1    4300 3700
	1    0    0    -1  
$EndComp
$Comp
L TEST TP2
U 1 1 59AE214D
P 4450 4150
F 0 "TP2" H 4450 4450 50  0000 C BNN
F 1 "TEST" H 4450 4400 50  0000 C CNN
F 2 "Measurement_Points:Measurement_Point_Round-SMD-Pad_Big" H 4450 4150 50  0001 C CNN
F 3 "" H 4450 4150 50  0001 C CNN
	1    4450 4150
	0    1    1    0   
$EndComp
$Comp
L +5V #PWR9
U 1 1 59AE2249
P 1200 1550
F 0 "#PWR9" H 1200 1400 50  0001 C CNN
F 1 "+5V" H 1200 1690 50  0000 C CNN
F 2 "" H 1200 1550 50  0001 C CNN
F 3 "" H 1200 1550 50  0001 C CNN
	1    1200 1550
	-1   0    0    1   
$EndComp
Wire Wire Line
	4450 3800 4450 4500
Connection ~ 4450 4150
Wire Wire Line
	4300 4400 4300 3700
Wire Wire Line
	4300 3700 4750 3700
Text Notes 6550 2250 0    60   ~ 0
GPIO for custom applications
Text Notes 6450 3950 0    60   ~ 0
PIC in circuit programming header
Text Notes 2650 850  0    60   ~ 0
Power supply
Text Notes 2600 3000 0    60   ~ 0
PIC16F1455 connections
$EndSCHEMATC
