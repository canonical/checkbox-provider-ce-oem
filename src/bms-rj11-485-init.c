#include <stdio.h>
#include <fcntl.h>
#include <linux/ioctl.h>
#include <linux/serial.h>
#include <asm-generic/ioctls.h> /* TIOCGRS485 + TIOCSRS485 ioctl definitions */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
//#include <linux/pthread.h>
#include <sched.h>

//#include <sys/types.h>
//#include <sys/stat.h>

#include <fcntl.h>
//#include <sys/ioctl.h>


#include <errno.h>
//#include <uapi/asm-generic/ioctls.h>

int set_baud (int fd, int baud_rate );
int init_serial (char *path, int baud_rate);

int set_baud (int fd, int baud_rate )
{
    struct termios attr;

    if (tcgetattr(fd, &attr) <0)
    {
        printf("get serial attribute failed\n");
        return -1;
    }

    cfsetispeed(&attr, baud_rate);
    cfsetospeed(&attr, baud_rate);

    if (tcsetattr(fd,  TCSANOW, &attr) < 0)
    {
        printf("get serial attribute failed\n");
        return -1;
    }

    return 0;
}


int init_serial (char *path, int baud_rate)
{
    struct termios attr;
    int fd;

	fd = open ("/dev/ttySC0", O_RDWR);

    if (fd <= 0)
    {
        printf("open serial %s failed\n", path);
        perror("");
        return -1;
    }
    printf("open serial %s ok\n", path);
    attr.c_cflag = 0;

    if (tcgetattr(fd, &attr) <0)
    {
        printf("get serial attribute\n");
        close (fd);
        return -1;
    }
    printf("get attr ok\n", path);
    // Set to 8 bits, not parity 1 stop bit
    cfmakeraw(&attr) ;
    #if 0
    cfsetispeed(&attr, baud_rate);
    cfsetospeed(&attr, baud_rate);

    attr.c_cflag &= ~PARENB;
    attr.c_cflag &= ~CSTOPB;
    attr.c_cflag &= ~CRTSCTS;
    attr.c_cflag |= CS8;
	#endif
	cfsetispeed(&attr, baud_rate);
    cfsetospeed(&attr, baud_rate);
    
	attr.c_cflag &= ~PARENB;
    attr.c_cflag &= ~CSTOPB;
    attr.c_cflag |= CS8;


    if (tcsetattr(fd,  0, &attr) < 0)
    {
        printf("failed to set serial attribute\n");
        close (fd);
        return -1;
    }
	fcntl(fd,F_SETFL,FNDELAY);

    return fd;
}

union U{
float v;
unsigned char c[4];
unsigned int i;
}uu;

int main(void) {
         struct serial_rs485 rs485conf;
///
	char inbuff[256];
	int fd;	
	char outbuff[256];
	memset(inbuff,0x0,256);
///

	fd = init_serial ("/dev/ttySC0", B115200);

	if(fd < 0)
	{
	printf ("Initialize the serial port  failed\n");
	return -1;
	}

         /* Don't forget to read first the current state of the RS-485 options with ioctl.
            If You don't do this, You will destroy the rs485conf.delay_rts_last_char_tx
            parameter which is automatically calculated by the driver when You opens the
            port device. */
         if (ioctl (fd, TIOCGRS485, &rs485conf) < 0) {
                 printf("Error: TIOCGRS485 ioctl not supported.\n");
         }

         /* Enable RS-485 mode: */
         rs485conf.flags |= SER_RS485_ENABLED;
         rs485conf.flags |= SER_RS485_RTS_AFTER_SEND;

         /* Set rts/txen delay before send, if needed: (in microseconds) */
         rs485conf.delay_rts_before_send = 0;

         /* Set rts/txen delay after send, if needed: (in microseconds) */
         rs485conf.delay_rts_after_send = 0;

         if (ioctl (fd, TIOCSRS485, &rs485conf) < 0) {
                 printf("Error: TIOCSRS485 ioctl not supported.\n");
         }

         fcntl(fd, F_SETFL, 0);
         //int n = write(fd, "ABC\r\n", 5);
/////
/*	while(1)
	{
		//read
        printf ( "-read begin-\r\n");
		memset(outbuff,0,128);
    	int readnum = read(fd, &outbuff[0], 127);
        printf("readdata is %d\r\n",outbuff[0]);
 		
        //write
        inbuff[0]=outbuff[0];
        int n = write(fd, &inbuff[0], readnum);
        if (n < 0) 
        {
		 //Error handling
		    printf ( "write error \r\n");
		}
        else
        {
            printf("write %d back \r\n",inbuff[0]);
        }
			
		sleep(3);
	}
*/
/////
    if (close (fd) < 0) 
    {
        printf("Error: Can't close: /dev/ttySC0\n");
    }
 
}
