# entire node #

import gevent
from udpPeerManager import PeerManager, State
import crypto

pm_configs = {
    'node' : {'privkey':None,'wif':None},
    'p2p' : {
        'bootstrap_nodes' : [],
        'min_peers':1,
        'max_peers':10,
        'num_workers':1,
        'num_queue':10,
        'listen_port':'',
        'listen_host':'127.0.0.1',
        'timeout':15.0,
        'pingtime':7.0,
        'discovery_delay':0.1
    }
}

class Node:
    def __init__(self, pm_configs, tp):
        self.stopped = True
        self.priv_wif = pm_configs['node']['wif']
        pm_configs['node']['ID'] = crypto.priv2addr(priv=pm_configs['node']['privkey'], wif=pm_configs['node']['wif'])
        self.nodeID = pm_configs['node']['ID']
        self.pm = PeerManager(pm_configs)
        #self.db = Database()
        self.key = None
        self.mgrs = dict(stat=statusMgr(self),db=dbMgr(self),consensus=consensusMgr(self))

        self.test_peer = tp # give testing pubID


    def stop(self):
        if not self.stopped:
            self.stopped = True
            for mgr in self.mgrs.values():
                try:
                    mgr.stop()
                except gevent.GreenletExit:
                    pass
            self.mgrs = None
            self.pm.stop() 

    def start(self):
        print("Running main loop of node.")
        self.stopped = False
        self.pm.start()
        for mgr in self.mgrs.values():
            mgr.start()
        self.run() 
        try:
            gevent.joinall([self.pm, self.mgrs['stat'], self.mgrs['db'], self.mgrs['consensus']])  
        except KeyboardInterrupt:
            self.stop()
        
    def run(self):
        print("Running!!!!!")
        self.test1()

    def test1(self):
        #msg_2 = {"method":"02", "hash" : "Test starting!", "maxBlock": "0"}
        #self.pm.send(msg_2, self.test_peer)
        msg_10 = {"method":"10", "blocks":{"hash":"testing consensus!"}}
        self.mgrs['consensus'].publishBlock(msg_10)


class statusMgr(gevent.Greenlet):
    def __init__(self,node):
        gevent.Greenlet.__init__(self)
        self.pm = node.pm
        #self.status = None # to be modified
        self.status = {"method":"00","ver":"sue", "id":"","genesisHash":"0","blockNumber":"0"}
        self.status['id'] = node.nodeID
        self.is_stopped = False
    
    def stop(self):
        if not self.is_stopped:
            self.is_stopped = True
            self.kill()

    def run(self):
        # initial broadcast of status to receive updates from neighbor
        print("Sending initial status block...")
        self.pm.broadcast(self.status)
        while not self.is_stopped and self.pm.state is State.STARTED:
            if not self.pm.recv_queue[0].empty():
                new_stat = self.pm.recv_queue[0].get()
                print("Received status block!")
                print("Version: %s\nBlock num: %s\n" %(new_stat['data']['ver'], new_stat['data']['blockNumber']))
                # TODO: update own status and broadcast
                stat = {"method":"02", "hash" : "Test starting!", "maxBlock": "0"}
                self.pm.broadcast(stat)
            gevent.sleep()    
        


