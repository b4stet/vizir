import ipaddress
import random
import time



class NetworkNode:
    def __init__(self, network: dict):
        self.block = network['block']
        self.children = []
        self.parent = None
        self.ip_start = network['ip_start']
        self.ip_end = network['ip_end']
        self.ip_start_int = int(ipaddress.ip_address(self.ip_start))
        self.ip_end_int = int(ipaddress.ip_address(self.ip_end))
        self.cidr = int(network['cidr'])
        self.nb_ips = int(network['nb_ips'])
        self.ip_type = network['ip_type']
        self.desc = 'n/a'
    
    def __repr__(self):
        return f"{self.block}, parent: {self.parent}, nb children: {len(self.children)}, desc: {self.desc}"



class NetworksHierarchicalTree:
    def __init__(self, networks: list = []):
        self.roots = []
        self.nodes = {network['block']: NetworkNode(network) for network in networks}
    
    def set_nodes(self, networks: list):
        self.nodes = {network['block']: NetworkNode(network) for network in networks}


    def build(self):
        if len(self.nodes) == 0:
            return

        # reset all nodes
        self.roots = []
        for node in self.nodes.values():
            node.parent = None
            node.children = []

        # Sweep line algorithm init: 
        # create all start/stop events, sort (on dry, stop before start and biggest range first) and keep track of active networks
        events = []
        for network in self.nodes.values():
            events.append((network.ip_start_int, '1_start', network.cidr, network.block))
            events.append((network.ip_end_int, '0_stop', network.cidr, network.block))
        events.sort(key=lambda x: (x[0], x[1], x[2]))
        active_networks = []

        # Process events
        for _, event_type, _, network in events:
            if event_type == '1_start':
                # the most right active network is the smallest parent
                if len(active_networks) > 0:
                    parent_node = self.nodes[active_networks[-1]]
                    child_node = self.nodes[network]
                    child_node.parent = parent_node.block
                    parent_node.children.append(child_node)
                else:
                    self.roots.append(self.nodes[network])
                
                if self.nodes[network].nb_ips > 1:
                    active_networks.append(network)
            
            else:
                if self.nodes[network].nb_ips > 1:
                    active_networks.remove(network)
    
    def print_tree(self):
        if len(self.roots) == 0:
            return "Empty tree"
        
        for root in self.roots:
            self.print_from_node(root, "", True)
    
    def print_from_node(self, node: NetworkNode, prefix: str, is_last: bool):
        print(prefix + ("└── " if is_last else "├── ") + f"{node.block} ({node.desc})")
        for i, child in enumerate(node.children):
            is_child_last = True if i == len(node.children) - 1 else False
            new_prefix = prefix + ("    " if is_last else "│   ")
            self.print_from_node(child, new_prefix, is_child_last)
        
    def test_performance(self, nb_networks: int) -> float:
        networks = []
        for i in range(nb_networks):
            start = random.randint(0, 1000000)
            end = start + random.randint(1, 1000)
            networks.append({
                'block': str(i), 'cidr': end-start, 'nb_ips': 1, 'ip_type': 'x',
                'ip_start': start, 'ip_end': end, 'ip_start_int': start, 'ip_end_int': end, 
            })

        self.set_nodes(networks)

        start_time = time.time()
        self.build()
        end_time = time.time()
        return end_time - start_time


if __name__ == "__main__":
    # test data
    networks = [
        {'block': '0-5', 'ip_start': 0, 'ip_end': 5, 'ip_start_int': 0, 'ip_end_int': 5, 'cidr': 100-(5-0), 'nb_ips': 5-0, 'ip_type': 'x'},
        {'block': '0-100', 'ip_start': 0, 'ip_end': 100, 'ip_start_int': 0, 'ip_end_int': 100, 'cidr': 100-(100-0), 'nb_ips': 100-0, 'ip_type': 'x'},
        {'block': '50-55', 'ip_start': 50, 'ip_end': 55, 'ip_start_int': 50, 'ip_end_int': 55, 'cidr': 100-(55-50), 'nb_ips': 55-50, 'ip_type': 'x'},
        {'block': '10-28', 'ip_start': 10, 'ip_end': 28, 'ip_start_int': 10, 'ip_end_int': 28, 'cidr': 100-(28-10), 'nb_ips': 28-10, 'ip_type': 'x'},
        {'block': '64-67', 'ip_start': 64, 'ip_end': 67, 'ip_start_int': 64, 'ip_end_int': 67, 'cidr': 100-(67-64), 'nb_ips': 67-64, 'ip_type': 'x'}, 
        {'block': '70-94', 'ip_start': 70, 'ip_end': 94, 'ip_start_int': 70, 'ip_end_int': 94, 'cidr': 100-(94-70), 'nb_ips': 94-70, 'ip_type': 'x'},
        {'block': '45-62', 'ip_start': 45, 'ip_end': 62, 'ip_start_int': 45, 'ip_end_int': 62, 'cidr': 100-(62-45), 'nb_ips': 62-45, 'ip_type': 'x'},
        {'block': '42-67', 'ip_start': 42, 'ip_end': 67, 'ip_start_int': 42, 'ip_end_int': 67, 'cidr': 100-(67-42), 'nb_ips': 67-42, 'ip_type': 'x'}, 
    ]
    
    tree = NetworksHierarchicalTree(networks)
    tree.build()
    tree.print_tree()
    for node in tree.nodes.values():
        print(node)

    # timing measurements
    # print("\nPerformance Test:")
    # sizes = [1000, 10000, 100000, 1000000]
    # for size in sizes:
    #     tree = NetworksHierarchicalTree()
    #     elapsed = tree.test_performance(size)
    #     print(f"Built tree with {size} networks: {elapsed:.4f} seconds")