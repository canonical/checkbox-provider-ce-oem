#!/bin/bash
SNAP=tridium-lontest
result=()
logFile=''
exitcode=1
if ( ls /tmp/lon*.log 2>null ); then
   echo "Removing previous log file..."
   rm -f /tmp/lon*.log
fi
installLonSnap() {
    echo "Checking needed snap \"$SNAP\"..."
    snap list |grep -q "$SNAP"
    if [ $? = "1" ]; then
        echo "Installing snap \"$SNAP\""
        snap install "$SNAP" --devmode --edge
    else
        echo "Snap been installed"
    fi
}

enableLonModule() {
    lonTTY=( ACM2 ACM3 )
    for tty in "${lonTTY[@]}"
    do
        echo "Enabling \"$tty\""
        "$SNAP".lonifd -d /dev/tty"$tty" -l 28 &
        sleep 3
    done
}

getLonInterface() {
    lonInterfaces=()
    lon=$(ip a | grep lon | awk -F ": " '{print $2}' | sed -e '/^$/d')
    while IFS= read -r line
    do 
        lonInterfaces+=("$line") 
    done <<< "$lon"
    lonOne="${lonInterfaces[0]}"
    lonTwo="${lonInterfaces[1]}"
}

testSendLonMsg() {
    if [ "${1}" == "lon10" ]; then
        "$SNAP".lonc -l "$2" -p subnet=1,node=100,count=3,peermode=r | tee -a /tmp/"$1"To"$2".log &
        echo "Wait for 10 sec to setup \"$2\""
        sleep 10
        "$SNAP".lonc -l "$1" -p subnet=1,node=101,testnode=100,count=3,peermode=s | tee -a /tmp/"$1"To"$2".log &
        echo "Wait for 30 sec to testing send from \"$1\" to \"$2\""
        sleep 30
    else
        "$SNAP".lonc -l "$2" -p subnet=1,node=101,count=3,peermode=r | tee -a /tmp/"$1"To"$2".log &
        echo "Wait for 10 sec to setup \"$2\""
        sleep 10
        "$SNAP".lonc -l "$1" -p subnet=1,node=100,testnode=101,count=3,peermode=s | tee -a /tmp/"$1"To"$2".log &
        echo "Wait for 30 sec to testing send from \"$1\" to \"$2\""
        sleep 30
    fi
}

resultParser() {
    echo "Parser log"
    logFile=$(ls /tmp/"$1"To"$2".log)
    count=$(grep "PASSED" "$logFile" -c)
    if [ "$count" -lt 10 ]  ; then
        echo "LON test failed" 
        result+=("1")
    else 
        echo "LON test passed"
        result+=("0")
    fi
}

clearsession() {
    pgrep "lon" | while read PID; do kill -9 "$PID"; done
}

main() {
    enableLonModule
    getLonInterface
    ### testSendLonMsg {sender} {receiver}
    testSendLonMsg "$lonOne" "$lonTwo"
    resultParser "$lonOne" "$lonTwo"
    testSendLonMsg "$lonTwo" "$lonOne"
    resultParser "$lonTwo" "$lonOne"
    if [ "${result[0]}" = '1' ];then
        echo "\"$lonOne\" send failed"
    else
        echo "\"$lonOne\" send passed"
        exitcode=0
    fi
    if [ "${result[1]}" = '1' ];then
        echo "\"$lonTwo\" send failed"
        exitcode=1
    else
        echo "\"$lonTwo\" send passed"
        exitcode=0
    fi
    clearsession
    return $exitcode
}

main
exit $?