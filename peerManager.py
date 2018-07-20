"""
    Class PeerManager
        - 1 for each node, bound to address(runs server) and protocol
        - manages list of peers and handles connection errors
        - uses kademlia to discover new nodes

    Data members:
        - list of peers
        - address
        - private key
        - server
        - errors from peers
        - other configs(max, min number of peers allowed, timeout, delays...)

    Functions:
        - init: setup configurations, initialize instances
        - start: bootstrap to nodes, start server, run discovery loop(?)
        - stop: stop server and peers
        - connect: create socket connections -> create peers and add to list
        - on receive hello: check if connect request is legal
        - broadcast: //not sure what this is about

    Notes & TODO:
        - use sockets or ssl?
        - decide on delays and timeout limitations
        * initialize with private key, format= bytes/wif ? --> need to keep identity() in peerManager?
            * no need for all keys --> only keep privkey and id for now
        * pubkey or pubID? decide format of bootstrap_nodes
            * (addr, pubID) for now
        - in discovery(), connect to random peers, nearest neighbors, or other?
        - discovery!! 
"""
import time
import random
import socket
import gevent
from gevent.server import DatagramServer as Server
from gevent.socket import create_connection, timeout
import .crypto

ENCODING = 'utf-8'

def peer_die(peer):
    peer.stop()

class PeerManager(gevent.Greenlet):

    default_config = dict(p2p=dict(bootstrap_nodes=[],
                                   min_peers=5,
                                   max_peers=10,
                                   listen_port=30303,
                                   listen_host='0.0.0.0',
                                   timeout = 1.0,           # tbd
                                   discovery_delay = 0.1),  # tbd
                          log_disconnects=False,
                          node=dict(privkey=''))

    def __init__(self, configs=None):
        print('Initializing peerManager....')
        super(PeerManager,self).__init__()
        self.is_stopped = False
        self.configs = configs if configs else self.default_config
        self.peers = []
        self.address = (self.configs['p2p']['listen_host'], self.configs['p2p']['listen_port'])
        self.server = Server(self.address, handle=self._new_conn)
        # make sure privkey is given in config
        self.configs['node']['id'] = crypto.priv2addr(self.configs['node']['privkey'])
        self.hello_packet = self.construct_hello()
        # needs further investigation
        self.upnp = None
        self.errors = PeerErrors() if self.configs['log_disconnects'] else None
    
    def start(self):
        print('Starting peerManager...')
        super(PeerManager,self).start()
        self.server.set_handle(self._new_conn)
        self.server.start()
        gevent.spawn_later(0.001, self.bootstrap, self.configs['p2p']['bootstrap_nodes'])   # delays tbd
        gevent.spawn_later(1, self.discovery)                                               # delays tbd

    def stop(self):
        print('Stopping peerManager..')
        self.server.stop()
        for peer in self.peers:
            peer.stop()
        super(PeerManager,self).stop()

    def _new_conn(self, data, addr):
        try:
            pubID = self.recv_hello(data, addr)
        except AssertionError as e:
            print("Receive hello failed. ", e)
        
        try:
            peer = self.connect(addr, pubID)
        except socket.error:
            print("Connection failed at peer address: %s", %addr)
        else:
            peer.join()
        
        self.approve_conn(peer)

    def approve_conn(self, peer):
        num_peers = len(self.peers)
        max_peers = self.configs['p2p']['max_peers']
        if num_peers > max_peers:
            print("Too many connections! Disconnecting from peer %s" %peer.pubID)
            disconnect_packet = p2p.Packet("disconnect", dict(pubID=self.configs['node']['id'], reason="too many peers"))
            peer.send(disconnect_packet)
            #peer.stop()
        

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

    def bootstrap(self, bootstrap_nodes=[]):
        for node in bootstrap_nodes:
            addr, pubID = node      #undecided format. temp: node = (addr, pubID)
            try:
                peer = self.connect(addr, pubID)
            except socket.error:
                print('bootstrap failed at peer address: %s', %addr)
            if not peer.connection.closed:
                peer.send(self.hello_packet)

    def connect(self, address, pubID):
        """
        gevent.socket.create_connection(address, timeout=Timeout, source_address=None)
        Connect to address (a 2-tuple (host, port)) and return the socket object.
        """
        print('Connecting to: %s', %address)
        try:
            connection = create_connection(address, timeout=self.configs['p2p']['timeout'], source_address=self.address)
        except socket.timeout:
            #self.errors.add(address, 'connection timeout')
            print('Connection timeout at address: %s', %address)
            return False
        except socket.error as e:
            #self.errors.add(address, 'connection error')
            print('Connection error at address: %s', %address)
            print(e)
            return False
        # successful connection
        peer = self.start_peer(connection, address, pubID)
        return peer
    
    def start_peer(self, connection, address, pubID):
        #pubID = crypto.pub2addr(pubkey)
        print('Starting new peer: %s', %pubID)
        peer = Peer(self, connection, address, pubID)
        peer.link(peer_die)
        self.peers.append(peer)
        peer.start()
        assert not connection.closed
        return peer

    # do we need this? yes, we do, and we also need a send() for a specific peer
    # change: use peermanager.broadcast() for broadcasts; use peer.send() for direct transports
    def broadcast(self, packet, num_peers=None, excluded=[]):
        valid_peers = [p for p in self.peers if p not in excluded]
        num_peers = num_peers if num_peers else len(valid_peers)
        for peer in random.sample(valid_peers, min(num_peers, len(valid_peers))):
            #peer.protocol.send(message)
            peer.send(packet)
            peer.safe_to_read.wait()

    def recv_hello(self, packet, addr):
        'Check if hello packet is correct and return pubID to create connection.'
        #packet = p2p.decode(packet)
        packet = packet.decode(ENCODING)
        try:
            recv_addr = packet.data['addr']
        except KeyError:
            print("Missing sender address in hello packet!")
        try:
            recv_id = packet.data['pubID']
        except KeyError:
            print("Missing sender public ID in hello packet!")

        assert packet.control_code == "hello", "Control code for hello packet incorrect!"
        assert recv_addr == addr, "Address mismatch! Expected: %s .Received: %s" %(addr,recv_addr)
        
        return recv_id


    def construct_hello(self):
        'Construct hello packet. Format: [0,{addr:sender_addr, pubID:sender_pubID}]'
        packet = p2p.Packet("connect", dict(addr=self.address, pubID=self.configs['node']['id']))
        return packet
