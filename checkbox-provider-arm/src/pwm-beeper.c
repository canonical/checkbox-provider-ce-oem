#include<stdint.h>
#include<string.h>
#include<fcntl.h>
#include<unistd.h>
#include<stdio.h>
#include<linux/input.h>
#include<unistd.h>
 
int main(int argc, char *argv[])
{
 
        int fd, version, ret;
        struct input_event event;
 
        if ((fd = open("/dev/input/event1", O_RDWR)) < 0) {
 
                perror("beep test");
                return 1;
        }
 
        event.type = EV_SND;
        event.code = SND_TONE;
        event.value = 1000;
 
        ret = write(fd, &event, sizeof(struct input_event));

	sleep(1);
        event.value = 0;
        ret = write(fd, &event, sizeof(struct input_event));
 
        close(fd);
 
        return 0;
}
