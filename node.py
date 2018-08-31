# entire node #

import gevent
import trie.MerklePatriciaTrie as MPT
from core.database import Database
from core.block import Block
from p2p.udpPeerManager import PeerManager,State
import p2p.crypto as crypto


#from udpPeerManager import PeerManager, State
#import crypto

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
    def __init__(self, pm_configs, tp, db):
        self.stopped = True
        self.status = {"method":"00","ver":"sue", "id":"","genesisHash":"AC66D1839E1B79F1FB22181B70237F1E45E3D95A512A0790C216328CA2631674","blockNumber":"0", "maxBlock":"3"}
        self.priv_wif = pm_configs['node']['wif']
        pm_configs['node']['ID'] = crypto.priv2addr(priv=pm_configs['node']['privkey'], wif=pm_configs['node']['wif'])
        self.nodeID = pm_configs['node']['ID']
        self.pm = PeerManager(pm_configs)
        self.db = db
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
        
        #self.run() 
        
    def run(self):
        print("Running!!!!!")
        #self.test1()

    def test1(self):
        #msg_2 = {"method":"02", "hash" : "Test starting!", "maxBlock": "0"}
        #self.pm.send(msg_2, self.test_peer)
        print ("sending consensus test to peer...")
        hsh = {'version': 'sue', 'config': {'version': 'init'}, 'blockNumber': '2', 'timestamp': 1535539113.2238808, 'hash': '8f8ea8192e61acc92c7eadb88a821d7a55c2b6eb665ffbcecfb451872a7594c6', 'extraData': '', 'ParentHash': 'ece794d79787fcf4072f525482840f338ec26e94736bf6d1b11e46bdb56721d0', 'verify': [{'7b83ad6afb1209f3c82ebeb08c0c5fa9bf6724548506f2fb4f991e2287a77090177316ca82b0bdf70cd9dee145c3002c0da1d92626449875972a27807b73b42e': 'f54b7e22c7d063b02f71d2aa98b5fdd6a7fbd2fe40db28b0ccd5cc99d21e65a7877e41901f49fb54afa97d44bafb3019c06d61c78cbc1898bc6b137d66bc07d9'}], 'transaction': [{'fee': '000000000000000000000000000010', 'to': 'cxSnVjNUyeNsVkWc4Pxb09MafFujRYWFoSUBnFUE', 'out': {'cic': '13'}, 'nonce': '000000000000000000000000000001', 'type': 'cic', 'input': '', 'sign': '98f5cd573fdd7ced0653b657b33cf4e408a14d58b2b3bd4353a0aceb16ec799ddd2a4d7c3075722c1820ed9c3f04a92d94811ebbc466cfe78573e1f99a3e47d4', 'publicKey': '7b83ad6afb1209f3c82ebeb08c0c5fa9bf6724548506f2fb4f991e2287a77090177316ca82b0bdf70cd9dee145c3002c0da1d92626449875972a27807b73b42e', 'txid': '4e4f181f85a3f6bf0ee32fcbf48d90f8ad30b34b2eb278047903f6b660068fdd', 'from': 'cxa65cfc9af6b7daae5811836e1b49c8d2570c9387', 'timestamp': 1535539113.3744135}]}
        msg_5 = {"method":"05", "blocks":hsh}
        self.mgrs['consensus'].publishBlock(msg_5)


class statusMgr(gevent.Greenlet):
    def __init__(self,node):
        gevent.Greenlet.__init__(self)
        self.pm = node.pm
        self.db = node.db
        self.status = node.status
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
                if new_stat['data']['genesisHash'] == self.status['genesisHash']:
                    if new_stat['data']['blockNumber'] > self.status['blockNumber']:
                        stat = {"method":"03", "from" : self.status['blockNumber'], "to": new_stat['data']['blockNumber'], "maxBlock": self.status['maxBlock']}
                        self.pm.broadcast(stat)
                    elif new_stat['data']['blockNumber'] < self.status['blockNumber']:
                        to = int(self.status['blockNumber']); fro = int(new_stat['data']['blockNumber'])
                        res = [Database.getBlockByID(i, self.db) for i in range(fro+1, to+1)]
                        index = 0; length = to-fro
                        while index < length:
                            if index+int(new_stat['data']['maxBlock']) < length:
                                result = {"method": "04", "blocks": res[index:]}
                            else:
                                result = {"method": "04", "blocks": res[index:index+int(new_stat['data']['maxBlock'])]}
                            index = index + int(new_stat['data']['maxBlock'])
                            self.pm.send(result, new_stat['nodeID'])
            gevent.sleep()    

    def setBlockNum(self, idx):
        self.status['blockNumber'] = idx   


