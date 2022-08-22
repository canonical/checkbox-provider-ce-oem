#define _XOPEN_SOURCE 1 /* for ptsname */
#define _GNU_SOURCE   1 /* "" */

#include "sc16is7xx.h"

#include <unistd.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/select.h>
#include <fcntl.h>
#include <pthread.h>  

#include <termios.h>

#define DEFAULT_DEVICE    "/dev/i2c-0"
#define DEFAULT_COMM_DEVICE    "/dev/ttymxcx"
#define DEFAULT_I2C_ADDR  0x4d
#define DEFAULT_BAUDRATE  115200

pthread_t ntid;

int set_opt(int fd, int nSpeed, int nBits, char nEvent, int nStop)
{
    struct termios newtio,oldtio;
    
    if ( tcgetattr(fd, &oldtio) != 0) 
    { 
        perror("SetupSerial 1");
        return -1;
    }
    bzero( &newtio, sizeof( newtio ) );
    newtio.c_cflag |= CLOCAL | CREAD; 
    newtio.c_cflag &= ~CSIZE; 

    switch( nBits )
    {
    case 7:
        newtio.c_cflag |= CS7;
        break;
    case 8:
        newtio.c_cflag |= CS8;
        break;
    }

    switch( nEvent )
    {
    case 'O':
        newtio.c_cflag |= PARENB;
        newtio.c_cflag |= PARODD;
        newtio.c_iflag |= (INPCK | ISTRIP);
        break;
    case 'E': 
        newtio.c_iflag |= (INPCK | ISTRIP);
        newtio.c_cflag |= PARENB;
        newtio.c_cflag &= ~PARODD;
        break;
    case 'N': 
        newtio.c_cflag &= ~PARENB;
        break;
    }

    switch( nSpeed )
    {
    case 2400:
        cfsetispeed(&newtio, B2400);
        cfsetospeed(&newtio, B2400);
        break;
    case 4800:
        cfsetispeed(&newtio, B4800);
        cfsetospeed(&newtio, B4800);
        break;
    case 9600:
        cfsetispeed(&newtio, B9600);
        cfsetospeed(&newtio, B9600);
        break;
    case 115200:
        cfsetispeed(&newtio, B115200);
        cfsetospeed(&newtio, B115200);
        break;
    default:
        cfsetispeed(&newtio, B9600);
        cfsetospeed(&newtio, B9600);
        break;
    }
    
    if( nStop == 1 )
    {
        newtio.c_cflag &= ~CSTOPB;        
    }
    else if ( nStop == 2 )
    {
        newtio.c_cflag |= CSTOPB;
        newtio.c_cc[VTIME] = 0;
        newtio.c_cc[VMIN] = 0;
        tcflush(fd,TCIFLUSH);
    }
    
    if((tcsetattr(fd, TCSANOW, &newtio))!=0)
    {
        perror("com set error");
        return -1;
    }
    printf("set done!\n");
    return 0;
}

static int uartfd = -1, pipefd = -1; 

int open_com_port(char *path)  
{    
    int tmpfd = -1;
    tmpfd = open(path, O_RDWR);
    if(tmpfd == -1)  
    {  
        perror("Can't Open SerialPort");  
    }  
   
    set_opt(tmpfd, 115200, 8, 'N', 1);
    fcntl(tmpfd, F_SETFL, FNDELAY);
    return tmpfd;  
}  

int uart_write(int fd, void *buf, size_t nbytes)
{
    return write(fd, buf, nbytes);
}

int success_count = 0;
void *thread(void *arg)  
{  
    fd_set readfds;
    struct timeval tv;

    char buf[6];
    
    int ret, i, size, res;
    
    printf("thread run...\n");
    
    while(1)
    {
        // uart write
        uart_write(uartfd, "\x01\x02\x03\x04\x05\x06", 6);
        
        // uart read
        FD_ZERO(&readfds);
        FD_SET(uartfd, &readfds);
        
        tv.tv_sec  = 5;
        tv.tv_usec = 0;
        
        memset(buf, 0, sizeof(buf));
        
        ret = select(uartfd + 1, &readfds, NULL, NULL, &tv);
        if(ret < 0)
        {
            printf("select error\n");
            success_count = -1;
            pthread_exit(0);
        }
        else if(ret > 0)
        {    
            if(FD_ISSET(uartfd, &readfds))
            {
                //printf("receive data\n");
                size = read(uartfd, buf, 6); 
                if(size == 6 && memcmp(buf, "\x01\x02\x03\x04\x05\x06", 6) == 0)
                {
                    success_count++;
                    if(success_count > 4)
                    {
                        pthread_exit(0);
                    }
                }
            }
        }
        else
        {
            printf("select continue\n");
            success_count = -1;
            pthread_exit(0);
        }
        
        sleep(1);
    }
    return ((void *)0);  
}  

