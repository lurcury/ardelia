'''
    To fix:
        - peerManager stopping? running?
            - no "receiving" signal in peer1 after peer2 and peer3 broadcasted
        - gevent event wait/sleep/clear/set
        - figure out how to spawn multiple threads without peermanager dying    --> add to readme
'''
# testing p2p
import time
import gevent
import sys
import os
import signal
import crypto
from tcpPeerManager import PeerManager
from tcpPeer import Peer
import p2p


evt = gevent.event.Event()
transaction1 = {
    'fee': '100',
    'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
    'out': {'cic':'100'},
    'nonce': '10',
    'type': 'cic',
    'input': '90f4god100000000'
}
transaction2 = {
    'fee': '200',
    'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
    'out': {'cic':'200'},
    'nonce': '10',
    'type': 'cic',
    'input': '90f4god100000000'
}
transaction3 = {
    'fee': '300',
    'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
    'out': {'cic':'300'},
    'nonce': '10',
    'type': 'cic',
    'input': '90f4god100000000'
}
transaction4 = {
    'fee': '400',
    'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
    'out': {'cic':'400'},
    'nonce': '10',
    'type': 'cic',
    'input': '90f4god100000000'
}
config = {
    'node' : {'privkey':'','wif':''},
    'p2p' : {
        'bootstrap_nodes' : [],
        'min_peers':1,
        'max_peers':10,
        'forever':False,
        'listen_port':'',
        'listen_host':'127.0.0.1',
        'timeout':6.0,
        'discovery_delay':0.1
    },
    'logs_disconnects':False
}


