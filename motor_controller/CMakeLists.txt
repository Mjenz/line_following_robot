add_executable(motor_controller
        motor_controller.c
        )

# pull in common dependencies and additional uart hardware support
target_link_libraries(motor_controller pico_stdlib hardware_pwm hardware_uart hardware_irq hardware_i2c)


pico_enable_stdio_usb(motor_controller 1)
pico_enable_stdio_uart(motor_controller 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(motor_controller)






