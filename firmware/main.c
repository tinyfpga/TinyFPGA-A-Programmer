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

#include "stdint.h"

#define MAX_PKT_SIZE 64
//static uint8_t usb_rx_buf[MAX_PKT_SIZE];

static uint8_t usb_rx_buf[MAX_PKT_SIZE] = {
    0, 7,
    8, 0, 0, 0, 16, 0, 16, 0,
    9, 1, 0, 0, 16, 32, 48, 0,
    10, 1, 0, 0, 16, 8, 24, 32,
    11, 4, 4, 0, 16, 0, 16, 32,
    12, 12, 4, 0, 16, 0, 16, 32,
    0, 15,
    
    28, 8, 3, 67, 255, 160, 255, 43, 255, 1, 255
};

static uint8_t usb_tx_buf[MAX_PKT_SIZE];

#include "mcc_generated_files/mcc.h"
#include "pt.h"
#include "stdio.h"


static uint8_t usb_rx_bytes_avail = 55;
static uint8_t usb_rx_ptr = 0;
static uint8_t usb_tx_ptr = 0;

struct sie_config_t {
    uint8_t config_byte;
    uint8_t input_mask;
    uint8_t do0p0;
    uint8_t do0p1;
    uint8_t do1p0;
    uint8_t do1p1;
    uint8_t last_phase_overlay;
    uint8_t dummy;
};


static struct sie_config_t sie_configs[8];



#define GET_BYTE(pt, dst)\
    PT_WAIT_UNTIL(pt, usb_rx_ptr < usb_rx_bytes_avail);\
    dst = usb_rx_buf[usb_rx_ptr];\
    usb_rx_ptr += 1;



#define SEND_BYTE(pt, src)\
    PT_WAIT_UNTIL(pt, USBUSARTIsTxTrfReady() && (usb_tx_ptr < MAX_PKT_SIZE));\
    usb_tx_buf[usb_tx_ptr] = src;\
    usb_tx_ptr += 1;



void putch(char data) {
    usb_tx_buf[usb_tx_ptr] = data;
    usb_tx_ptr += 1;
}

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
 * FIXME: this is outdated, please update with latest command definitions
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

void inline gpio_init() {
    TRISC = 0b111111;
}

/**
 * Process GPIO and SIE commands from host.
 */
