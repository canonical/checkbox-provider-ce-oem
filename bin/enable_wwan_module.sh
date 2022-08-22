#!/bin/bash
echo 509 > /sys/class/gpio/export 
echo "out" > /sys/class/gpio/gpio509/direction 
echo 1 > /sys/class/gpio/gpio509/value

echo 506 > /sys/class/gpio/export 
echo "out" > /sys/class/gpio/gpio506/direction
echo 0 > /sys/class/gpio/gpio506/value

echo 507 > /sys/class/gpio/export 
echo "out" > /sys/class/gpio/gpio507/direction 
echo 0 > /sys/class/gpio/gpio507/value

echo 504 > /sys/class/gpio/export 
echo "out" > /sys/class/gpio/gpio504/direction 
echo 0 > /sys/class/gpio/gpio504/value

echo 1 > /sys/class/gpio/gpio504/value
sleep 10;
echo 0 > /sys/class/gpio/gpio504/value

echo 506 > /sys/class/gpio/unexport 
echo 507 > /sys/class/gpio/unexport 
echo 504 > /sys/class/gpio/unexport