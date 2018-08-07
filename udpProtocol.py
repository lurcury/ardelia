## UDP Protocol ##

import time
import gevent
from gevent.queue import Queue as Queue
import pickle
from p2p import Packet

class Protocol(gevent.Greenlet):
    'Handler of incoming and outgoing messages. Takes care of packaging packets and signature verification.'

    def __init__(self, peer, privwif, pubkey, num_workers):
        gevent.Greenlet.__init__(self)
        self.peer = peer
        self.node_info = dict(addr=self.peer.myAddr, ID=self.peer.myID)
        self.hello_received = False
        self.is_stopped = False
        self.rQ = Queue()
        self.sQ = Queue()
        self.num_workers = num_workers
        self.workers = list()
        # this node's own privkey and pubkey, not from peer!
        self.priv_wif = privwif
        self.pubkey = pubkey
    
    def stop(self):
        if not self.is_stopped:
            self.is_stopped = True
            try:
                for worker in self.workers:
                    try:
                        worker.kill()
                    except gevent.GreenletExit:
                        pass
                self.workers = None
            except:
                print('Failed to kill all workers.')
            finally:
                self.kill()

    def run(self):
        for i in range(self.num_workers):
            sw = gevent.spawn(self.send_worker)
            rw = gevent.spawn(self.recv_worker)
            self.workers.append(sw)
            self.workers.append(rw)

    def send_worker(self):
        while not self.is_stopped:
            raw = self.sQ.get()
            #print ("Sending *blah* to peer...")
            if raw['action'] == 0:   
                packet = Packet(ctrl="hello", node_info=self.node_info, pubkey=self.pubkey, data=raw['payload'])
                self.signsend(packet)
            elif raw['action'] == 1:
                self.hello_received = True
                packet = Packet(ctrl="confirm", node_info=self.node_info, pubkey=self.pubkey, data=raw['payload'])
                self.signsend(packet)
            elif raw['action'] == 2:
                packet = Packet(ctrl="disconnect", node_info=self.node_info, pubkey=self.pubkey, data=raw['payload'])
                self.signsend(packet)
            elif raw['action'] == 3:
                packet = Packet(ctrl="ping", node_info=self.node_info, pubkey=self.pubkey, data='ping')
                self.signsend(packet)
            elif raw['action'] == 4:
                packet = Packet(ctrl="pong", node_info=self.node_info, pubkey=self.pubkey, data='pong')
                self.signsend(packet)
            elif raw['action'] == 5:
                packet = Packet(ctrl="data", node_info=self.node_info, pubkey=self.pubkey, data=raw['payload'])
                self.signsend(packet, priority=False)
            else:
                print ("Unknown command!")

    def recv_worker(self):
        while not self.is_stopped:
            datagram = self.peer.inbox.get()
            packet = pickle.loads(datagram)
            assert isinstance(packet, Packet)
            try:
                packet.verify()
            except:
                print ("Uh oh. This is a problem.")
                msg = "Packet verification failed."
                self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))
            else:
                if packet.ctrl_code == "hello":
                    if self.hello_received:
                        msg = "Duplicate hello from peer!"
                        self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))
                    else:
                        # send confirm
                        self.sQ.put(dict(action=1, payload="Successfully received hello."))

                elif packet.ctrl_code == "confirm":
                    if not self.hello_received:
                        print ("Received confirm from ID: %s!" % str(packet.node['ID']))
                        self.hello_received = True
                        self.rQ.put(("checked"))
                    else:
                        msg = "confirm after handshaked"
                        self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))

                elif packet.ctrl_code == "disconnect":
                    print ("Received disconnect from ID: %s!" % str(packet.node['ID']))
                    self.rQ.put(("disconnect", dict(type="end_session",reason=packet.data)))

                elif packet.ctrl_code == "ping":
                    if self.hello_received:
                        print ("Received ping from ID: %s!" % str(packet.node['ID']))
                        self.sQ.put(dict(action=4))
                        self.rQ.put(("checked"))
                    else:
                        msg = "ping received before confirming connection"
                        self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))

                elif packet.ctrl_code == "pong":
                    print ("Received pong from ID: %s!" % str(packet.node['ID']))
                    self.rQ.put(("checked"))
                    print ("ping pong completed.")

                elif packet.ctrl_code == "data":
                    print ("Received data from ID: %s!" % str(packet.node['ID']))
                    if self.hello_received:
                        self.rQ.put(("data", dict(nodeID=packet.node['ID'],data=packet.data)))
                    else:
                        msg = "data received before confirming connection"
                        self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))

                else:
                    msg = "Unknown packet control code: %s" % packet.ctrl_code
                    self.rQ.put(("disconnect", dict(type="badpeer",reason=msg)))

    def signsend(self, packet, priority=True):
        packet.sign(self.priv_wif)
        packet = pickle.dumps(packet)
        if priority:
            self.peer.vipbox.put(packet)
        else:
            self.peer.outbox.put(packet)

        