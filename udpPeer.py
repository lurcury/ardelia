## UDP Peer ##
import time
import gevent
import json
from gevent.queue import Queue as Queue
from p2p import Packet
from udpProtocol import Protocol
import errno
import socket
import gevent.socket

class Peer(gevent.Greenlet):

    def __init__(self, peermanager, node_info):
        gevent.Greenlet.__init__(self)
        print ("Constructing basic configs")
        self.peermanager = peermanager
        self.peerID = node_info['ID']
        self.peerAddr = node_info['addr']
        self.ping_interval = self.peermanager.configs['p2p']['pingtime']        # timeout
        self.timeout = self.peermanager.configs['p2p']['timeout']
        try:
            self.socket = gevent.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(("", 0))
            self.socket.settimeout(self.peermanager.configs['p2p']['timeout'])      # timeout
        except gevent.socket.error as e:
            print('Socket creation error: %s' % e.strerror)
        
        self.myID = peermanager.configs['node']['ID']
        self.myAddr = (self.peermanager.configs['p2p']['listen_host'],self.socket.getsockname()[1])
        self.handler = Protocol(self,self.peermanager.configs['node']['wif'],self.peermanager.configs['node']['pubkey'],self.peermanager.configs['p2p']['num_workers'])
        self.handler.start()
        self.greenlets = dict()
        self.outbox = Queue()
        self.vipbox = Queue()
        self.inbox = Queue()
        self.is_stopped = False
        self.is_pinged = False
        self.last_contact = time.time()
        self.read_ready = gevent.event.Event()
        self.read_ready.set()

    def stop(self):
        if not self.is_stopped:
            print("Trying to stop peer.")
            self.is_stopped = True
            try:
                self.handler.stop()
                for process in self.greenlets.values():
                    try:
                        process.kill()
                    except gevent.GreenletExit:
                        pass
                self.greenlets = None              
            except:
                print('Failed to kill all processes.')
            finally:
                self.peermanager.peers.remove(self)
                self.kill()
    
    def run(self):
        print('Running main loop of peer ', self.peerID)
        self.handler.run()
        self.greenlets['sender'] = gevent.spawn(self.send_loop)
        self.greenlets['receiver'] = gevent.spawn(self.recv_loop)

        while not self.is_stopped:
            self.read_ready.wait()
            try:
                gevent.socket.wait_read(self.socket.fileno())
            except gevent.socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in (errno.EBADF):
                    self.report(("disconnect", dict(type="end_session",reason=e.__str__())))
                    self.stop()
                else:
                    raise e 
            
            try:
                message, addr = self.socket.recvfrom(4096)
                self.peerAddr = addr
            except gevent.socket.error as e:
                print('Network error: %s' %e.strerror)
                if e.errno in (errno.ENETDOWN, errno.ECONNRESET, errno.ETIMEDOUT,errno.EHOSTUNREACH, errno.ECONNABORTED):
                    self.report(("disconnect", dict(type="end_session",reason=e.__str__())))
                    self.stop()
                else:
                    raise e
            
            if message:
                self.last_contact = time.time()
                self.is_pinged = False
                self.inbox.put(message)

    def send_loop(self):
        while not self.is_stopped:
            elapsed = time.time() - self.last_contact
            
            if elapsed > self.timeout:
                self.send_disconnect('Ping pong timeout')
            elif elapsed > self.ping_interval and not self.is_pinged:
                print("time elapsed:", elapsed)
                self.is_pinged = True
                self.send_ping()
            else:
                if not self.vipbox.empty():
                    self.send(self.vipbox.get())
                if not self.outbox.empty():
                    self.send(self.outbox.get())
            gevent.sleep(0)
        
    def recv_loop(self):
        while not self.is_stopped:
            self.report(self.handler.rQ.get())

    def send(self, packet):
        if not packet:
            print("Missing packet!")
            return
        self.read_ready.clear()
        # use socket.wait_write() ??
        try:
            self.socket.sendto(packet, self.peerAddr)
        except gevent.socket.error as e:
            print("Error in send! ", e)
            self.report(("disconnect", dict(type="end_session",reason='send error')))
            self.stop()
        except gevent.socket.timeout as e:
            print("Timeout in send! ", e)
            self.report(("disconnect", dict(type="end_session",reason='send timeout')))
            self.stop()       
        self.read_ready.set()

    def send_hello(self):
        self.handler.sQ.put(dict(action=0, payload="Hello, requesting connection."))

    def send_confirm(self):
        self.handler.sQ.put(dict(action=1, payload="Successfully received hello."))

    def send_disconnect(self, msg):
        self.handler.sQ.put(dict(action=2, payload=msg))
        self.report(("disconnect", dict(type="end_session",reason=msg)))
        self.stop()

    def send_packet(self, packet):
        packet = json.dumps(packet)
        self.handler.sQ.put(dict(action=5,payload=packet))

    def send_ping(self):
        self.handler.sQ.put(dict(action=3))
    
    def report(self, rp):
        if rp[0] == "checked":
            self.peermanager.log(self.peerID, 1)
        if rp[0] == "disconnect":
            self.peermanager.log(self.peerID, 0, reasons=rp[1])
            self.stop()
        if rp[0] == "data":
            self.peermanager.log(self.peerID, 1)
            rp[1]['data'] = json.loads(rp[1]['data'])
            self.parse_data(rp[1])
            #self.peermanager.recv_queue.put(rp[1])
    
    def parse_data(self, data):
        method = int(data['data']['method'])
        #'status','transaction','new_block','new_block_hash','new_sign_block','get_block','get_block_hash','block','block_hash','sign_block'
        try:
            self.peermanager.recv_queue[method].put(data)
        except IndexError:
            print ("Illegal method index!")
        """
        if method == "status":
            self.peermanager.recv_queue['status'].put(data)
        elif method == "transactions":
            self.peermanager.recv_queue['transaction'].put(data)
        elif method == "getBlockHashes":
            self.peermanager.recv_queue['get_block_hash'].put(data)
        elif method == "blockHashes":
            self.peermanager.recv_queue['block_hash'].put(data)
        elif method == "getBlocks":
            self.peermanager.recv_queue['get_block'].put(data)
        elif method == "blocks":
            self.peermanager.recv_queue['block'].put(data)
        elif method == "newBlockHashes":
            self.peermanager.recv_queue['new_block_hash'].put(data)
        elif method == "newBlock":
            self.peermanager.recv_queue['new_block'].put(data)
        elif method == "signBlock":
            self.peermanager.recv_queue['sign_block'].put(data)
        elif method == "newSignBlock":
            self.peermanager.recv_queue['new_sign_block'].put(data)
        else:
            print("Message not recognized.")
        """