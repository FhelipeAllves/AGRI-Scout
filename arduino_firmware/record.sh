#!/bin/bash
echo "Compiling..."
arduino-cli compile --fqbn arduino:avr:uno $1

if [ $? -eq 0 ]; then
    echo "Sending to Arduino..."
    arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno $1
    echo "Success!"
else
    echo "Compilation error."
fi
