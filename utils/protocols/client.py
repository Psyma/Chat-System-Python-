import asyncio

from concurrent.futures import ThreadPoolExecutor
from TCPClientProtocol import TCPClientProtocol
from UDPClientProtocol import UDPClientProtocol

class Client(object):
    def __init__(self, host, tcp_port, udp_port) -> None:
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.tcp_transport: asyncio.Transport = None
        self.udp_transport: asyncio.DatagramTransport = None

    def tcp_connection_made(self, transport: asyncio.Transport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname')
        self.tcp_transport = transport 
        self.tcp_transport.write(b'Hi Server!, Message from client via tcp')
        #print("Client tcp connection made {}".format(sockname))

    def tcp_data_received(self, data: bytes):
        print(data.decode())

    def udp_connection_made(self, transport: asyncio.DatagramTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname') 
        transport.sendto(b'Hi Server!, Message from client via udp', peername)
        #print("Client udp connection made {}".format(sockname))

    def udp_datagram_received(self, data: bytes, addr: tuple):
        print(data.decode()) 

    def start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.tcp_connection_made, self.tcp_data_received), self.host, self.tcp_port)
        server, _ = self.loop.run_until_complete(coro) 
        
        connect = self.loop.create_datagram_endpoint(lambda: UDPClientProtocol(self.udp_connection_made, self.udp_datagram_received), remote_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)

        try:
            self.loop.run_forever()
        except KeyboardInterrupt as e:
            self.loop.call_soon_threadsafe(self.loop.stop)

if __name__ == "__main__":
    client = Client('127.0.0.1', 9999, 6666)
    client.start()