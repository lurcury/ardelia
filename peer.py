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

    Notes & TODO:
        * inbox, outbox queue --> decoding(extract packet) & encoding(use protocol?)
        * how to implement hello packet under UDP?
        - decide message size through connection, ideally 1024~4096, 4096 for now
        * when bootstrapping/discovering peermanager, use peer.send() to send connect_request
        - remove self.protocol if not needed
"""

import gevent
import p2p
import errno

ENCODING = 'utf-8'

class Peer(gevent.Greenlet):

    def __init__(self, peermanager, connection, pubID):
        #super(Peer,self).__init__()
        super().__init__()
        self.peermanager = peermanager
        self.connection = connection
        self.pubID = pubID
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
            try:
                self.is_stopped = True
                for process in self.greenlets.values():
                    process.kill()
                    self.greenlets = None
                #self.protocol.stop()
            except:
                print('Failed to kill all processes.')
            finally:
                self.peermanager.peers.remove(self)
                self.kill()
    
    def run(self):
        print('Running main loop of peer ', self.pubID)
        assert not self.connection.closed(), "Connection closed!"
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
                else:
                    raise e 

            if message:
                try:
                    control, data = self.parse(message)
                except AssertionError:
                    print("Message sent is not a valid packet!")
                else:
                    if control == "connect":
                        print("Already connected to this peer! Disconnecting from peer %s" % data['node']['pubID'])
                        pk = dict(node=dict(address=self.address, pubID=self.pubID), reason="duplicate hello")
                        disconnect_packet = p2p.Packet("disconnect", pk)
                        self.send(disconnect_packet)
                        self.stop()
                    elif control == "disconnect":
                        print("Received disconnect! Reason: ", data['reason'])
                        self.stop()
                    #elif control_code == "ping"
                    #elif control_code == "pong"
                    # other legit controls: [block, transaction, precommit, commit]
                    elif control == "transaction":
                        assert data['transaction'] is not None, "Received empty transaction!"
                        print("Received transaction from %s" % data['node']['pubID'])
                        print(data['transaction'])
                    else:
                        self.inbox.put(message)

    def send(self, packet=None):
        'Directly send packet through connection'
        if not packet:
            print("Missing packet!")
            return
        self.read_ready.clear()
        try:
            packet = packet.encode(ENCODING)
            self.connection.sendall(packet)
        except gevent.socket.error as e:
            print("Error in send! ", e)
            self.stop()
        except gevent.socket.timeout as e:
            print("Timeout in send! ", e)
            self.stop()
        self.read_ready.set()

    def parse(self, message):
        packet = message.decode(ENCODING)
        assert isinstance(packet,p2p.Packet)
        return packet.control_code, packet.data
