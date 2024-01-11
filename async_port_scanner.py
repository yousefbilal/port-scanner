import asyncio
import socket
import sys
from rich import print as pr
from typing import Iterable
import argparse
from time import time

MAX_SOCKETS = 100
TIMEOUT = 0.5

def filter_ports(ports: Iterable[int]):
    return filter(lambda port: port < 65536, ports)

async def scan_port(host:str, port_number:int):
    try:
        # print('connecting to', port_number)
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port_number), TIMEOUT)
        writer.close()
        pr(f'{host} is listening on port [green]{port_number}')
    except (ConnectionRefusedError, TimeoutError):
        pass
    except Exception as e:
        print(e)
        # sys.exit(1)


async def scan_ports(host:str, ports:Iterable[int]):
    it = iter(ports)
    end = False
    while True:
        batch = []
        count = 0
        while count < MAX_SOCKETS:
            try:
                batch.append(next(it))
                count+=1
            except StopIteration:
                end = True
                break
        start = time()
        
        await asyncio.gather(*(scan_port(host, port) for port in batch))
        print(time() - start)
        if end: return
        
    
parser = argparse.ArgumentParser()

parser.add_argument(
    'host',
    help='the IPv4 address or DNS name of the target device',
)

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument(
    '-p', '--ports',
    nargs='*',
    type=int,
    help='port numbers to scan'
)
group.add_argument(
    '-a', '--all',
    help='scan all port numbers 1->65535',
    action='store_true'
)

group.add_argument(
    '-r', '--range',
    help='scan all port numbers in range',
    nargs=2,
    type=int
)

parser.add_argument(
    '-t', '--timeout',
    help=f'set the timeouts of socket connections in seconds, default is {TIMEOUT} sec',
    type=float,
    required=False,
)

parser.add_argument(
    '-s', '--sockets',
    help='sets the maximum number of concurrently connected sockets, default is {MAX_SOCKETS}',
    type=int,
    required=False
)

args = parser.parse_args()

MAX_SOCKETS = args.sockets or MAX_SOCKETS
TIMEOUT = args.timeout or TIMEOUT
try:
    ip_addr = socket.getaddrinfo(args.host, None)[0][-1][0]
except socket.gaierror:
    pr('[red]failed to get host address info, make sure that its a correct IP address or a domain name')
    sys.exit(1)

if args.all:
    asyncio.run(scan_ports(ip_addr, range(1, 2**16)))
elif args.ports:
    ports = filter_ports(args.ports)
    asyncio.run(scan_ports(ip_addr, ports))
elif args.range:
    ports = filter_ports(range(args.range[0], args.range[1] + 1))
    asyncio.run(scan_ports(ip_addr, ports))
