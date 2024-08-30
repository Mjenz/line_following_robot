// // PID CONTROL FOR LINE FOLLOWING ROBOT;
// // RECIEVES CENTER OF LINE FROM RASPI ZERO W AND USES PID CONTROL TO CREATE MOTOR COMMAND

// Import libraries
#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/uart.h"
#include "hardware/irq.h"
#include "hardware/i2c.h"

// Define PMW constants 
#define PWM_A1 15
#define PWM_B1 16 
#define PWM_MAX 65535

// Define state pins for H-bridge
#define STATE_A2 14
#define STATE_B2 17 

// Define UART constants
#define UART_ID uart0
#define BAUD_RATE 115200
#define DATA_BITS 8
#define STOP_BITS 1
#define PARITY    UART_PARITY_NONE
#define UART_TX_PIN 0
#define UART_RX_PIN 1

// Initialize PID Input: Center of line in range of 0-639 (width of image)
volatile int control_input;

// Initialize UART buffer and counter
char tracker[50];
volatile int counter = 0;

// // DEFINE HELPER FUNCTIONS

// Define UART recieve callback function 
void on_uart_rx() {

    // Check UART is readable
    while (uart_is_readable(UART_ID)) {
        uint8_t ch = uart_getc(UART_ID);    // get UART input
        
        // Check if byte is end of line character
        if (ch =='\n') {
            control_input = atoi(tracker);  // convert UART rx buffer to float
            counter = 0;                    // reset counter
            tracker[0] = '\0';              // reset rx buffer

        } else {
            tracker[counter] = ch;  // add byte to rx buffer (its part of input but not the end)
            counter = counter + 1; // increment counter
        }
    }
}

// Define state pin initialization function
void initialize_state() {
    // Initialize pin 14 and 17 as GPIO high/low output pins
    gpio_init(STATE_A2);
    gpio_set_dir(STATE_A2,GPIO_OUT);
    gpio_init(STATE_B2);
    gpio_set_dir(STATE_B2,GPIO_OUT);

    // set initially as forward (==0)
    gpio_put(STATE_A2,0);
    gpio_put(STATE_B2,0);
}

// Define UART initalizaiton function
void initialize_UART() {
    uart_init(UART_ID, BAUD_RATE);                          // UART initilialize, buad rate
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);         // Init transmitting pin (not used)
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);         // Init recieving pin
    uart_set_hw_flow(UART_ID, false, false);                // Hardware flow off
    uart_set_format(UART_ID, DATA_BITS, STOP_BITS, PARITY); // Initialize length of UART input
    uart_set_fifo_enabled(UART_ID, false);                  // Turn off FIFO
    int UART_IRQ = UART_ID == uart0 ? UART0_IRQ : UART1_IRQ;// Set UART_IRQ ID according to UART_ID value
    irq_set_exclusive_handler(UART_IRQ, on_uart_rx);        // Initialize UART callback
    irq_set_enabled(UART_IRQ, true);                        // Enable callback IRQ
    uart_set_irq_enables(UART_ID, true, false);             
}

// Define PWM initialization function
void initialize_PWM() {
    uint16_t wrap = 65535;                            // Initialize PWM rollover (max 65535)
    float div = 200;                                  // Initialize clock prescaler (max 255)

    gpio_set_function(PWM_A1, GPIO_FUNC_PWM);         // Set pin 15 as right motor PWM pin
    uint slice_num = pwm_gpio_to_slice_num(PWM_A1);   // Get PWM slice number
    pwm_set_clkdiv(slice_num, div);                   // Set prescaler
    pwm_set_wrap(slice_num, wrap);                    // Set wrap/rollover
    pwm_set_enabled(slice_num, true);                 // Enable the PWM pin
    pwm_set_gpio_level(PWM_A1,0);                     // Set the initial duty cycle to 0% PWM (stationary)

    gpio_set_function(PWM_B1, GPIO_FUNC_PWM);         // Set pin 16 as right motor PWM pin
    uint slice_num2 = pwm_gpio_to_slice_num(PWM_B1);  // Get PWM slice number
    pwm_set_clkdiv(slice_num, div);                   // Set prescaler
    pwm_set_wrap(slice_num2, wrap);                   // Set wrap/rollover
    pwm_set_enabled(slice_num2, true);                // Enable the PWM pin
    pwm_set_gpio_level(PWM_B1,0);                     // Set the initial duty cycle to 0% PWM (stationary)
}

// Define PWM set function
void set_PWM(int input1, int input2) {

    // Set right motor PWM
    pwm_set_gpio_level(PWM_A1,input1);

    // Set left motor PWM
    pwm_set_gpio_level(PWM_B1,input2);

}

// Define state pin set function (sets direction of motor) (NOT USED)
void set_state(int input1, int input2) {

    // Set right motor state pin
    gpio_put(STATE_A2,input1);

    // Set left motor state pin
    gpio_put(STATE_B2,input2);

}

// DEFINE MAIN FUNCTION

int main(){
    stdio_init_all();       // initialize pico standard input output
    initialize_PWM();       // run PWM init function
    initialize_state();     // run state pin init function
    initialize_UART();      // run UART init function

    // Define pwm variables
    int pwm_left, pwm_right;
    
    // Define PID variables
    float error, error_der, ei, ep;
    float P,I,D,u;

    // Define PID control parameters
    float Kp = .1, Ki = 0.001, Kd = 0.1;

    // Define I anti-windup clamping maximum
    float wind_max = 2.5;

    // Define motor PWM scaling terms (To account for motor power imbalance)
    float scale = 0.35;
    float scale_left = .5;
    
    // START PID CONTROL LOOP
    while(1) {
        tight_loop_contents();          // function for empty while loops

        // PID controller
        error = control_input - 320;    // calculate error, sign is backwards accounted for later (SP == 320 center of line)
        ei += error;                    // calculate integrated error
        error_der = error - ep;         // calculate derivative error
        if (ei > wind_max)              // perform clamping for anti windup
            ei = wind_max;          
        else if (ei < -wind_max)
            ei = -wind_max;
        P = Kp * error;                 // find P
        I = Ki * ei;                    // find I 
        D = Kd * error_der;             // find D
        u = P + I + D;              // find u
        ep = error;                     // save previous error
        if (u > 0){                                                         // if u is greater than zero, needs to turn left
            pwm_right = (int)(-u/100 * PWM_MAX + PWM_MAX * scale);          // scale down right motor speed from middle speed
            pwm_left  = (int)( u/100 * PWM_MAX + PWM_MAX * scale_left);     // scale up left motor from middle speed
        } else if(u <= 0){                                                  // if u is less than zero, need to turn right
            pwm_right = (int)(-u/100 * PWM_MAX + PWM_MAX * scale);          // scale up right motor from middle speed
            pwm_left  = (int)( u/100 * PWM_MAX  + PWM_MAX * scale_left);    // scale down left motor from middle speed
        } 
        set_PWM(pwm_right,pwm_left);    // Call pwm set function
    }
}