pv1 = crypto.wif2priv('5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT')
pv2 = crypto.wif2priv('5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ')
pv3 = crypto.wif2priv('5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ')
pv4 = crypto.wif2priv('5JHj8HdUMeDv8nWZazrraWsz9a1jWu7g6UgLCye1vZV9QJ8hprs')
pb1 = crypto.priv2addr(pv1)
pb2 = crypto.priv2addr(pv2)
pb3 = crypto.priv2addr(pv3)
pb4 = crypto.priv2addr(pv4)
peer1 = (('127.0.0.1','10000'),pb1)
peer2 = (('127.0.0.1','15000'),pb2)
peer3 = (('127.0.0.1','20000'),pb3)
peer4 = (('127.0.0.1','25000'),pb4)
def main(argv):
    
    test_subject = argv[1]
    if test_subject == 'peer1':
        print ("%s, pubID: %s" %(test_subject, pb1))
        #config1 = config
        config['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
        config['p2p']['listen_port'] = '10000'
        config['p2p']['bootstrap_nodes'] = []#peer2,peer3,peer4]

    elif test_subject == 'peer2':
        print ("%s, pubID: %s" %(test_subject, pb2))
        #config2 = config
        config['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
        config['p2p']['listen_port'] = '15000'
        config['p2p']['forever'] = False
        config['p2p']['bootstrap_nodes'] = [peer1]#peer3,peer4]
        
    elif test_subject == 'peer3':
        config['node']['wif'] = '5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ'
        config['p2p']['listen_port'] = '20000'
        config['p2p']['bootstrap_nodes'] = [peer1,peer2]#eer4]

    elif test_subject == 'peer4':
        config['node']['wif'] = '5JHj8HdUMeDv8nWZazrraWsz9a1jWu7g6UgLCye1vZV9QJ8hprs'
        config['p2p']['listen_port'] = '25000'
        config['p2p']['bootstrap_nodes'] = [peer1,peer2,peer3]
        
    else:
        print('No such peer!!')
    
    print("Configs for peer: %s" % test_subject)
    evt.clear()
    gevent.signal(signal.SIGQUIT, evt.set)
    gevent.signal(signal.SIGTERM, evt.set)
    gevent.signal(signal.SIGINT, evt.set)
    pm = PeerManager(config)
    pm.start()
    
    thread1 = gevent.spawn(run_pm_loop, pm, test_subject)
    thread2 = gevent.spawn(end_pm, pm)
    
    gevent.joinall([pm,thread1, thread2])
    #evt = gevent.event.Event()
    #gevent.signal(signal.SIGQUIT, evt.set)
    #gevent.signal(signal.SIGTERM, evt.set)
    #gevent.signal(signal.SIGINT, evt.set)
    #evt.wait()
    

def run_pm_loop(pm, test_subject):
    '''
    Test 1: peer1 sending data to peer2
    start_time = time.time()
    count = 0
    print("running! time: %f" %start_time)
    while not pm.is_stopped:
        if test_subject == 'peer1':
            packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction1))
            pm.send(packet,pb2)
        if test_subject == 'peer2':
            if not pm.recv_queue.empty():
                count = count+1
                print("You've got mail! #of mails: %i" % len(pm.recv_queue))
                msg = pm.recv_queue.get()
                print("One mail from: %s \n There are %i messages left in inbox." % (msg['node']['pubID'], len(pm.recv_queue)))
                
                #print(msg['transaction'])
                #print("Broadcasting received message...")
                #packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=msg['transaction']))
                #pm.broadcast(packet,excluded=[msg['node']['pubID']])
                
                print("peermanager stopped. Count: %i, time elapsed: %f" %(count, time.time()-start_time))
        gevent.sleep(0)
    '''
    
    # Another test: 4 peers broadcasting and receiving
    if test_subject == 'peer1':
        gevent.sleep(2)
        packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction1))
        pm.send(packet,pb2)   
    if test_subject == 'peer2':
        gevent.sleep(1.2)
        packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction2))
        #pm.broadcast(packet)
        pm.send(packet,pb3)
    if test_subject == 'peer3':
        gevent.sleep(0.6)
        packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction3))
        #pm.broadcast(packet)
        pm.send(packet,pb4)
    if test_subject == 'peer4':
        packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction4))
        #pm.broadcast(packet)
        pm.send(packet,pb1)
    start_time = time.time()
    count = 0
    print("running! time: %f" %start_time)
    while not pm.is_stopped:
        # the same as: if keyboard interrupt: evt.set()
        if not pm.recv_queue.empty():
            count = count+1
            print("You've got mail! #of mails: %i" % len(pm.recv_queue))
            msg = pm.recv_queue.get()
            print("One mail from: %s \n There are %i messages left in inbox." % (msg['node']['pubID'], len(pm.recv_queue)))
            print(msg['transaction'])
            print("Broadcasting received message...")
            packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=msg['transaction']))
            pm.broadcast(packet,excluded=[msg['node']['pubID']])
            print("peermanager stopped. Count: %i, time elapsed: %f" %(count, time.time()-start_time))
        gevent.sleep(0)
    
    '''
    # Another test in while loop: send to next peer in a circle
    while not pm.is_stopped:
        if test_subject == 'peer1':
            packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction1))
            pm.send(packet,pb2)
        if test_subject == 'peer2':
            packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction2))
            #pm.broadcast(packet)
            pm.send(packet,pb3)
        if test_subject == 'peer3':
            packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction3))
            #pm.broadcast(packet)
            pm.send(packet,pb1)
            #if test_subject == 'peer4':
            #    packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction3))
            #    pm.send(packet,pb1)
            #pm2.send(packet2,pb1)
        if not pm.recv_queue.empty():
            print("You've got mail! #of mails: %i" % len(pm.recv_queue))
        #if test_subject == 'peer1':
        gevent.sleep(0)
    '''
    #print("peermanager stopped. Count: %i, time elapsed: %f" %(count, time.time()-start_time))

def end_pm(pm):
    print("blocking!")
    evt.wait()
    print("non-blocking!")
    #print("peermanager stopped. Count: %i, time elapsed: %f" %(count, time.time()-start_time))
    pm.stop()

if __name__ == '__main__':
    main(sys.argv)