PT_THREAD(cmd_task(struct pt* pt)) {
    static uint8_t gpio_dir = 0b111111;
    
    static uint8_t cmd;
    static uint8_t op0;
    static uint8_t sie;
    static uint8_t num_bits;
    static uint8_t num_bytes;
    static uint8_t input_mask;
    static uint8_t do0p0;
    static uint8_t do0p1;
    static uint8_t do1p0;
    static uint8_t do1p1;
    static uint8_t inout_cfg;
    static uint8_t i;
    
    static uint8_t loop_start = 3; // loop is always contained in a single packet
    static uint16_t loop_count;
    static uint8_t loop_is_active = 0;
    
    
    static uint8_t actual_data;
    static uint8_t expected_data;
    static uint8_t mask;
    
    static uint8_t byte_to_send;
    
    
    static uint8_t compare_data_matches = 1;
    static uint8_t data;
    
    static const uint8_t STATUS_SUCCESS = 0;
    static const uint8_t STATUS_FAIL = 1;
    static uint8_t status = 0; 
    static uint8_t status_sent = 0;
    
    PT_BEGIN(pt);
    
    while (1) {
        PT_YIELD(pt);
        GET_BYTE(pt, cmd);
        
        
    
        //printf("CMD: %02x", cmd);
        
        op0 = cmd & 0xc0;
        
        if (op0 == 0x40) {
            // SET CMD
            LATC = cmd & ~gpio_dir;
            
        } else if (op0 == 0x80) {
            // SET_GET CMD
            byte_to_send = PORTC & gpio_dir;
            LATC = cmd & ~gpio_dir;
            SEND_BYTE(pt, byte_to_send);
            
        } else {
            uint8_t op1 = cmd & 0xF8;
            
            if (op1 == 0x18) {
                // SHIFT CMD
                sie = cmd & 0x7;

                GET_BYTE(pt, num_bits);
                GET_BYTE(pt, num_bytes);
                
                do0p0 = sie_configs[sie].do0p0;
                do0p1 = sie_configs[sie].do0p1;
                inout_cfg = sie_configs[sie].config_byte & 0xf;
                
                
                if (inout_cfg == 0x0C) { // DATA COMPARE ONLY
                    compare_data_matches = 1;
                    
                    input_mask = sie_configs[sie].input_mask;
                
                    for (i = 0; i < num_bytes; i += 1) {
                        actual_data = 0;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x01;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x02;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x04;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x08;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x10;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x20;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x40;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | 0x80;
                 
                        
                        GET_BYTE(pt, expected_data);
                        GET_BYTE(pt, mask);
                        
                        if ((expected_data & mask) != (actual_data & mask)) {
                            compare_data_matches = 0;
                        }
                    }

                    actual_data = 0;
                    uint8_t bit_to_set = 1;

                    for (i = 0; i < num_bits - 1; i += 1) {
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) actual_data = actual_data | bit_to_set;

                        bit_to_set = bit_to_set << 1;
                    }
                
                    uint8_t last_phase_overlay = sie_configs[sie].last_phase_overlay;
                            
                    LATC = do0p0 | last_phase_overlay;
                    LATC = do0p1 | last_phase_overlay;
                    if (PORTC & input_mask) actual_data = actual_data | bit_to_set;
                    
                    
                    GET_BYTE(pt, expected_data);
                    GET_BYTE(pt, mask);

                    if ((expected_data & mask) != (actual_data & mask)) {
                        compare_data_matches = 0;
                    }
                    
                    if (loop_is_active) {
                        if (compare_data_matches) {
                            loop_is_active = 0;
                        }
                    } else {
                        if (!compare_data_matches) {
                            status = STATUS_FAIL;
                            
                            if (!status_sent) {
                                SEND_BYTE(pt, STATUS_FAIL);
                                status_sent = 1;
                            }
                        }
                    }
                    
                    
                    
                } else if (inout_cfg == 4) { // SHIFT DATA IN ONLY
                    input_mask = sie_configs[sie].input_mask;
                
                    for (i = 0; i < num_bytes; i += 1) {
                        data = 0;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x01;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x02;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x04;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x08;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x10;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x20;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x40;
                        
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | 0x80;
                 
                        SEND_BYTE(pt, data);
                    }

                    data = 0;
                    uint8_t bit_to_set = 1;

                    for (i = 0; i < num_bits - 1; i += 1) {
                        LATC = do0p0;
                        LATC = do0p1;
                        if (PORTC & input_mask) data = data | bit_to_set;

                        bit_to_set = bit_to_set << 1;
                    }
                
                    uint8_t last_phase_overlay = sie_configs[sie].last_phase_overlay;
                            
                    LATC = do0p0 | last_phase_overlay;
                    LATC = do0p1 | last_phase_overlay;
                    if (PORTC & input_mask) data = data | bit_to_set;
                    
                    SEND_BYTE(pt, data);
                
                } else if (inout_cfg == 1) { // SHIFT DATA OUT ONLY
                    do1p0 = sie_configs[sie].do1p0;
                    do1p1 = sie_configs[sie].do1p1;
                
                    for (i = 0; i < num_bytes; i += 1) {
                        GET_BYTE(pt, uint8_t data);
                        
                        if (data & 0x01) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x02) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x04) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x08) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x10) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x20) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x40) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                        
                        if (data & 0x80) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }
                    }

                    GET_BYTE(pt, uint8_t data);

                    for (i = 0; i < num_bits - 1; i += 1) {
                        if (data & 1) {
                            LATC = do1p0;
                            LATC = do1p1;
                        } else {
                            LATC = do0p0;
                            LATC = do0p1;
                        }

                        data = data >> 1;
                    }
                
                    uint8_t last_phase_overlay = sie_configs[sie].last_phase_overlay;
                            
                    if (data & 1) {
                        LATC = do1p0 | last_phase_overlay;
                        LATC = do1p1 | last_phase_overlay;
                    } else {
                        LATC = do0p0 | last_phase_overlay;
                        LATC = do0p1 | last_phase_overlay;
                    }
                    
                } else if (inout_cfg == 0) { // RUN PHASE 0 PATTERN ONLY
                    for (i = 0; i < num_bytes; i += 1) {
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                        LATC = do0p0;
                        LATC = do0p1;
                    }

                    for (i = 0; i < num_bits; i += 1) {
                        LATC = do0p0;
                        LATC = do0p1;
                    }
                }
                
            } else if (cmd == 0x10) {
                // LOOP CMD
                GET_BYTE(pt, uint8_t tmp);
                loop_count = tmp;
                
                GET_BYTE(pt, tmp);
                loop_count |= ((uint16_t) tmp) << 8;
                
                loop_is_active = 1;
                
            } else if (cmd == 0x11) {
                // END_LOOP CMD
                loop_count -= 1;
                
                if (loop_count > 0) {
                    if (loop_is_active) {
                        // loop is not complete, continue
                        usb_rx_ptr = loop_start;
                    } else {
                        // loop is complete, exit loop
                    }
                    
                } else {
                    // loop counter has expired, check if loop is active
                    if (loop_is_active) {
                        // we should have matched before now, send error
                        status = STATUS_FAIL;
                        status_sent = 1;
                        SEND_BYTE(pt, STATUS_FAIL);
                    }
                    
                    loop_is_active = 0;
                }
                
                
                
            } else if (op1 == 0x08) {
                // CONFIG_SIE CMD
                sie = cmd & 0x7;
                
                GET_BYTE(pt, sie_configs[sie].config_byte);
                GET_BYTE(pt, sie_configs[sie].input_mask);
                GET_BYTE(pt, sie_configs[sie].do0p0);
                GET_BYTE(pt, sie_configs[sie].do0p1);
                GET_BYTE(pt, sie_configs[sie].do1p0);
                GET_BYTE(pt, sie_configs[sie].do1p1);
                GET_BYTE(pt, sie_configs[sie].last_phase_overlay);
                
            } else if (cmd == 0x20) {
                // CLEAR STATUS CMD
                status = STATUS_SUCCESS;
                status_sent = 0;
                
            } else if (cmd == 0x21) {
                // GET STATUS CMD
                SEND_BYTE(pt, status);
                status_sent = 1;
                
            } else {
                // CONFIG_IO CMD
                GET_BYTE(pt, cmd);
                gpio_dir = cmd & 0x3f;
                TRISC = gpio_dir;
            }
        }
        
                
    } // while
    
    PT_END(pt); 
}

/**
 * Manage CMD RX buffer
 */
void inline cmd_rx_buffer_task() {
    if (usb_rx_ptr >= usb_rx_bytes_avail) {
        usb_rx_bytes_avail = getsUSBUSART(usb_rx_buf, MAX_PKT_SIZE);
        usb_rx_ptr = 0;
    }
}

/**
 * Manage CMD TX buffer
 */
void inline cmd_tx_buffer_task() {    
    if (USBUSARTIsTxTrfReady() && usb_tx_ptr > 0) {
        putUSBUSART(usb_tx_buf, usb_tx_ptr);
        usb_tx_ptr = 0;  
    }
}

/**
 * Main program.  Initialize the system and USB device, then process GPIO
 * commands from USB forever.
 */
void main(void) {
    struct pt cmd_pt;
    PT_INIT(&cmd_pt);
    
    usb_rx_bytes_avail = 55;
    usb_rx_ptr = 0;
    usb_tx_ptr = 0;
    
    SYSTEM_Initialize();
    USBDeviceInit();
    gpio_init();
    
    while (1) {
        usb_task();
        cmd_rx_buffer_task();
        cmd_tx_buffer_task();
        cmd_task(&cmd_pt);
    }
}