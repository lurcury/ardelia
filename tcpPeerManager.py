##  TCP  peermanager  ##
import time
import random
import socket
import pickle
import gevent
import gevent.queue
from gevent.server import StreamServer as Server
import gevent.socket #as socket
from gevent.socket import create_connection, timeout
import crypto
from tcpPeer import Peer
import p2p

ENCODING = 'utf-8'

def peer_die(peer):
    peer.stop()

class PeerManager(gevent.Greenlet):

    default_config = dict(p2p=dict(bootstrap_nodes=[],
                                   min_peers=1,
                                   max_peers=10,
                                   forever=False,
                                   listen_port=30303,
                                   listen_host='0.0.0.0',
                                   timeout = 5.0,           # tbd
                                   discovery_delay = 0.1),  # tbd
                          log_disconnects=False,
                          node=dict(privkey='',wif=''))

    def __init__(self, configs=None):
        print('Initializing peerManager....')
        #super().__init__()
        gevent.Greenlet.__init__(self)
        self.is_stopped = False
        self.configs = configs if configs else self.default_config
        self.peers = []
        self.address = (self.configs['p2p']['listen_host'], int(self.configs['p2p']['listen_port']))
        self.server = Server(self.address, handle=self._new_conn)
        # make sure privkey is given in config
        if not self.configs['node']['privkey']:
            #print("Creating private key!!")
            self.configs['node']['privkey'] = crypto.wif2priv(self.configs['node']['wif']) 
        self.configs['node']['id'] = crypto.priv2addr(self.configs['node']['privkey'])
        self.hello_packet = self.construct_hello()
        self.recv_queue = gevent.queue.Queue()
        # needs further investigation
        #self.upnp = None
        #self.errors = PeerErrors() if self.configs['log_disconnects'] else None
    
    def start(self):
        print('Starting peerManager...')
        #super().start()
        gevent.Greenlet.start(self)
        self.server.set_handle(self._new_conn)
        if self.configs['p2p']['forever']:
            self.server.serve_forever()
        else:
            self.server.start()
        
        if not self.server.started:
            print("server not started!")
            self.server.serve_forever()
        self.bootstrap(self.configs['p2p']['bootstrap_nodes'])
        gevent.sleep(5)
        #gevent.spawn_later(0.001, self.bootstrap, self.configs['p2p']['bootstrap_nodes'])   # delays tbd
        #gevent.spawn_later(1, self.discovery)                                               # delays tbd

    def stop(self):
        print('Stopping peerManager..')
        self.server.stop()
        for peer in self.peers:
            peer.stop()
        #super().kill()
        self.is_stopped = True
        gevent.Greenlet.kill(self)
    
    
    def _new_conn(self, conn, addr):
        print("received connection at peermanager")
        peer = self.start_peer(conn, addr)
        # Explicit join is required in gevent >= 1.1.
        # See: https://github.com/gevent/gevent/issues/594
        # and http://www.gevent.org/whatsnew_1_1.html#compatibility
        peer.join()
        '''
        try:
            pubID = self.recv_hello(data, addr)
        except AssertionError as e:
            print("Receive hello failed. ", e)
        
        if pubID not in [p.pubID for p in self.peers]:
            try:
                peer = self.connect(addr, pubID)
            except socket.error:
                print("Connection failed at peer address: %s" %addr)
            else:
                peer.join()
                self.approve_conn(peer)
                confirm_packet = p2p.Packet("confirm", dict(node=dict(address=peer.own_addr, pubID=self.configs['node']['id'])))
                peer.send(confirm_packet)
        '''  
            
        

    def approve_conn(self, peer):
        num_peers = len(self.peers)
        max_peers = self.configs['p2p']['max_peers']
        if num_peers > max_peers:
            print("Too many connections! Disconnecting from peer %s" %peer.pubID)
            pk = dict(node=dict(address=self.address, pubID=self.configs['node']['id']), reason="too many peers")
            disconnect_packet = p2p.Packet("disconnect", pk)
            peer.send(disconnect_packet)
            return False
            #peer.stop()
        '''if peer in [p for p in self.peers]:
            print("Already connected to this peer! Disconnecting....")
            pk = dict(node=dict(address=self.address, pubID=self.configs['node']['id']), reason="duplicate hello")
            disconnect_packet = p2p.Packet("disconnect", pk)
            peer.send(disconnect_packet)
            return False'''
        return True

    def confirm_conn(self, peer):
        'Return confirm packet to ensure successful connection.'
        confirm_packet = p2p.Packet("confirm", dict(node=dict(address=self.address, pubID=self.configs['node']['id'])))
        peer.send(confirm_packet)

    # TODO!!
    
    def discovery(self):
        gevent.sleep(self.configs['p2p']['discovery_delay'])     # yield to other processes
        while not self.is_stopped:
            try:
                num_peers = len(self.peers) # check if all peers are valid and working
                min_peers = self.configs['p2p']['min_peers']
                if num_peers < min_peers:
                    print('Min #peers: %i; Current #peers: %i' %(min_peers,num_peers))
                    # connect to random peers? 
                    # connect to nearest neighbors?
            except:
                print ("exception in discovery loop.")
        
        evt = gevent.event.Event()
        evt.wait()

    def bootstrap(self, bootstrap_nodes=[]):
        for node in bootstrap_nodes:
            addr, pubID = node      #undecided format. temp: node = (addr, pubID)
            print("Bootstrapping to node: %s" %(pubID))
            try:
                self.connect(addr, pubID)
            except socket.error:
                print('bootstrap failed at peer address: %s' %pubID)
                '''
                if not peer.connection.closed:
                    print("Sending hello packet to node: %s" %(pubID))
                    peer.send(self.hello_packet)
                '''
            #else:
            #    print("Connection closed somehow!")
            gevent.sleep(1.0)

    def connect(self, address, pubID):
        """
        gevent.socket.create_connection(address, timeout=Timeout, source_address=None)
        Connect to address (a 2-tuple (host, port)) and return the socket object.
        """
        print('Connecting to: %s' % pubID)
        print("addr: %s; port: %s" %address)
        connection = None
        #ip,port = address
        try:
            #connection = gevent.socket.socket(gevent.socket.AF_INET, gevent.socket.SOCK_DGRAM)
            #connection.settimeout(5.0)
            #connection.connect((ip, int(port)))
            #own_addr = connection.
            connection = create_connection(address, timeout=self.configs['p2p']['timeout'])
        except socket.timeout:
            #self.errors.add(address, 'connection timeout')
            print('Connection timeout at address: %s' % pubID)
            return False
        except socket.error as e:
            #self.errors.add(address, 'connection error')
            print('Connection error at address: %s' % pubID)
            print(e)
            #raise
            return False
        # successful connection
        if connection:
            #connection.sendall(pickle.dumps(self.hello_packet))     #--> move to start_peer (pass by udp socket)
            self.start_peer(connection, address, pubID)
            return True
            #return peer
        else: 
            print("socket connection is none!")
    
    def start_peer(self, connection, address, pubID=None):
        #pubID = crypto.pub2addr(pubkey)
        print('Starting new peer: %s' %pubID)
        peer = Peer(self, connection, address, pubID)
        #peer.create_UDP_socket(address)                        #--> create udp socket
        peer.link(peer_die)
        self.peers.append(peer)
        peer.start()
        peer.send(self.hello_packet)
        assert not connection.closed
        return peer

    # do we need this? yes, we do, and we also need a send() for a specific peer
    # change: use peermanager.broadcast() for broadcasts; use peer.send() for direct transports
    def broadcast(self, packet, num_peers=None, excluded=[]):
        print("broadcasting...")
        valid_peers = [p for p in self.peers if p not in excluded]
        num_peers = num_peers if num_peers else len(valid_peers)
        print("#peers to broadcast: %i" % min(num_peers, len(valid_peers)))
        for peer in random.sample(valid_peers, min(num_peers, len(valid_peers))):
            #peer.protocol.send(message)
            print("Sending broadcast to peer: %s" % peer.pubID)
            peer.send_packet(packet)
            peer.read_ready.wait()

    def send(self, packet, pubID):
        print("sending to specific peer: %s" % pubID)
        peer = [p for p in self.peers if p.pubID==pubID]
        assert len(peer) == 1, "too many peers"
        peer[0].send_packet(packet)
        peer[0].read_ready.wait()
    
    def recv_hello(self, packet, addr):
        'Check if hello packet is correct and return pubID to create connection.'
        #packet = p2p.decode(packet)
        packet = pickle.loads(packet)
        #packet = packet.decode(ENCODING)
        try:
            recv_addr = packet.data['node']['address']
        except KeyError:
            print("Missing sender address in hello packet!")
        try:
            recv_id = packet.data['node']['pubID']
        except KeyError:
            print("Missing sender public ID in hello packet!")

        assert packet.control_code == "connect", "Control code for hello packet incorrect!"
        #assert recv_addr == addr, "Address mismatch! Expected: %s .Received: %s" %(addr,recv_addr)
        print("Received hello from %s" %recv_id)
        return recv_id


    def construct_hello(self):
        'Construct hello packet. Format: [0,{addr:sender_addr, pubID:sender_pubID}]'
        packet = p2p.Packet("connect", dict(node=dict(address=self.address, pubID=self.configs['node']['id'])))
        return packet