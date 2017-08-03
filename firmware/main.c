/*
 * USB GPIO FW for a PIC16F1455.
 * 2017 Luke Valenty (lvalenty@gmail.com) 
 * 
 * This FW implements a very simple USB GPIO device using a PIC16F1455
 * microcontroller.  It enables control of the lower 6 PORTC GPIO pins 
 * for both input and output.  Input/output settings are configurable at
 * runtime.
 * 
 * The primary purpose of this FW is to allow the development of a cheap
 * JTAG programmer board for the TinyFPGA A-Series boards.  However, because
 * of it's flexibility it may be used for other tasks as well.
 */

#include "mcc_generated_files/mcc.h"

#define MAX_PKT_SIZE 64

#define CFG_CMD 0x00
#define EXT_CMD 0x40
#define SET_CMD 0x80
#define SETGET_CMD 0xC0

/**
 * Give some CPU time to the generic USB and CDC tasks so they can manage
 * generic USB device tasks and CDC UART data transfers.
 */
void inline usb_task() {
    USBDeviceTasks();
        
    if (
        (USBGetDeviceState() >= CONFIGURED_STATE) &&
        (USBIsDeviceSuspended() == false)
    ) {
        CDCTxService();
    } 
}

/**
 * Command Structure
 * -----------------
 * bit 7-6: Command Type
 * bit 5-0: Command Data
 * 
 * Command Types
 * -------------
 * 0: CFG - Configure Input/Output
 *     Command data represents GPIO pins 5-0
 *     1: set GPIO pin n to INPUT
 *     0: set GPIO pin n to OUTPUT
 * 
 * 1: EXT - Extended Command
 *     Currently unused
 * 
 * 2: SET - Set output pins without sampling inputs
 *     1: set output GPIO pin n to 1
 *     0: set output GPIO pin n to 0
 *     For INPUT pins there is no change
 * 
 * 3: SETGET - Set output pins and return current value of input pins
 *     Same encoding as SET but a bitmap representing current state of input
 *     pins is returned.
 */
bool inline process_gpio_cmd(uint8_t cmd, uint8_t* rsp) {
    static uint8_t gpio_dir = 0;
    uint8_t cmd_type = cmd & 0xC0;
    
    switch (cmd_type) {
        case CFG_CMD:
            gpio_dir = cmd & 0x3f;
            TRISC = gpio_dir;
            return false;
        
        case EXT_CMD:
            return false;
        
        case SET_CMD:
            LATC = cmd & ~gpio_dir;
            return false;
        
        case SETGET_CMD:
            LATC = cmd & ~gpio_dir;
            (*rsp) = PORTC & gpio_dir;
            return true;
    }
}

void inline gpio_init() {
    TRISC = 0b111111;
}

/**
 * Manage USB RX and TX buffers.  Process GPIO commands and send any response
 * back to the USB host.
 */
void inline gpio_task() {
    static uint8_t usb_rx_buf[MAX_PKT_SIZE];
    static uint8_t usb_tx_buf[MAX_PKT_SIZE];
    
    if (USBUSARTIsTxTrfReady()) {
        uint8_t bytes_rcvd = getsUSBUSART(usb_rx_buf, MAX_PKT_SIZE);
        uint8_t tx_ptr = 0;
        
        for (uint8_t rx_ptr = 0; rx_ptr < bytes_rcvd; rx_ptr++) {
            bool has_output = process_gpio_cmd(usb_rx_buf[rx_ptr], &usb_tx_buf[tx_ptr]);
            
            if (has_output) {
                tx_ptr += 1;
            }
        }
        
        if (tx_ptr > 0) {
            putUSBUSART(usb_tx_buf, tx_ptr);
        }
    }
}

/**
 * Main program.  Initialize the system and USB device, then process GPIO
 * commands from USB forever.
 */
void main(void) {
    SYSTEM_Initialize();
    USBDeviceInit();
    gpio_init();
    
    while (1) {
        usb_task();
        gpio_task();
    }
}