void
usage(char *argv0)
{
	fprintf(stderr,"Usage: %s [options]\n", argv0);
	fprintf(stderr,"  -d  DEV    i2c or spi device node (df: %s)\n",
		DEFAULT_DEVICE);
    fprintf(stderr,"  -c  DEV    uart device node (df: %s)\n",
		DEFAULT_COMM_DEVICE);    
	fprintf(stderr,"  -a  ADDR   select i2c address (0 = spi, def: %d)\n",
		DEFAULT_I2C_ADDR);
	fprintf(stderr,"  -b  BAUD   select baudrate (df: %d)\n",
		DEFAULT_BAUDRATE);
	fprintf(stderr,"  -g  0xNN    set gpio port to value N\n");
}

int
main(int argc, char **argv)
{
	int spi_i2c_fd;
	char *spi_i2c_devname = DEFAULT_DEVICE;
	struct sc16is7xx *sc16is7xx;
	ssize_t txlvl, rxlvl;
	int i2c_addr = DEFAULT_I2C_ADDR;
	int i;
	int baudrate = DEFAULT_BAUDRATE;
	int gpio_out = -1;
    
    char *comm_devname = DEFAULT_COMM_DEVICE;
    
	while ((i = getopt(argc, argv, "d:c:a:b:g:h")) != -1) 
    {
		switch (i) 
        {
		case 'd':
			spi_i2c_devname = optarg;
			break;
        case 'c':
			comm_devname = optarg;
			break;    
		case 'a':
			i2c_addr = atoi(optarg);
			break;
		case 'b':
			baudrate = atoi(optarg);
			break;
		case 'g':
			gpio_out = strtoul(optarg, NULL, 0);
			break;
		case 'h':
			usage(argv[0]);
			exit(1);
			break;
		}
	}

	if ((spi_i2c_fd = open(spi_i2c_devname, O_RDWR|O_NOCTTY)) == -1) 
    {
		perror(spi_i2c_devname);
		exit(1);
	}

	sc16is7xx = sc16is7xx_new(spi_i2c_fd, i2c_addr, 0/*flags*/);
	if (!sc16is7xx) 
    {
		fprintf(stderr, "Could not create sc16is7xx instance.\n");
		exit(1);
	}

	if (sc16is7xx_set_baud(sc16is7xx, baudrate) == -1) 
    {
		perror("sc16is7xx_set_baud()");
		exit(1);
	}

	if (gpio_out != -1) 
    {
		fprintf(stderr, "setting GPIO to 0x%04x\n", gpio_out & 0xff);
		for (i=7; i>=0; i--)
			fprintf(stderr," D%d=%d", i, !!(gpio_out & (1<<i)));
		fprintf(stderr,"\n");
		if (sc16is7xx_gpio_out(sc16is7xx, 0xff, gpio_out & 0xff) == -1) 
        {
			perror("sc16is7xx_gpio_out");
			exit(1);
		}
	}

	//fprintf(stderr, "Baudrate is %d...\n\n", baudrate);

    uartfd = open_com_port(comm_devname); 
    
    int temp;
    if((temp = pthread_create(&ntid, NULL, thread, NULL))!= 0)  
    {  
        printf("can't create thread: %s\n", strerror(temp));  
        return 1;  
    } 
    
    unsigned char rer_rhr = 0x00;
    unsigned char reg_lsr = 0x00;

	/* main loop */
	while (1) 
    {
        // spi
		txlvl = sc16is7xx_get_txlvl(sc16is7xx);
		if (txlvl == -1) 
        {
			perror("sc16is7xx_get_txlvl()");
			exit(1);
		}

		/* is there something in the receive buffer? */
		rxlvl = sc16is7xx_get_rxlvl(sc16is7xx);
		if (rxlvl == -1) 
        {
			perror("sc16is7xx_get_rxlvl()");
			exit(1);
		}
        
        sc16is7xx_reg_rd(sc16is7xx, 0x05, &reg_lsr);
        if(reg_lsr & 0x01)
        {
            sc16is7xx_reg_rd(sc16is7xx, 0x00, &rer_rhr);
            sc16is7xx_write(sc16is7xx, &rer_rhr, 1);
            
            reg_lsr = 0x00;
        }
        
        if(success_count > 4)
        {
            printf("test success\n");
            exit(0);
        }
        else if(success_count == -1)
        {
            printf("test failed\n");
            exit(1);
        }
	} /* while(1) */

	return 0;
}

