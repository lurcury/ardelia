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
            - receive: get packet by queue.get()

    Notes & TODO:
        - inbox, outbox queue --> decoding(extract packet) & encoding(use protocol?)
        - how to implement hello packet under UDP?
        - decide message size through connection, ideally 1024~4096, 4096 for now
        - when bootstrapping/discovering peermanager, use peer.send() to send connect_request
"""

import gevent

class Peer(gevent.Greenlet):

    def __init__(self, peermanager, connection, pubID):
        super(Peer,self).__init__()
        self.peermanager = peermanager
        self.connection = connection
        self.pubID = pubID
        self.is_stopped = False
        self.get_hello = False
        self.greenlets = dict()
        self.read_ready = gevent.event.Event()
        self.read_ready.set()
        self.protocol = P2PProtocol(self)
        self.protocol.start()
        self.outbox = gevent.queue.Queue()
        self.inbox = gevent.queue.Queue()
        # not sure about this one
        hello_packet = self.protocol.get_hello_packet()

    
    def stop(self):
        if not self.is_stopped:
            try:
                self.is_stopped = True
                for process in self.greenlets:
                    process.kill()
                    self.greenlets = None
                self.protocol.stop()
            except:
                print('Failed to kill all processes and protocol.')
            finally:
                self.peermanager.peers.remove(self)
                self.kill()
    
    def run(self):
        print('Running main loop of peer ', self.pubID)
        assert not self.connection.closed(), "Connection closed!"
        self.greenlets['sender'] = gevent.spawn(self.send_message)
        self.greenlets['receiver'] = gevent.spawn(self.get_message)

        while not self.is_stopped:
            self.read_ready.wait()
            try:
                gevent.socket.wait_read(self.connection.fileno())
            except gevent.socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in errno.EBADF:
                    self.stop()
                else:
                    raise e 
                    break
            try:
                message = self.connection.recv(4096)        # byte size tbd(1024, 2048, or 4096)
            except gevent,socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in (errno.ENETDOWN, errno.ECONNRESET, errno.ETIMEDOUT,errno.EHOSTUNREACH, errno.ECONNABORTED):
                    self.stop()
                else:
                    raise e 
                    break
            if message:
                
                #add message to inbox --> decode before adding?
                self.inbox.put(message)

    def send_message(self):
        'Main sending process'
        pass

    def get_message(self):
        'Main receiving process'
        pass

    def send(self, data):
        'Directly send message through connection'
        pass

    # how to implement this under UDP?
    def receive_hello(self):
        pass