class dbMgr(gevent.Greenlet):
    def __init__(self, node):
        gevent.Greenlet.__init__(self)
        #self.db = node.db
        self.pm = node.pm
        self.is_stopped = False

    def stop(self):
        print("Stopping dbMgr......")
        if not self.is_stopped:
            self.is_stopped = True
            self.kill()

    def run(self):
        while not self.is_stopped and self.pm.state is State.STARTED:
            # getBlockHash
            if not self.pm.recv_queue[2].empty():
                message = self.pm.recv_queue[2].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 02, return 03")
                print("Hash: %s\nMax Block: %s\n" %(request['hash'], request['maxBlock']))
                result = {"method": "03", "hash": ["this","is","test"]} #self.getBlockHashes(int(request['maxBlocks']))
                self.pm.send(result, nodeID)
            
            # ReturnBlockHash
            if not self.pm.recv_queue[3].empty():
                message = self.pm.recv_queue[3].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 03, return 05")
                print("Hash: %s\n" %(request['hash']))
                # save block hash to db and request block
                result = {"method": "05", "hash": request['hash']}
                self.pm.send(result, nodeID)
            
            # getBlock
            if not self.pm.recv_queue[5].empty():
                message = self.pm.recv_queue[5].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 05, return 06")
                print("Hash: %s\n" %(request['hash']))
                result = {"method": "06", "blocks": [{"a":"aa","b":"bb","c":"cc"},{"d":"dd","e":"ee","f":"ff"}]} #self.getBlocks(request['hash'])
                self.pm.send(result, nodeID)
            
            # ReturnBlock
            if not self.pm.recv_queue[6].empty():
                message = self.pm.recv_queue[6].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 06, return 07")
                print("Block: %s\n" %(request['blocks']))
                
                for _b in request['blocks']:    
                    #Database().createBlock(_b)  
                    #result = {"method": "07", "hash": _b['transactions']}
                    hsh = [v for v in _b.values()]
                    result = {"method": "07", "hash": hsh}
                    self.pm.send(result, nodeID)
            
            # GetTransaction
            if not self.pm.recv_queue[7].empty():
                message = self.pm.recv_queue[7].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 07, return 09")
                print("Hash: %s\n" %(request['hash']))
                result = {"method": "09", "transactions": [{"ha":"haha"},{"hee":"heehee"},{"huh":"huhuh"}]} #self.getTrans(request['transactions']) # txid->transactions
                self.pm.send(result, nodeID)
            
            # ReturnTransaction
            if not self.pm.recv_queue[9].empty():
                message = self.pm.recv_queue[9].get()
                request = message["data"]
                print("Method: get 09")
                print("Transactions: %s\n" %(request['transactions']))
                print("Test ended.")
                #for _t in request['transactions']:
                #    Database().createTransaction(_t)

            gevent.sleep()
    '''
    def getBlockHashes(self, maxBlocks):
        blockNum = self.db.getBlockNumber(self.pm)
        blocks = []
        for num in range(maxBlocks, blockNum):
            block = self.db.getBlockByID(num)
            blocks.append(block["hash"])
        result = {"method": "03", "hash": blocks}
        return result

    def getBlocks(self, blockHash):
        result = {}; res = []
        for _hash in blockHash:
            res.append(self.db.getBlock(_hash))
        result = {"method": "06", "blocks": res}
        return result

    def getTrans(self, tranHash):
        result = {}; res = []
        for _hash in tranHash:
            res.append(self.db.getTransaction(_hash))
        result = {"method": "09", "transactions": res}
        return result
    '''

class consensusMgr(gevent.Greenlet):
    def __init__(self, node):
        self.pm = node.pm
        #self.db = node.db
        self.key = node.priv_wif
        self.threshold = 2 # min consensus threshold
        self.is_stopped = False
        self.temp = {} # for now, move to db later
    
    def stop(self):
        if not self.is_stopped:
            self.is_stopped = True
            self.kill()
    
    def run(self):
        while not self.is_stopped:
            # Received: General broadcast new proposed block
            if not self.pm.recv_queue[10].empty():
                message = self.pm.recv_queue[10].get()
                nodeID = message["nodeID"]
                blk = message["data"]
                print("Block: %s\n" %(blk['blocks']))
                result = self.signBlock(blk['blocks'])
                self.pm.send(result, nodeID)
            
            # Received: signed blocks from peers
            if not self.pm.recv_queue[12].empty():
                message = self.pm.recv_queue[12].get()
                self.vote(message)                      
            
            # Received: NewSignedBlock 
            if not self.pm.recv_queue[13].empty():
                message = self.pm.recv_queue[13].get()
                # add consensus to end of chain
                consensus = message["data"]["blocks"]
                print("Consensus block: %s" %consensus)
                
            gevent.sleep()
    
    def publishBlock(self, block):
        self.temp[block] = {"voters":list(), "agreed":False}
        self.pm.broadcast(block)

    def vote(self, message):
        nodeID = message["nodeID"]
        block = message["data"]["blocks"]["block"]    # verify signature later
        try:
            if nodeID not in self.temp[block]["voters"]:
                self.temp[block]["voters"].append(nodeID)
                if len(self.temp[block]["voters"]) > self.threshold:
                    consensus = {"method":"13", "blocks":{"block":block}}
                    self.pm.broadcast(consensus)
        except KeyError:
            print("Block not proposed by this node!")
    
    def signBlock(self, block):
        sig = crypto.signdata(wif=self.key, data=block['block'])
        return {"method":"12", "blocks":{"block":block['block'], "signature":sig}}