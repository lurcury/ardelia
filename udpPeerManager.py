## UDP PeerManager ##

import random
import enum
import pickle
import gevent
from gevent.queue import Queue as Queue
from gevent.server import DatagramServer as Server
import crypto
from udpPeer import Peer
from p2p import Packet


class State(enum.Enum):
    STARTING = 'starting'
    STARTED = 'started'
    STOPPING = 'stopping'
    STOPPED = 'stopped'

def peer_die(peer):
    peer.stop()

class PeerManager(gevent.Greenlet):

    default_config = dict(p2p=dict(bootstrap_nodes=[],
                                   min_peers=1,
                                   max_peers=10,
                                   num_workers=1,
                                   num_queue=10,
                                   listen_port=30303,
                                   listen_host='0.0.0.0',
                                   timeout = 10.0,           # tbd
                                   pingtime = 5.0,
                                   discovery_delay = 0.1),  # tbd
                          node=dict(privkey=None, wif=None))

    def __init__(self, configs=None):
        print('Initializing peerManager....')
        gevent.Greenlet.__init__(self)
        self.configs = configs if configs else self.default_config
        self.address = (self.configs['p2p']['listen_host'], int(self.configs['p2p']['listen_port']))
        self.peers = []
        self.server = Server(self.address, handle=self._new_conn)
        self.configs['node']['pubkey'] = crypto.priv2pub(priv=self.configs['node']['privkey'], wif=self.configs['node']['wif'])
        self.state = State.STARTING
        self.status_book = dict()
        # recv_queues for the ten types of messages
        self.recv_queue = [Queue() for i in range(self.configs['p2p']['num_queue'])]

    # for server
    def _new_conn(self, data, address):
        if self.state is State.STARTED:
            try:
                node_info = self.check_hello(data, address)
            except:                             #TODO: implement class of errors
                print ("New connection failed!")
                raise
            else:
                disagree = self.approve_connection(node_info['ID'])
                peer = self.create_peer(node_info)
                if disagree:
                    peer.send_disconnect(disagree)
                else:
                    self.status_book[peer.peerID] = ['starting']
                    peer.send_confirm()
        else:
            print ("Incorrect state! ", self.state)

    # Other functions
    def start(self):
        print ("Starting peerManager...")
        gevent.Greenlet.start(self)
        self.server.start()
        self.state = State.STARTED
        self.bootstrap()
        #self.discovery()
        gevent.sleep(5)
        
    def bootstrap(self):
        print ("Bootstrapping to nodes...")
        if self.state is State.STARTED:
            for node in self.configs['p2p']['bootstrap_nodes']:
                addr, pID = node
                node_info = dict(ID=pID, addr=addr)
                try:
                    self.make_connection(node_info)
                except: 
                    print ("Connection to node: %s failed." % pID)          
    
    # TODO
    def discovery(self):
        pass

    def make_connection(self, node_info):
        disagree = self.approve_connection(node_info['ID'])
        if not disagree:
            peer = self.create_peer(node_info)
            self.status_book[peer.peerID] = ['starting']
            peer.send_hello()
            return True
        else:
            print("Reason: %s" % disagree)
            return False

    def broadcast(self, packet, num_peers=None, excluded=[]):
        valid_peers = [p for p in self.peers if p.peerID not in excluded]
        num_peers = num_peers if num_peers else len(valid_peers)
        for peer in random.sample(valid_peers, min(num_peers, len(valid_peers))):
            if self.state is State.STARTED:
                print("Sending broadcast to peer: %s" % peer.peerID)
                peer.send_packet(packet)

    def send(self, packet, peerID):
        if self.state is State.STARTED:
            peer = [p for p in self.peers if p.peerID==peerID]
            if peer:
                try:
                    assert len(peer) == 1, "Duplicate peer in peer list! "
                except AssertionError as e:
                    print (e)
                    return 
                print("Sending packet to specific peer: %s" % peer[0].peerID)
                peer[0].send_packet(packet)
            else:
                # TODO: use chord to find next peer
                print ("Target peer not in peer list!")
                return
        else:
            print ("Peermanager not started yet. Try again later.")
    
    def stop(self):
        print ("Stopping peerManager...")
        if self.state is not State.STOPPED:
            self.state = State.STOPPING
            self.server.stop()
            msg = "Peer stopping."
            for peer in self.peers:
                peer.send_disconnect(msg)
            gevent.Greenlet.kill(self)
            self.state = State.STOPPED

    # Helper functions
    def check_hello(self, data, address):
        packet = pickle.loads(data)
        assert isinstance(packet, Packet)
        try:
            packet.verify()
        except:
            print ("Uh oh. Problem in hello packet.")
        else:
            try:
                assert packet.ctrl_code == "hello", "This is not a hello packet! Received %s" %packet.ctrl_code
                assert packet.node['addr'] == address, "Address mismatch! Expected: %s; Got: %s" % (packet.node['addr'], address)
            except AssertionError as e:
                raise e
            else:
                node_info = packet.node
        return node_info

    def create_peer(self, node_info):
        peer = Peer(self, node_info)
        print("Peer created.")
        peer.link(peer_die)
        peer.start()
        self.peers.append(peer)
        return peer

    def approve_connection(self, peerID):
        msg = None
        if len(self.peers) >= self.configs['p2p']['max_peers']:
            msg = "Too many peers."
        if peerID in [p.peerID for p in self.peers]:
            msg = "Duplicate connection."
        return msg          

    def log(self, peerID, status, reasons=None):
        if status:
            self.status_book[peerID] = ['working']
        else:
            self.status_book[peerID] = ['disconnected', reasons]

    def check_status(self, peerID):
        return self.status_book[peerID]