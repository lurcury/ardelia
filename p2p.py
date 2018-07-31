"""
    Implementation of p2p protocol.
    UDP does not require ping/pong interactions.
    For now: only do hello and disconnect
    FIGURE OUT: get_hello_packet()
"""

class Packet():
    """
    Class for packets to be sent over network. 
    Supports encoding and decoding of packets.
    packet format: [ctrl, **kwargs] where **kwargs can be {node={address,pubID}, block={}, trans={}, commit={}, ...}
    """
    def __init__(self, ctrl=None, data={}):
        self.control_code = ctrl
        self.data = data
    