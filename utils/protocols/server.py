import asyncio 

from concurrent.futures import ThreadPoolExecutor
from TCPServerProtocol import TCPServerProtocol
from UDPServerProtocol import UDPServerProtocol

class Server(object):
    def __init__(self, host, tcp_port, udp_port) -> None:
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.udp_peername: tuple = None
        self.tcp_transport: asyncio.BaseTransport = None
        self.udp_transport: asyncio.DatagramTransport = None

    def tcp_connection_made(self, transport: asyncio.BaseTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname')
        self.tcp_transport = transport 
        self.tcp_transport.write(b'Hi Client!, Message from server via tcp')
        #print("Server tcp connection made {}".format(peername))

    def tcp_data_received(self, data: bytes):
        print(data.decode())

    def tcp_connection_lost(self, transport: asyncio.BaseTransport):
        print("Connection lost")

    def udp_connection_made(self, transport: asyncio.DatagramTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname') 
        self.udp_peername = peername
        self.udp_transport = transport 
        
    def udp_datagram_received(self, data: bytes, addr: tuple):
        print(data.decode())
        self.udp_transport.sendto(b'Hi Client!, Message from server via udp', addr)

    def start(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_server(lambda: TCPServerProtocol(self.tcp_connection_made, self.tcp_data_received, self.tcp_connection_lost), self.host, self.tcp_port)
        server = self.loop.run_until_complete(coro)

        connect = self.loop.create_datagram_endpoint(lambda: UDPServerProtocol(self.udp_connection_made, self.udp_datagram_received), local_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)
        
        try:
            self.loop.run_forever()
        except KeyboardInterrupt as e:
            self.loop.call_soon_threadsafe(self.loop.stop)



if __name__ == "__main__": 
    server = Server('127.0.0.1', 9999, 6666)
    server.start()

       