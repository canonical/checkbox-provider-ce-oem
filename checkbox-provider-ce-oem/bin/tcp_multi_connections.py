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


class PortOutputer():
    def __init__(self, port,
                 message="",
                 list_status={}):
        self.port = port
        self.message = message
        self.list_status = list_status
        self._status = None
        self._total_period = None
        self._avg_time_period = None
        self._max_time_period = None
        self._min_time_period = None

    @property
    def status(self):
        if not self.list_status:
            return "ERROR"
        else:
            for check in self.list_status.values():
                if check['status'] is False:
                    self.message = "Received payload incorrect!"
                    return "FAIL"
            self.message = "Received payload correct!"
            return "PASS"

    @property
    def total_period(self):
        if not self.list_status:
            return self._total_period
        else:
            total_value = timedelta()
            for value in self.list_status.values():
                total_value += value.get('time')
            return total_value

    @property
    def avg_time_period(self):
        if not self.list_status:
            return self._avg_time_period
        else:
            sum_value = timedelta()
            for value in self.list_status.values():
                sum_value += value.get('time')
            return (sum_value / len(self.list_status))

    @property
    def max_time_period(self):
        if not self.list_status:
            return self._max_time_period
        else:
            max_value = timedelta()
            for value in self.list_status.values():
                current_value = value.get('time')
                max_value = max(max_value, current_value)
            return max_value

    @property
    def min_time_period(self):
        if not self.list_status:
            return self._min_time_period
        else:
            min_value = None
            for value in self.list_status.values():
                current_value = value.get('time')
                if min_value is None:
                    min_value = current_value
                else:
                    min_value = min(min_value, current_value)
            return min_value

    def generate_result(self):
        return {
            'port': self.port,
            'status': self.status,
            'message': self.message,
            'list_status': self.list_status,
            'total_period': self.total_period,
            'avg_period': self.avg_time_period,
            'max_period': self.max_time_period,
            'min_period': self.min_time_period,
        }


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
    server = ("0.0.0.0", port)
    try:
        with socket.create_server(server) as server_socket:
            # Set send buffer size to 4096
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.listen()

            logging.info("Server listening on port {}".format(port))

            while True:
                try:
                    conn, addr = server_socket.accept()
                    with conn:
                        logging.info("Connected by {}.".format(addr))
                        while True:
                            data = conn.recv(4096)
                            if data:
                                conn.sendall(data)
                            else:
                                break
                except Exception as e:
                    logging.error("Error handling connection: {}".
                                  format(str(e)))
    except Exception as e:
        logging.error("{}: An unexpected error occurred for port {}"
                      .format(str(e), port))


def client(host, start_port, end_port, payload, start_time, results):
    """
    Start the client to connect to a range of server ports.

    Args:
    - host (str): Server host.
    - start_port (int): Starting port for the client.
    - end_port (int): Ending port for the client.
    - payload (str): Payload to send to the server.
    - done_event (threading.Event): Event to single when the client is done.
    - start_time (datetime): Time until which the client should run.
    """
    global global_results
    time = datetime.now()
    threads = []
    for port in range(start_port, end_port + 1):
        thread = threading.Thread(target=send_payload,
                                  args=(host,
                                        port,
                                        payload,
                                        start_time,
                                        results))
        threads.append(thread)
        thread.start()

    # Wait for all client threads to finish
    for thread in threads:
        thread.join()
    final = 0
    for x in results:
        if ("FAIL") in x['status']:
            final = 1
            logging.error("Fail on port {}.\n"
                          "{}\n"
                          "Detail:\n{}"
                          .format(x['port'],
                                  x['message'],
                                  "\n".join("{}: period: {} status: {}"
                                            .format(key,
                                                    value['time'],
                                                    value['status']) for key,
                                            value in x['list_status'].items()))
                          )
        elif ("ERROR") in x['status']:
            final = 1
            logging.error("Not able to connect on port {}."
                          "{}"
                          .format(x['port'],
                                  x['message']))
    if final:
        raise RuntimeError("TCP payload test fail!")
    else:
        logging.info("Run TCP multi-connections test in {}"
                     .format(datetime.now() - time))


def send_payload(host, port, payload, start_time, results):
    """
    Send a payload to the specified port and handle the server response.

    Args:
    - host (str): Server host.
    - port (int): Port to connect to.
    - payload (str): Payload to send to the server.
    - start_time (datetime): Time until which the client should run.
    """
    port_result = PortOutputer(port=port)
    # Retry connect to server port for 5 times.
    for _ in range(5):
        try:
            server_host = (host, port)
            with socket.create_connection(server_host) as client_socket:
                # Set send buffer size to 4096
                client_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_SNDBUF, 4096)
                logging.info("Connect to port {}".format(port))
                # Sleep until start time)
                start_time = start_time - datetime.now()
                time.sleep(start_time.total_seconds())
                logging.info("Sending payload to port {}.".format(port))
                # Sending payload for 10 times
                status_all = {}
                for x in range(10):
                    single_start = datetime.now()
                    client_socket.sendall(payload.encode())
                    received_data = ""
                    while len(received_data) < len(payload):
                        # set socket time out for 30 seconds,
                        # in case recv hang.
                        client_socket.settimeout(30)
                        try:
                            data = client_socket.recv(4096)
                            if not data:
                                break
                            received_data += data.decode()
                        except TimeoutError:
                            break
                    single_end = datetime.now() - single_start
                    if received_data != payload:
                        status_all[x] = {'time': single_end,
                                         'status': False}
                    else:
                        status_all[x] = {'time': single_end,
                                         'status': True}
                logging.info("Received payload from {}.".
                             format(server_host))
                port_result.port = port
                port_result.list_status = status_all
                client_socket.close()
                break
        except socket.error as e:
            logging.error("{} on {}".format(e, port))
            port_result.message = str(e)
            port_result.port = port
        except Exception as e:
            logging.error("{} on {}".format(e, port))
            port_result.message = str(e)
            port_result.port = port
        time.sleep(3)
    results.append(port_result.generate_result())
    return results


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
    start_time = datetime.now() + timedelta(seconds=20)

    if args.mode == "server":
        server(args.port, args.end_port)
    elif args.mode == "client":
        payload = 'A' * (args.payload * 1024)
        client(args.host, args.port, args.end_port,
               payload, start_time, results)
