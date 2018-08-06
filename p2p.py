import time
import crypto
import pickle
    
class Packet():

    def __init__(self, ctrl, node_info, pubkey, data=None):
        self.ctrl_code = ctrl
        self.node = node_info
        self.pubkey = pubkey
        self.signature = None
        self.data = data
    
    def sign(self, privkey):
        self.signature = crypto.signdata(wif=privkey, data=self.data)

    def verify(self):
        #print ("Verifying... timed")
        #s_t = time.time()
        try:
            assert self.ctrl_code, "Missing control code!"
            assert self.node, "Missing node info!"
            assert self.pubkey, "Missing pubkey!"
            assert self.signature, "Missing signature!"
            assert self.data, "Missing data!"
        except AssertionError as e:
            print ("Packet incomplete.", e)
            return False

        try:
            crypto.verifydata(pub=self.pubkey, sigdata=self.signature, origdata=self.data)
        except:
            print ("Signature verification failed.")
            return False
        try:
            addr = crypto.pub2addr(self.pubkey)
            assert addr == self.node['ID'], "Pubkey from malicious party."
        except AssertionError as e:
            print ("Address mismatch! ", e)
            return False
        #print ("Verified, time: %f" % (time.time()-s_t))

if __name__ == "__main__":
    priv_wif = '5JsyQainyFU5CXJsGcdpRArcggbHTUbfmcqXcTUfU62v56VK5La'
    pubkey = crypto.priv2pub(wif=priv_wif)
    addr = crypto.pub2addr(pubkey)
    node_info = dict(ID=addr, addr=('127.0.0.1',30303))
    pkt = dict(nodeID=addr, data='test data')
    packet = Packet(ctrl="data", node_info=node_info, pubkey=pubkey, data=pkt["data"])
    # sign and pack
    packet.sign(priv_wif)
    packet = pickle.dumps(packet)
    # unpack and verify
    packet = pickle.loads(packet)
    try:
        packet.verify()
        print ("Packet verification success.")
    except:
        print ("Packet verification failed.")