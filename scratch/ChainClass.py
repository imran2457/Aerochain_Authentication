import uuid
from datetime import datetime

from utils import *


class GeekCoinBlock:
    def __init__(self, previous_block_hash, transaction_list):
        self.index = int(uuid.uuid4())
        self.timestamp = datetime.now()
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list
        self.block_data = f"{transaction_list}___{previous_block_hash}"
        # time.sleep(0.05)
        self.block_hash = SHA256(self.block_data)


class Blockchain:
    def __init__(self):
        self.chain = []
        # self.generate_genesis_block()

    def generate_genesis_block(self):
        self.chain.append(GeekCoinBlock("0", 'Genesis Block'))

    def create_block_from_transaction(self, transaction_list):
        previous_block_hash = self.last_block.block_hash
        self.chain.append(GeekCoinBlock(previous_block_hash, transaction_list))

    def yet_to_mine(self, previous_block_hash, transaction_list):
        block_unmined = GeekCoinBlock(previous_block_hash, transaction_list)
        return block_unmined

    def mine(self, block):
        MAX_NONCE = 100000000000
        zeroes = 4
        prefix = '1' * zeroes

        for nonce in range(MAX_NONCE):
            new_hash = block.transaction_list
            new_hash = SHA256(str(new_hash) + str(nonce))

            if new_hash.startswith(prefix):
                # print(f"Yay! Successfully mined bitcoins with nonce value:{nonce}")
                self.chain.append(block)
                return new_hash
        return -1

    def display_chain(self):
        for i in range(len(self.chain)):
            print(f"Data {i + 1}: {self.chain[i].block_data}")
            print(f"Hash {i + 1}: {self.chain[i].block_hash}\n")

    def get_chain(self):
        chain_list = []
        for i in range(len(self.chain)):
            segment = f"{self.chain[i].block_hash}___{self.chain[i].block_data}___{self.chain[i].index}___{self.chain[i].timestamp}"
            chain_list.append(segment)
        return chain_list

    def chain_update(self, nodi, f_node_list, directory_log, main_chain):
        for y in range(1, nodi):

            if y in f_node_list:
                continue
            else:
                save(directory_log + "/blockchain_" + str(y) + ".csv", main_chain)
        transaction = ''

    @property
    def last_block(self):
        return self.chain[-1]


class Mejority:

    def send_prepared_msg(self, nodi, f_node_list, directory_log, proposal):
        for x in range(1, nodi):
            if x in f_node_list:
                continue
            else:
                f = open(directory_log + "/node_" + str(x) + ".log", "w")
                f.write(proposal)
                f.close()

    def mejority(self, nodi, directory_log, proposal, req_n):
        # send pre prepared message
        prepared_list = []
        faulty_nodes = []

        for x in range(1, nodi):
            p = 0
            for y in range(1, nodi):
                f = open(directory_log + "/node_" + str(y) + ".log", "r")
                p_content = f.read()

                if proposal == p_content:
                    p = p + 1
                else:
                    faulty_nodes.append(y)

            if p >= req_n:
                prepared_list.append(x)

        faulty_nodes = list(dict.fromkeys(faulty_nodes))

        filtered_list = list(filter_list(prepared_list, faulty_nodes))
        filtered_list_len = len(filtered_list)

        mejority_func_list = [[filtered_list_len], [prepared_list], [faulty_nodes]]

        return mejority_func_list