class dbMgr(gevent.Greenlet):
    def __init__(self, node):
        gevent.Greenlet.__init__(self)
        self.db = node.db
        self.pm = node.pm
        self.status = node.status
        self.is_stopped = False

    def stop(self):
        print("Stopping dbMgr......")
        if not self.is_stopped:
            self.is_stopped = True
            self.kill()

    def run(self):
        print("Starting dbMgr...")
        while not self.is_stopped and self.pm.state is State.STARTED:
            '''
            # getBlockHash
            if not self.pm.recv_queue[2].empty():
                message = self.pm.recv_queue[2].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 02, return 03")
                print("Hash: %s\nMax Block: %s\n" %(request['hash'], request['maxBlock']))
                #result = {"method": "03", "hash": ["this","is","test"]} 
                result = self.getBlockHashes(int(request['maxBlock']))
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
            '''
            # get broadcasted block
            if not self.pm.recv_queue[1].empty():
                message = self.pm.recv_queue[1].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 01")
                print("Received broadcasted block: %s\n" %(request['block']))
                request['blocks']['hash'] = int(request['blocks']['hash'],16)
                Database.createBlock([request['blocks']], self.db)
                self.pm.broadcast(request, excluded=[nodeID])


            # get broadcasted transaction
            if not self.pm.recv_queue[2].empty():
                message = self.pm.recv_queue[2].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 02")
                print("Received broadcasted transaction: %s\n" %(request['transaction']))
                Database.pendingTransaction(request['transactions'], self.db)
                self.pm.broadcast(request, excluded=[nodeID])
            
            # getBlock
            if not self.pm.recv_queue[3].empty():
                message = self.pm.recv_queue[3].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 03, return 04")
                print("From: %s\nTo:%s\n" %(request['from'],request['to']))
                #result = self.getBlocks(request['from'],request['to'])
                #self.pm.send(result, nodeID)
                res = [Database.getBlockByID(str(i), self.db) for i in range(int(request['from'])+1, int(request['to'])+1)]
                print("res:", res)
                index = 0; length = int(request['to'])-int(request['from'])
                while index < length:
                    if index+int(request['maxBlock']) < length:
                        result = {"method": "04", "blocks": res[index:]}
                    else:
                        result = {"method": "04", "blocks": res[index:index+int(request['maxBlock'])]}
                    index = index + int(request['maxBlock'])
                    self.pm.send(result, nodeID)
            
            # ReturnBlock
            if not self.pm.recv_queue[4].empty():
                message = self.pm.recv_queue[4].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 04. Updating block and transaction.")
                print("Block: %s\n" %(request['blocks']))
                #hsh = [_b['hash'] for _b in request['blocks']]
                #result = {"method": "07", "hash": hsh}
                #self.pm.send(result, nodeID)
                self.updateBlkTrans(request['blocks'])
                #TODO: if still missing blocks, send another request msg_03, else update status
                self.status['blockNumber'] = request['blocks'][-1]['blockNumber']   #assume last is newest for now
                
            '''
            # GetTransaction
            if not self.pm.recv_queue[7].empty():
                message = self.pm.recv_queue[7].get()
                nodeID = message["nodeID"]
                request = message["data"]
                print("Method: get 07, return 09")
                print("Hash: %s\n" %(request['hash']))
                #result = {"method": "09", "transactions": [{"ha":"haha"},{"hee":"heehee"},{"huh":"huhuh"}]} 
                result = self.getTrans(request['hash']) # txid->transactions
                self.pm.send(result, nodeID)
            
            # ReturnTransaction
            if not self.pm.recv_queue[9].empty():
                message = self.pm.recv_queue[9].get()
                request = message["data"]
                print("Method: get 09")
                print("Transactions: %s\n" %(request['transactions']))
                print("Test ended.")
                Database.createTransaction(request['transactions'], self.db)
            '''
            gevent.sleep()
    
    def updateBlkTrans(self, blockData):
        for _b in blockData:
            # verify and create transactions
            #Database.verifyBalanceAndNonce(_b['transactions'], self.db, "run")
            if _b:
                for _t in _b['transaction']:
                    if _t:
                        Database.updateBalanceAndNonce(_t, self.db) 
                    else:
                        print("transaction is none!")
                Database.createTransaction(_b['transaction'], self.db)
                _b['hash'] = int(_b['hash'],16)
            else:
                print("block is none!")
        Database.createBlock(blockData,self.db)
    
    def getBlockHashes(self, maxBlocks):
        blockNum = Database.getBlockNumber(self.db)           
        blocks = []
        for num in range(maxBlocks, blockNum):
            block = Database.getBlockByID(num, self.db)                
            blocks.append(block["hash"])
        result = {"method": "03", "hash": blocks}
        return result

    def getBlocks(self, blockHash):
        result = {}; res = []
        for _hash in blockHash:
            res.append(Database.getBlock(_hash, self.db))              
        result = {"method": "06", "blocks": res}
        return result

    def getTrans(self, tranHash):
        result = {}; res = []
        for _hash in tranHash:
            res.append(Database.getTransaction(_hash, self.db))  
        result = {"method": "09", "transactions": res}
        return result
    

