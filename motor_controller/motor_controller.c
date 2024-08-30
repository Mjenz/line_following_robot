#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"

#include "hardware/uart.h"
#include "hardware/irq.h"
#include "hardware/i2c.h"

#define PWM_A1 15
#define STATE_A2 14
#define PWM_B1 16 
#define STATE_B2 17 

#define UART_ID uart0
#define BAUD_RATE 115200
#define DATA_BITS 8
#define STOP_BITS 1
#define PARITY    UART_PARITY_NONE
#define PWM_MAX 65535

#define UART_TX_PIN 0
#define UART_RX_PIN 1

static int chars_rxed = 0;
volatile int counter = 0;
volatile int input;
char tracker[50];
volatile int control_input;


void on_uart_rx() {
    while (uart_is_readable(UART_ID)) {
        uint8_t ch = uart_getc(UART_ID);

        if (ch =='\n') {
            // printf("WHILE STRING IS READABLE\n %d",ch);
            char ms[50];
            // sprintf(ms,"From pico: %s\r\n", tracker);
            printf(ms);
            control_input = atoi(tracker);
            counter = 0;
            tracker[0] = '\0';

            
        } else {
            tracker[counter] = ch;
            counter = counter + 1;
        }
        chars_rxed++;
    }
}


void initialize_state() {
    gpio_init(STATE_A2);
    gpio_set_dir(STATE_A2,GPIO_OUT);
    gpio_init(STATE_B2);
    gpio_set_dir(STATE_B2,GPIO_OUT);

    // set initially as forward (==0)
    gpio_put(STATE_A2,0);
    gpio_put(STATE_B2,0);
}

void initialize_UART() {
    uart_init(UART_ID, 115200);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    uart_set_hw_flow(UART_ID, false, false);
    uart_set_format(UART_ID, DATA_BITS, STOP_BITS, PARITY);
    uart_set_fifo_enabled(UART_ID, false);
    int UART_IRQ = UART_ID == uart0 ? UART0_IRQ : UART1_IRQ;
    irq_set_exclusive_handler(UART_IRQ, on_uart_rx);
    irq_set_enabled(UART_IRQ, true);
    uart_set_irq_enables(UART_ID, true, false);


}

void initialize_PWM() {
  gpio_set_function(PWM_A1, GPIO_FUNC_PWM); // Set the LED Pin to be PWM
  uint slice_num = pwm_gpio_to_slice_num(PWM_A1); // Get PWM slice number
  float div = 200; // must be between 1-255
  pwm_set_clkdiv(slice_num, div); // divider
  uint16_t wrap = 65535; // when to rollover, must be less than 65535
  pwm_set_wrap(slice_num, wrap);
  pwm_set_enabled(slice_num, true); // turn on the PWM
  pwm_set_gpio_level(PWM_A1, wrap / 2); // set the duty cycle to 50%

  gpio_set_function(PWM_B1, GPIO_FUNC_PWM); // Set the LED Pin to be PWM
  uint slice_num2 = pwm_gpio_to_slice_num(PWM_B1); // Get PWM slice number
  pwm_set_clkdiv(slice_num, div); // divider
  pwm_set_wrap(slice_num2, wrap);
  pwm_set_enabled(slice_num2, true); // turn on the PWM
  pwm_set_gpio_level(PWM_B1, wrap / 2); // set the duty cycle to 50%

  pwm_set_gpio_level(PWM_A1,0);
  pwm_set_gpio_level(PWM_B1,0);
}

void set_PWM(int input1, int input2) {
    // char ms[50];
    // sprintf(ms,"setting PWM as %d\r\n",input1);
    // printf(ms);
    pwm_set_gpio_level(PWM_A1,input1);
    pwm_set_gpio_level(PWM_B1,input2);


}

void set_state(int input1, int input2) {
    // char ms[50];
    // sprintf(ms,"setting state as %d\r\n",input1);
    // printf(ms);
    gpio_put(STATE_A2,input1);
    gpio_put(STATE_B2,input2);


}

int main(){
    stdio_init_all();

    // initilize LED pin and blink
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN,GPIO_OUT);
    gpio_put(PICO_DEFAULT_LED_PIN,1);
    sleep_ms(500);
    gpio_put(PICO_DEFAULT_LED_PIN,0);
   
    initialize_PWM();
    initialize_state();
    initialize_UART();
    int pwm1;
    int pwm2;
    int dir1;
    int dir2;
    int scaled1;
    int scaled2;
    char ms[50];
    int pwm_left, pwm_right;


    float error, error_der, ei, ep;
    float P,I,D,F,u;
    float Kp = .1, Ki = 0.001, Kd = 0.1, Kf = 0.0;
    float wind_max = 2.5;

    // works!
    // float scale = 0.25;
    // float scale_left = .4;

    // works!
    // float scale = 0.3;
    // float scale_left = .45;

    // works!
    float scale = 0.35;
    float scale_left = .5;

    // works! 
    // float scale = 0.4;
    // float scale_left = .55;

    // doesn't work :(
    // float scale = 0.45;
    // float scale_left = .60;
    
    while(1) {
        // why do i need this function?
        tight_loop_contents();

        // print control value received
        // sprintf(ms,"Recieved: %d\r\n", control_input);
        printf(ms);


        // PID controller
        error = control_input - 320; // calculate error
        ei += error;                // calculate integrated error
        error_der = error - ep;     // calculate derivative error
        if (ei > wind_max)          // perform clamping as anti windup
            ei = wind_max;          
        else if (ei < -wind_max)
            ei = -wind_max;
        P = Kp * error;             // find P
        I = Ki * ei;                // find I 
        D = Kd * error_der;         // find D
        F = Kf * control_input;     // find ff term
        u = P + I + D + F;          // find u
        ep = error;                 // save previous error
        if (u > 0){                 // set pwm based on sign of u
            pwm_right = (int)(-u/100 * PWM_MAX + PWM_MAX * scale);
            pwm_left  = (int)( u/100 * PWM_MAX + PWM_MAX * scale_left);
        } else if(u <= 0){
            pwm_right = (int)(-u/100 * PWM_MAX + PWM_MAX * scale);// negative sign is the same because u will be negative
            pwm_left  = (int)( u/100 * PWM_MAX  + PWM_MAX * scale_left);
        } // else {
        //     pwm_right = 0;
        //     pwm_left = 0;
        // }
        printf("right %d left %d u %f error %f\n",pwm_right,pwm_left,u,error);

        set_PWM(pwm_right,pwm_left);
        // sprintf(ms, "pwm1: %d, pwm2  %d\r\n", pwm_right, pwm_left);
        printf(ms);
        

    }
}