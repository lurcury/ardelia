## msg protocol to test PoT ##

import sys
from node import Node
import crypto as crypto

pm_configs = {
    'node' : {'privkey':None,'wif':None},
    'p2p' : {
        'bootstrap_nodes' : [],
        'min_peers':1,
        'max_peers':10,
        'num_workers':1,
        'num_queue':15,
        'listen_port':'',
        'listen_host':'127.0.0.1',
        'timeout':15.0,
        'pingtime':7.0,
        'discovery_delay':0.1
    }
}
pv1 = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
pv2 = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
pb1 = crypto.priv2addr(wif=pv1)
pb2 = crypto.priv2addr(wif=pv2)
peer1 = (('127.0.0.1',10000),pb1)
peer2 = (('127.0.0.1',15000),pb2)

def main(argv):
    
    # setup
    testnum = argv[1]
    if testnum == "node1":
        print("Configs for node 1")
        pm_configs['node']['wif'] = pv1
        pm_configs['p2p']['listen_port'] = '10000'
        test_node = Node(pm_configs,pb2)
        try:
            test_node.start()
        except KeyboardInterrupt:
            test_node.stop()

    elif testnum == "node2":
        print("Configs for node 2")
        pm_configs['node']['wif'] = pv2
        pm_configs['p2p']['listen_port'] = '15000'
        pm_configs['p2p']['bootstrap_nodes'] = [peer1]
        test_node = Node(pm_configs,pb1)
        try:
            test_node.start()
        except KeyboardInterrupt:
            test_node.stop()
    
    #test_node.stop()



if __name__ == '__main__':
    main(sys.argv)