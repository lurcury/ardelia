# testing p2p

import sys
import os
import crypto
import peerManager
import p2p

def main(argv):
    
    transaction = {
        'fee': '100',
        'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
        'out': {'cic':'100'},
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
            'listen_port':'',
            'listen_host':'127.0.0.1',
            'timeout':1.0,
            'discovery_delay':0.1
        },
        'logs_disconnects':False
    }


    pv1 = crypto.wif2priv('5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT')
    pv2 = crypto.wif2priv('5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ')
    #pv3 = crypto.wif2priv('5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ')
    #pv4 = crypto.wif2priv('5JHj8HdUMeDv8nWZazrraWsz9a1jWu7g6UgLCye1vZV9QJ8hprs')
    pb1 = crypto.priv2addr(pv1)
    pb2 = crypto.priv2addr(pv2)
    #pb3 = crypto.priv2addr(pv3)
    #pb4 = crypto.priv2addr(pv4)
    peer1 = (('127.0.0.1','10000'),pb1)
    peer2 = (('127.0.0.1','8000'),pb2)
    #peer3 = (('127.0.0.1','30307'),pb3)
    #peer4 = (('127.0.0.1','30309'),pb4)

    #test_subject = argv[1]
    #if test_subject == 'peer1':
    #    print ("%s, pubID: %s" %(test_subject, pb1))
    #config1 = config
    #config1['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
    #config1['p2p']['listen_port'] = '30303'
    #config1['p2p']['bootstrap_nodes'] = [peer2]
    config1 = {
        'node' : {'privkey':'','wif':'5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'},
        'p2p' : {
            'bootstrap_nodes' : [peer2],
            'min_peers':1,
            'max_peers':10,
            'listen_port':'10000',
            'listen_host':'127.0.0.1',
            'timeout':1.0,
            'discovery_delay':0.1
        },
        'logs_disconnects':False
    }
    #config['p2p']['bootstrap_nodes'] = [peer2,peer3,peer4]
        
    #elif test_subject == 'peer2':
    #    print ("%s, pubID: %s" %(test_subject, pb2))
    #config2 = config
    #config2['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
    #config2['p2p']['listen_port'] = '30305'
    #config2['p2p']['bootstrap_nodes'] = [peer1]
    config2 = {
        'node' : {'privkey':'','wif':'5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'},
        'p2p' : {
            'bootstrap_nodes' : [peer1],
            'min_peers':1,
            'max_peers':10,
            'listen_port':'8000',
            'listen_host':'127.0.0.1',
            'timeout':1.0,
            'discovery_delay':0.1
        },
        'logs_disconnects':False
    }
    #config['p2p']['bootstrap_nodes'] = [peer1,peer3,peer4]
    '''
    elif test_subject == 'peer3':
        config['node']['wif'] = '5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ'
        config['p2p']['listen_port'] = '30305'
        config['p2p']['bootstrap_nodes'] = [peer1,peer2,peer4]

    elif test_subject == 'peer4':
        config['node']['wif'] = '5JHj8HdUMeDv8nWZazrraWsz9a1jWu7g6UgLCye1vZV9QJ8hprs'
        config['p2p']['listen_port'] = '30306'
        config['p2p']['bootstrap_nodes'] = [peer1,peer2,peer3]

    else:
        print('No such peer!!')
    '''
    print("Configs for peer1: %s" % pb1)
    pm1 = peerManager.PeerManager(config1)
    pm1.start()
    print("Configs for peer2: %s" % pb2)
    pm2 = peerManager.PeerManager(config2)
    pm2.start()
    pm1.bootstrap(pm1.configs['p2p']['bootstrap_nodes'])
    pm2.bootstrap(pm2.configs['p2p']['bootstrap_nodes'])
    packet1 = p2p.Packet("transaction", dict(node=dict(address=pm1.address, pubID=pm1.configs['node']['id']),transaction=transaction))
    packet2 = p2p.Packet("transaction", dict(node=dict(address=pm2.address, pubID=pm2.configs['node']['id']),transaction=transaction))
    pm1.broadcast(packet1)
    pm2.send(packet2,pb1)

if __name__ == '__main__':
    main(sys.argv)