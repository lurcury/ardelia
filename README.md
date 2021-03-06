# ardelia
python implementation of the P2P protocol with discovery and kademlia algorithm 

## usage
The current implementation supports p2p packet transmission between nodes. 

<<<<<<< HEAD
**NOTE: please import tcpPeerManager and tcpPeer! PeerManager.py and Peer.py is currently under revision.**

### configs

> To setup this network, you need to provide the ip address and ports of each server node and a private key in hex or wif format. When creating a peerManager instance, the following default configurations are fed into the constructor if user-defined configs are not provided.
=======
**NOTE: please import udpPeerManager and udpPeer!**
### details

* The implementation uses udp with ping pong to ensure connection
* The packets are signed and verified by protocol upon sending and receiving to check validity and integrity of peer.
* The routing algorithm (yet to be done) will be Chord instead of Kademlia.

### configs

> To setup this network, you need to provide the ip address and ports of each server node and a private key in hex or wif format. `min_peers` and `max_peers` indicate the allowed range of directly connected peers, while `timeout` and `pingtime` indicate the length of time(in seconds) before, respectively, a socket timeouts and the peer pings. The parameter `num_workers` determine the number of packet signers and verifiers in order to accelerate packet processing. The parameter `num_queue` corresponds to the number of queues needed for each message type.

When creating a peerManager instance, the following default configurations are fed into the constructor if user-defined configs are not provided.
>>>>>>> dev

    default_config = dict(p2p=dict(bootstrap_nodes=[],
                                   min_peers=1,
                                   max_peers=10,
<<<<<<< HEAD
                                   forever=False,
                                   listen_port=30303,
                                   listen_host='0.0.0.0',
                                   timeout = 5.0,
                                   discovery_delay = 0.1),
                          log_disconnects=False,
                          node=dict(privkey='',wif=''))
=======
                                   num_workers=1,
                                   num_queue=10,
                                   listen_port=30303,
                                   listen_host='0.0.0.0',
                                   timeout=10.0,
                                   pingtime=5.0
                                   discovery_delay = 0.1),
                          node=dict(privkey=None,wif=None))
>>>>>>> dev


Please feed your own configurations, for example:

    config = {
<<<<<<< HEAD
            'node' : {'privkey':'','wif':'5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'},
=======
            'node' : {'privkey':None,'wif':'5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT', 'ID':''},
>>>>>>> dev
            'p2p' : {
                'bootstrap_nodes' : [peer1,peer2],
                'min_peers':1,
                'max_peers':10,
<<<<<<< HEAD
                'forever':False,
                'listen_port':'10000',
                'listen_host':'127.0.0.1',
                'timeout':6.0,
                'discovery_delay':0.1
            },
            'logs_disconnects':False
=======
                'num_workers':3,
                'num_queue':10,
                'listen_port':'10000',
                'listen_host':'127.0.0.1',
                'timeout':10.0,
                'pingtime':5.0,
                'discovery_delay':0.1
            },
>>>>>>> dev
        }
    pm = PeerManager(config)
    pm.start()

### initialization