class consensusMgr(gevent.Greenlet):
    def __init__(self, node):
        gevent.Greenlet.__init__(self)
        self.pm = node.pm
        self.db = node.db       #
        self.key = node.priv_wif
        self.pubkey = crypto.priv2pub(wif=self.key)
        self.threshold = 1 # min consensus threshold
        self.is_stopped = False
        self.temp = {} # for now, move to db later
    
    def stop(self):
        if not self.is_stopped:
            self.is_stopped = True
            self.kill()
    
    def run(self):
        print("Starting consensusMgr...")
        while not self.is_stopped and self.pm.state is State.STARTED:
            # Received: General broadcast new proposed block
            if not self.pm.recv_queue[5].empty():
                message = self.pm.recv_queue[5].get()
                nodeID = message["nodeID"]
                blk = message["data"]
                print("Method: get 05, return 07")
                print("Block: %s\n" %(blk['blocks']))
                result = self.signBlock(blk['blocks'])
                self.pm.send(result, nodeID)
            
            # Received: General request signature
            if not self.pm.recv_queue[6].empty():
                message = self.pm.recv_queue[6].get()
                nodeID = message["nodeID"]
                blk = message["data"]
                print("Method: get 06, return 07")
                print("Block: %s\n" %(blk['blocks']))
                result = self.signBlock(blk['blocks'])
                self.pm.send(result, nodeID)
            
            # Received: signed blocks from peers
            if not self.pm.recv_queue[7].empty():
                print("Method: get 07, return 08")
                message = self.pm.recv_queue[7].get()
                self.vote(message)                      
            
            # Received: NewSignedBlock 
            if not self.pm.recv_queue[8].empty():
                message = self.pm.recv_queue[8].get()
                # add consensus to end of chain
                consensus = message["data"]["blocks"]
                print("Method: get 08, consensus sealed.")
                print("Consensus block: %s" %consensus)
            
            # Received: voter ask for block 
            if not self.pm.recv_queue[9].empty():
                message = self.pm.recv_queue[9].get()
                nodeID = message["nodeID"]
                hsh = message["data"]["blocks"]     # the hash of requested block
                msg_05 = {"method":"05", "blocks":self.temp[hsh]["block"]}
                self.pm.send(msg_05, nodeID)
                
            gevent.sleep()
    
    def publishBlock(self, block):
        key = block['blocks']['hash']
        self.temp[key] = {"block":block['blocks'], "voters":list(), "agreed":False}
        self.pm.broadcast(block)

    def vote(self, message):
        nodeID = message["nodeID"]
        _b = message['data']['blocks']
        
        try:
            crypto.verifydata(pub=_b['pubkey'], sigdata=_b['signature'], origdata=_b["block"])
        except:
            print("Vote verification failed!")

        try:
            block = _b["block"]
            if self.temp[block]:
                try:
                    if nodeID not in self.temp[block]["voters"] and not self.temp[block]['agreed']:
                        self.temp[block]["voters"].append(nodeID)
                        if len(self.temp[block]["voters"]) >= self.threshold:
                            print("Consensus reached, broadcasting block...")
                            self.temp[block]['agreed'] = True
                            consensus = {"method":"08", "blocks":self.temp[block]['block']}
                            self.pm.broadcast(consensus)
                            self.temp[block]['block']['hash'] = int(self.temp[block]['block']['hash'],16)
                            Database.createBlock([self.temp[block]['block']], self.db)
                except KeyError:
                    print("NodeID not from peer!")
            else: 
                print("Block empty...")
        except KeyError:
            print("Block not proposed by this node!")
    
    def signBlock(self, block):
        sig = crypto.signdata(wif=self.key, data=block['hash'])
        return {"method":"07", "blocks":{"block":block['hash'], "signature":sig, "pubkey":self.pubkey}}