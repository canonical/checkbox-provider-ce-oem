#!/bin/bash
MTD_PATH="/sys/class/mtd/"
MTDS=$(ls /dev/mtd[0-9] | awk -F "/" '{print $3}')
listAllMtd() {
    for c in ${MTDS}; do
        echo "MTD_NAME: ${c}"
        awk -F "=" '/OF_NAME/ { if ($2 == "mram" || $2 == "fram") print "MTD_TYPE: "$2; else print "MTD_TYPE: norflash" }' "${MTD_PATH}""${c}"/uevent
        echo ""
    done
}

countAllMtd() {
    #$1: type of MTD $2: total number of MTD
    fram=0
    mram=0
    norflash=0
    for c in $MTDS; do
        type=$(awk -F "=" '/OF_NAME/ { print $2 }' "${MTD_PATH}""${c}"/uevent)
        case ${type} in
                mram) mram=$((mram+1)) ;;
                fram) fram=$((fram+1)) ;;
                *) norflash=$((norflash+1))
        esac
    done
    if [ $((${1})) == "${2}" ]; then
        echo "Number of ""${1}"" are correct!"
    else
        echo "Number of ""${1}"" are incorrect!"
        exit 1 
    fi
}

listTotalNum() {
    #List from checkbox config ${TOTAL_MTD_NUM}
    for i in ${1}; do
        awk -F ":" '{print "TYPE: "$1 "\nNUM: "$2}' <<< "${i}"
        echo ""
    done
}

main(){
    case ${1} in
        list) listAllMtd ;;
        total) listTotalNum "${2}" ;;
        count) countAllMtd "${2}" "${3}" ;;
        *) echo "Need given parameter."
    esac
}

main "$@"
exit $?