> After the server has started, peerManager will bootstrap to the nodes in configurations, therefore it is extremely important that you start the target server before attempting to connect to it, otherwise the socket will return \[Error 61] connection refused and close the socket. 
For example, the following code will fail, regardless of the order of server initialization.

    test_subject = argv[1]
        if test_subject == 'peer1':
            print ("%s, pubID: %s" %(test_subject, pb1))
            #config1 = config
            config['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
<<<<<<< HEAD
=======
            config['node']['ID'] = pb1
>>>>>>> dev
            config['p2p']['listen_port'] = '10000'
            config['p2p']['bootstrap_nodes'] = [peer2, peer3]

        elif test_subject == 'peer2':
            print ("%s, pubID: %s" %(test_subject, pb2))
            #config2 = config
            config['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
<<<<<<< HEAD
            config['p2p']['listen_port'] = '15000'
            config['p2p']['forever'] = False
=======
            config['node']['ID'] = pb2
            config['p2p']['listen_port'] = '15000'
>>>>>>> dev
            config['p2p']['bootstrap_nodes'] = [peer1]

        elif test_subject == 'peer3':
            config['node']['wif'] = '5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ'
<<<<<<< HEAD
=======
            config['node']['ID'] = pb3
>>>>>>> dev
            config['p2p']['listen_port'] = '20000'
            config['p2p']['bootstrap_nodes'] = [peer2]
        ....

And the following will work if the servers are started in the order of: peer1 -> peer2 -> peer3.

    test_subject = argv[1]
        if test_subject == 'peer1':
            print ("%s, pubID: %s" %(test_subject, pb1))
<<<<<<< HEAD
            #config1 = config
            config['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
=======
            config['node']['wif'] = '5JdFN2jJvC9bCuN4F9i93RkDqBDBqcyinpzBRmnW8xXiXsnGmHT'
            config['node']['ID'] = pb1
>>>>>>> dev
            config['p2p']['listen_port'] = '10000'
            config['p2p']['bootstrap_nodes'] = []

        elif test_subject == 'peer2':
            print ("%s, pubID: %s" %(test_subject, pb2))
<<<<<<< HEAD
            #config2 = config
            config['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
            config['p2p']['listen_port'] = '15000'
            config['p2p']['forever'] = False
=======
            config['node']['wif'] = '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'
            config['node']['ID'] = pb2
            config['p2p']['listen_port'] = '15000'
>>>>>>> dev
            config['p2p']['bootstrap_nodes'] = [peer1]

        elif test_subject == 'peer3':
            config['node']['wif'] = '5KHSJUf7C6tnTQHwTKxuMKi9ifEeMdMs5XrGBJMU92yebTqyjMZ'
<<<<<<< HEAD
=======
            config['node']['ID'] = pb3
>>>>>>> dev
            config['p2p']['listen_port'] = '20000'
            config['p2p']['bootstrap_nodes'] = [peer1,peer2]
        ....

### sending and receiving packets

> The server takes care of sending and receiving packets, and stores the data in queues under Peer. To broadcast a packet, first create a packet with your payload, then call the broadcast() function provided by peerManager. Broadcast() has an optional parameter `excluded_peers` where you can explicitly list nodes that you don't want to broadcast to(often times the original node you received the broadcast from). Or, if the packet is meant for a specific peer, use the send() function provided by peerManager, which requires the parameter `pubkey` of the receiving node.

    transaction1 = {
            'fee': '100',
            'to': 'cx68c59720de07e4fdc28efab95fa04d2d1c5a2fc1',
            'out': {'cic':'100'},
            'nonce': '10',
            'type': 'cic',
            'input': '90f4god100000000'
        }
<<<<<<< HEAD
    packet = p2p.Packet("transaction", dict(node=dict(address=pm.address, pubID=pm.configs['node']['id']),transaction=transaction1))
    pm.broadcast(packet)      # for broadcasting
    pm.send(packet,pb1)       # for specific node

> For the time being, only transaction packets are implemented, though other methods can be created in a similar fashion. To access received transactions, get() from peerManager's inbox(pm.recv_queue) for the decoded packet.

    packet = pm.recv_queue.get()
    print("Data contents of transaction packet:", packet['transaction'])
=======
    packet = dict(method="02", transaction=transaction1)
    pm.broadcast(packet)      # for broadcasting
    pm.send(packet,pb1)       # for specific node

> All regular data packets, including but not limited to transactions, node status, blocks, and commits are accessible by calling get() from peerManager's inbox(pm.recv_queue) for the decoded packet. The returned item is a dictionary including the sender's public ID and the payload.

    packet = pm.recv_queue[2].get()
    print("From: %s \n Contents: %s", %(packet['nodeID'], packet['data']))
>>>>>>> dev


### stopping server

<<<<<<< HEAD
> The object Event() at the end of the code catches keyboard interrupt signals and stops the peerManager(which then stops the server and peer connections), therefore to terminate the program, press ctrl-c. If peerManager is to be instantiated in another program, use `evt.set()` before creating a peerManager and `evt.clear()` to terminate it.

For examples on how to use this network, please refer to test2.py.
To run test2.py, open up 4 terminals and in each one, type in the following command(with X substituting the index):
    
    python3.py test2.py peerX
=======
> The object Event() at the end of the code catches keyboard interrupt signals and stops the peerManager(which then stops the server and peer connections), therefore to terminate the program, press ctrl-c. If peerManager is to be instantiated in another program, use `evt.clear()` before creating a peerManager and `evt.set()` to link it to the terminate signal.

For examples on how to use this network, please refer to test_udp.py. 
To run test_udp.py, open up 4 terminals and in each one, type in the following command(with X substituting the index):
    
    python3.py test_udp.py peerX
    
**For examples on how to use peerManager in a node, please refer to node_test.py and node.py.**


### debugging tips
> For those unfamiliar with gevent, the following tips when utilizing this module may be helpful. 
* When spawning greenlets, `gevent.joinall([threads])` runs until all greenlets have terminated. This is useful when you want to make sure your program doesn't terminate prematurely.
* The target of a spawned greenlet is usually a function, and if you create a while loop inside your function, you should explicitly call `gevent.sleep()` which yields control to other threads if your peermanager might not call send(), in which case the socket operation implicitly yields. If you're not sure which gevent objects implicitly yield to other threads, check the [documentation](http://www.gevent.org/contents.html) or call `sleep()` yourself.
>>>>>>> dev
