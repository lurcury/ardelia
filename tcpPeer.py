##  TCP  peer  ##
"""
    Class Peer 
        - initialized by peerManager with socket connection
        - contains pubkey of connected peer
        - takes care of packet sending and receiving

    Data members:
        - peerManager
        - connection
        - pubkey
        - greenlet processes
        - outbox (send_queue with messages waiting to be sent)
        - inbox (recv_queue with messages waiting to be processed)
        - other configs

    Functions:
        - init: setup configurations
        - stop: kill greenlet processes
        - receive hello: check with manager to confirm successful peer connection
        - run: coordinate send() and receive() greenlets
            - send: send packet by queue.put()
            - receive: basic processing of packet & sendup by queue.put()
        - send: direct send through connection      --> hello packet, disconnect packet
        - send packet: add packet to queue          --> usual method

    Notes & TODO:
        - TCP + UDP connection for different packets
            - need new protocol -> 2 port connections?
            - regulate traffic and ensure delivery 
                - spam attacks / signature verification?
            - keep track of <state> in peer/peermanager
        -
        * inbox, outbox queue --> decoding(extract packet) & encoding(use protocol?)
        * how to implement hello packet under UDP?
        * decide message size through connection, ideally 1024~4096, 4096 for now
        * when bootstrapping/discovering peermanager, use peer.send() to send connect_request
"""

import gevent
import p2p
import errno
import pickle
import socket
import gevent.socket

ENCODING = 'utf-8'

class Peer(gevent.Greenlet):

    def __init__(self, peermanager, connection, address, pubID=None):
        #super(Peer,self).__init__()
        super().__init__()
        self.peermanager = peermanager
        self.connection = connection
        self.udp_sock = None
        self.pubID = pubID
        self.own_id = self.peermanager.configs['node']['id']
        self.own_addr = connection.getsockname()
        self.to_addr = address
        self.is_stopped = False
        #self.get_hello = False
        self.greenlets = dict()
        self.read_ready = gevent.event.Event()
        self.read_ready.set()
        #self.protocol = P2PProtocol(self)
        #self.protocol.start()
        self.outbox = gevent.queue.Queue()
        self.inbox = gevent.queue.Queue()
    
    def stop(self):
        if not self.is_stopped:
            print("Trying to stop peer.")
            self.is_stopped = True
            try:
                self.is_stopped = True
                for process in self.greenlets.values():
                    try:
                        process.kill()
                    except gevent.GreenletExit:
                        print("greenlet kill successful.")
                self.greenlets = None
                #self.protocol.stop()
            except:
                print('Failed to kill all processes.')
            finally:
                self.peermanager.peers.remove(self)
                self.kill()
    
    def create_UDP_socket(self, address):
        'Create a socket to take care of UDP transfers'
        if not self.udp_sock:
            self.udp_sock = gevent.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.to_addr = address
    
    
    def run(self):
        print('Running main loop of peer ', self.pubID)
        assert not self.connection.closed, "Connection closed!"
        self.greenlets['sender'] = gevent.spawn(self.send_message)
        self.greenlets['receiver'] = gevent.spawn(self.get_message)

    _run = run

    def send_message(self):
        'Main sending process'
        while not self.is_stopped:
            self.send(self.outbox.get())

    def get_message(self):
        'Main receiving process'
        while not self.is_stopped:
            if not self.inbox.empty():
                self.peermanager.recv_queue.put(self.inbox.get())
            
            self.read_ready.wait()
            try:
                gevent.socket.wait_read(self.connection.fileno())
            except gevent.socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in (errno.EBADF):
                    self.stop()
                else:
                    raise e 

            try:
                message = self.connection.recv(4096)        # byte size tbd(1024, 2048, or 4096)
            except gevent.socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in (errno.ENETDOWN, errno.ECONNRESET, errno.ETIMEDOUT,errno.EHOSTUNREACH, errno.ECONNABORTED):
                    self.stop()
                    #print(e)
                else:
                    raise e 

            if message:
                print("received message!")
                try:
                    control, data = self.parse(message)
                except AssertionError:
                    print("Message sent is not a valid packet!")
                else:
                    if control == "connect":
                        #print("Already connected to this peer! Disconnecting from peer %s" % data['node']['pubID'])
                        #print("received hello from peer!")
                        self.peermanager.approve_conn(self)
                        if not self.pubID:
                            self.pubID = data['node']['pubID']
                        self.to_addr = data['node']['address']
                        print("received hello from peer: %s, at address %s" % (self.pubID, self.to_addr))
                        #self.send_confirm()
                        #self.peermanager.confirm_conn(self)
                        #pk = dict(node=dict(address=self.address, pubID=self.pubID), reason="duplicate hello")
                        #disconnect_packet = p2p.Packet("disconnect", pk)
                        #self.send(disconnect_packet)
                        #self.stop()
                    elif control == "confirm":
                        print("received confirm packet!")
                        print("Checking connection and address...", (self.to_addr == data['node']['address']))
                        #self.connection.connect(data['node']['address'])
                        #self.to_addr = data['node']['address']
                    elif control == "disconnect":
                        print("Received disconnect from peer %s! Reason: %s" %(self.pubID, data['reason']))
                        self.stop()
                    #elif control_code == "ping"
                    #elif control_code == "pong"
                    # other legit controls: [block, transaction, precommit, commit]
                    elif control == "transaction":
                        assert data['transaction'] is not None, "Received empty transaction!"
                        print("Received transaction from %s" % data['node']['pubID'])
                        print(data['transaction'])
                        self.inbox.put(data)
                        #self.send_packet(message)
                    else:
                        self.inbox.put(message)

    def send_packet(self,packet=None):
        'Put packet into queue to be sent'
        if not packet:
            print("Missing packet!")
            return
        print("sending packet...")
        self.read_ready.clear()
        if self.connection.closed:
            print("Connection dead!")
            return
        else:
            self.outbox.put(packet)
        self.read_ready.set()


    def send(self, packet=None):
        'Directly send packet through connection'
        if not packet:
            print("Missing packet!")
            return
        self.read_ready.clear()
        if self.connection.closed:
            print("Connection dead!")
        try:
            packet = pickle.dumps(packet)
            #packet = packet.encode(ENCODING)
            if not self.connection.closed:
                self.connection.sendall(packet)
        except gevent.socket.error as e:
            print("Error in send! ", e)
            self.stop()
        except gevent.socket.timeout as e:
            print("Timeout in send! ", e)
            self.stop()
        self.read_ready.set()

    def parse(self, message):
        packet = pickle.loads(message)
        #packet = message.decode(ENCODING)
        assert isinstance(packet,p2p.Packet)
        return packet.control_code, packet.data
    
    def send_hello(self, serverid):
        'Construct hello packet and send. Format: ["connect",{addr:sender_addr, pubID:sender_pubID}]'
        packet = p2p.Packet("connect", dict(node=dict(address=self.own_addr, pubID=serverid)))
        self.send(packet)
        #return packet
    
    def send_confirm(self):
        'Return confirm packet to ensure successful connection.'
        confirm_packet = p2p.Packet("confirm", dict(node=dict(address=self.own_addr, pubID=self.own_id)))
        self.send(confirm_packet)

    def send_disconnect(self):
        'Construct disconnect packet and send. Format: ["disconnect",{addr:sender_addr, pubID:sender_pubID}]'
        packet = p2p.Packet("disconnect", dict(node=dict(address=self.own_addr, pubID=self.own_id),reason='stopping peer!'))
        self.send(packet)