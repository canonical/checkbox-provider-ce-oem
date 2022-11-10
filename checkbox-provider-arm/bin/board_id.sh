#!/bin/bash
current_boardId=''
imx6pdk_boardId='0000'
gpioList=( 499 500 501 502 )
for gpio in "${gpioList[@]}"
do
        echo "$gpio" > /sys/class/gpio/export && echo "in" > /sys/class/gpio/gpio"$gpio"/direction
        current_boardId=$current_boardId$(cat /sys/class/gpio/gpio"$gpio"/value)
done
if [ "$current_boardId" == "$imx6pdk_boardId" ]
then
        echo "Board ID is ${current_boardId} and it's correct"
        exit 0
else
        echo "Board ID is ${current_boardId} and it's incorrect"
        exit 1
fi