#!/usr/bin/env python3
import socket
import argparse
import threading
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


def server(start_port, end_port):
    """
    Start the server to listen on a range of ports.

    Args:
    - start_port (int): Starting port for the server.
    - end_port (int): Ending port for the server.
    """
    for port in range(start_port, end_port + 1):
        threading.Thread(target=handle_port, args=(port,)).start()


def handle_port(port):
    """
    Handle incoming connections on the specified port.

    Args:
    - port (int): Port to handle connections.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Set send buffer size to 4096
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen()

        logging.info("Server listening on port {}".format(port))

        while True:
            conn, addr = server_socket.accept()
            with conn:
                logging.info("Connected by {}.".format(addr))
                received_data = b''
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    received_data += data
                if received_data:
                    logging.info("Received raw data from {}.".format(addr))
                    conn.sendall(received_data)


def client(host, start_port, end_port, payload, start_time):
    """
    Start the client to connect to a range of server ports.

    Args:
    - host (str): Server host.
    - start_port (int): Starting port for the client.
    - end_port (int): Ending port for the client.
    - payload (str): Payload to send to the server.
    - done_event (threading.Event): Event to signal when the client is done.
    - start_time (datetime): Time until which the client should run.
    """
    threads = []
    for port in range(start_port, end_port + 1):
        thread = threading.Thread(target=send_payload,
                                  args=(host, port, payload, start_time))
        threads.append(thread)
        thread.start()

    # Wait for all client threads to finish
    for thread in threads:
        thread.join()

    fail_port = [x for x in results if "FAIL" in x]
    error_port = [x for x in results if "ERROR" in x]
    if not (fail_port or error_port):
        logging.info("TCP connections test pass!")
    else:
        if fail_port:
            for x in fail_port:
                logging.error("Fail on port {}.".format(x.split(":")[0]))
            raise RuntimeError("TCP payload test fail!")
        if error_port:
            for x in error_port:
                logging.error("Not able to connect on port {}."
                              .format(x.split(":")[0]))
            raise RuntimeError("TCP connection fail!")


def send_payload(host, port, payload, start_time):
    """
    Send a payload to the specified port and handle the server response.

    Args:
    - host (str): Server host.
    - port (int): Port to connect to.
    - payload (str): Payload to send to the server.
    - start_time (datetime): Time until which the client should run.
    """
    try:
        with socket.create_connection(
                (host, port), timeout=600) as client_socket:
            # Set send buffer size to 4096
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
            logging.info("Connect to port {}".format(port))
            while datetime.now() < start_time:
                time.sleep(1)
            logging.info("Sending payload to port {}.".format(port))
            count = 0
            # Sending payload for 30 sec after start sending.
            while datetime.now() < start_time + timedelta(seconds=30):
                client_socket.sendall(payload.encode())
                count = count+1
            # Shutdown send side by SHUT_WR, since socket.recv() won't recvie
            # 0 until connection timeout, error or shutdown.
            # ref: https://docs.python.org/3/howto/sockets.html
            client_socket.shutdown(socket.SHUT_WR)
            received_data = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                received_data += data
            logging.info("Server response from port {}.".format(port))
            if received_data == payload.encode() * count:
                results.append("{}:PASS".format(port))
            else:
                results.append("{}:FAIL".format(port))
    except socket.error as e:
        logging.error("{} on port {}".format(e, port))
        results.append("{}:ERROR".format(port))
    except Exception as e:
        logging.error("{}: An unexpected error occurred for port {}"
                      .format(e, port))
        results.append("{}:ERROR".format(port))


if __name__ == "__main__":
    """
    TCP Ping Test

    This script performs a TCP ping test between a server and multiple
    client ports.
    The server listens on a range of ports, and the clients connect to
    these ports to send a payload and receive a response from the server.

    Usage:
    - To run as a server: ./script.py server -p <star_port> -e <end_port>
    - To run as a client: ./script.py client -H <server_host> -p <start_port>
      -e <end_port> -P <payload_size>

    Arguments:
    - mode (str): Specify whether to run as a server or client.
    - host (str): Server host IP (client mode). This is mandatory arg.
    - port (int): Starting port for the server or server port for the client.
      Default is 1024.
    - payload (int): Payload size in KB for the client. Default is 64.
    - end_port (int): Ending port for the server. Default is 1223.

    Server Mode:
    - The server listens on a range of ports concurrently, handling
      incoming connections and send the received data back to client.

    Client Mode:
    - The client connects to a range of server ports,
      sending a payload and validating the received response.
      The script logs pass, fail, or error status for each port.
    """

    parser = argparse.ArgumentParser(
        description="Client-server with payload check on multiple ports")

    subparsers = parser.add_subparsers(dest="mode",
                                       help="Run as server or client")

    # Subparser for the server command
    server_parser = subparsers.add_parser("server", help="Run as server")
    server_parser.add_argument("-p", "--port",
                               type=int, default=1024,
                               help="Starting port for the server")
    server_parser.add_argument("-e", "--end-port", type=int, default=1223,
                               help="Ending port for the server")

    # Subparser for the client command
    client_parser = subparsers.add_parser("client", help="Run as client")
    client_parser.add_argument("-H", "--host", required=True,
                               help="Server host (client mode)")
    client_parser.add_argument("-p", "--port", type=int, default=1024,
                               help="Starting port for the client")
    client_parser.add_argument("-P", "--payload", type=int, default=64,
                               help="Payload size in KB (client mode)")
    client_parser.add_argument("-e", "--end-port", type=int, default=1223,
                               help="Ending port for the client")
    args = parser.parse_args()

    results = []
    # Ramp up time to wait until all ports are connected before
    # starting to send the payload.
    start_time = datetime.now() + timedelta(seconds=30)

    if args.mode == "server":
        server(args.port, args.end_port)
    elif args.mode == "client":
        payload = 'A' * (args.payload * 1024)
        client(args.host, args.port, args.end_port,
               payload, start_time)
