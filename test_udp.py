# test UDP #
import time
import gevent
import sys
import os
import signal
import crypto
import json
from udpPeerManager import PeerManager, State
from udpPeer import Peer
from p2p import Packet


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
    'node' : {'privkey':None,'wif':None},
    'p2p' : {
        'bootstrap_nodes' : [],
        'min_peers':1,
        'max_peers':10,
        'num_workers':3,
        'listen_port':'',
        'listen_host':'127.0.0.1',
        'timeout':15.0,
        'pingtime':7.0,
        'discovery_delay':0.1
    },
}


pv1 = crypto.wif2priv('5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT')
pv2 = crypto.wif2priv('5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ')
pv3 = crypto.wif2priv('5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ')
pv4 = crypto.wif2priv('5JHj8HdUMeDv8nWZazrraWsz9a1jWu7g6UgLCye1vZV9QJ8hprs')
pb1 = crypto.priv2addr(pv1)
pb2 = crypto.priv2addr(pv2)
pb3 = crypto.priv2addr(pv3)
pb4 = crypto.priv2addr(pv4)
peer1 = (('127.0.0.1',10000),pb1)
peer2 = (('127.0.0.1',15000),pb2)
peer3 = (('127.0.0.1',20000),pb3)
peer4 = (('127.0.0.1',25000),pb4)

def main(argv):    
    test_subject = argv[1]
    if test_subject == 'peer1':
        print ("%s, pubID: %s" %(test_subject, pb1))
        config['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
        config['p2p']['listen_port'] = '10000'
        config['p2p']['bootstrap_nodes'] = []

    elif test_subject == 'peer2':
        print ("%s, pubID: %s" %(test_subject, pb2))
        config['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
        config['p2p']['listen_port'] = '15000'
        config['p2p']['bootstrap_nodes'] = [peer1]
           
    elif test_subject == 'peer3':
        print ("%s, pubID: %s" %(test_subject, pb3))
        config['node']['wif'] = '5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ'
        config['p2p']['listen_port'] = '20000'
        config['p2p']['bootstrap_nodes'] = [peer1,peer2]

    elif test_subject == 'peer4':
        print ("%s, pubID: %s" %(test_subject, pb4))
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
    

def run_pm_loop(pm, test_subject):
    # Test: 4 peers broadcasting and receiving
    if test_subject == 'peer1':
        gevent.sleep(2)
        packet = dict(data=transaction1)
        pm.send(packet,pb2)   
    if test_subject == 'peer2':
        gevent.sleep(1.2)
        packet = dict(data=transaction2)
        pm.send(packet,pb3) 
    if test_subject == 'peer3':
        gevent.sleep(0.6)
        packet = dict(data=transaction3)
        pm.send(packet,pb4) 
    if test_subject == 'peer4':
        packet = dict(data=transaction4)
        pm.send(packet,pb1) 
    start_time = time.time()
    count = 0
    print("running! time: %f" %start_time)
    while pm.state is State.STARTED:
        if not pm.recv_queue.empty():
            count = count+1
            print("You've got mail! #of mails: %i" % len(pm.recv_queue))
            msg = pm.recv_queue.get()
            print("One mail from: %s \n There are %i messages left in inbox.\n %s" % (msg['nodeID'], len(pm.recv_queue), msg['data']))#data))
            if not test_subject == 'peer4':
                print("Broadcasting received message...")
                pm.broadcast(msg['data'],excluded=[msg['nodeID']])
            print("Count: %i, time elapsed: %f" %(count, time.time()-start_time))
        gevent.sleep(1)
    
def end_pm(pm):
    print("blocking!")
    evt.wait()
    print("non-blocking!")
    pm.stop()

if __name__ == '__main__':
    main(sys.argv)