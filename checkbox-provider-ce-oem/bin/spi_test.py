#!/usr/bin/env python

import spidev


def spi_bus_test():
    # Create an SPI device object
    spi = spidev.SpiDev()

    # Specify the SPI bus and device (chip-select) you want to use
    bus = 0  # SPI bus 0
    device = 0  # Chip-select 0

    try:
        # Open the SPI device
        spi.open(bus, device)

        # Configure SPI settings (mode, speed, etc.)
        spi.mode = 0b00  # SPI mode 0
        spi.max_speed_hz = 500000  # Clock speed in Hz
        spi.bits_per_word = 8  # Bits per word

        # Create test data (e.g., bytes to send)
        tx_data = [0x01, 0x02, 0x03, 0x04]

        # Transmit data and receive the response
        rx_data = spi.xfer2(tx_data)

        # Print the received data
        print("Received data:", rx_data)

    except Exception as e:
        print(f"SPI bus test failed: {e}")
    finally:
        # Close the SPI device
        spi.close()


if __name__ == "__main__":
    spi_bus_test()
