import os
from utils import *
from ChainClass import Blockchain
import pandas as pd
import time
from store_data_in_db import *
import glob, os

def compute_blockchain(transaction_pool_len, nod, transaction_pool, directory_log, nodi, req_n, transaction_list_len, f_node_list, datarate):
    backboneNodes = transaction_pool_len
    
    throughtpu_total_time_list = []
    if transaction_pool_len > 0 :
        
        for i in range(backboneNodes):

            start = time.time()

            i_less= i
            transaction_pool_data= transaction_pool[i_less].split("-")
            which_node = int(transaction_pool_data[0])
            transaction = transaction_pool_data[1]
            transaction_string = transaction_pool_data[1]

            # print(which_node)
            # print(transaction)

            def last_block():
                dl = directory_log+"/blockchain_"+str(which_node)+".csv"

                with open(dl, "r", encoding="utf-8", errors="ignore") as scraped:
                    final_line = scraped.readlines()[-1]
                    return final_line

            dl = directory_log+"/blockchain_"+str(which_node)+".csv"

            def block_len():
                results = pd.read_csv(dl)
                return len(results)


            myblockchain = Blockchain()
            un_list = transaction
            b_len = block_len()
            l_block = last_block()
            l_hash = l_block.split('___')
            l_hash = l_hash[0]

            can_mine_string = ''

            # print(len(un_list))

            if len(un_list) > 0:
                unmined = myblockchain.yet_to_mine(l_hash,un_list)
                proposal = f"{l_hash}-{un_list}"

                proposal_node = f"{which_node}"
                # print(proposal)

                # send pre prepared message
                for x in range(1,nodi):
                    if x in f_node_list:
                        continue
                    else:
                        f=open(directory_log+"/node_"+str(x)+".log", "w")
                        f.write(proposal)
                        f.close()


                #prepare log 2f+1
                prepared_list = []
                faulty_nodes = []
                for x in range(1,nodi):
                    p = 0
                    for y in range(1,nodi):
                        f = open(directory_log+"/node_"+str(y)+".log", "r")
                        p_content = f.read()

                        if proposal == p_content:
                            p = p +1
                        else:
                            faulty_nodes.append(y)

                    if p >= req_n:
                        prepared_list.append(x)

                faulty_nodes = list(dict.fromkeys(faulty_nodes))
                # print(prepared_list)
                # print(faulty_nodes)

                filtered_list = list(filter_list(prepared_list, faulty_nodes))
                filtered_list_len = len(filtered_list)

                # print(filtered_list_len)
                # print(filtered_list_len)

                #commit area

                if which_node in faulty_nodes:
                    print(f'faulty node {which_node}. Cant mine!')
                else:

                    if filtered_list_len < req_n:
                        print(f'cant mine! 2f+1 fails! {filtered_list_len} <{req_n} (min req. node)')
                        break
                    else:
                        can_mine_string = f"Can mine  {filtered_list_len} > = {req_n}(min req. node)"
                        # print('can mine')
                        # print(dl)
                        with open(dl) as file_obj:
                            reader_obj = csv.reader(file_obj)
                            kk = 0
                            for row in reader_obj:
                                kk = kk+1
                                row = row[0].split('___')
                                if kk == 1:
                                    myblockchain.generate_genesis_block()
                                else:
                                    row_1=row[1]
                                    myblockchain.create_block_from_transaction(row_1)

                        myblockchain.mine(unmined)

                        # myblockchain.display_chain()
                        main_chain = myblockchain.get_chain()

                        #update chain to all other node
                        for y in range(1,nodi):
                            if y in f_node_list:
                                continue                            
                            else:                            
                                save(directory_log+"/blockchain_"+str(y)+".csv",main_chain)
                            # f=open(directory_log+"/node_"+str(y)+".log", "w")
                            # f.write('')
                            # f.close()
                        transaction = ''

            else:
                can_mine_string = "nothing to mine. -- no transaction string available"


            elapsed_time_fl = (time.time() - start)
            output_string = f"node {which_node} - {can_mine_string} - transaction {transaction_string} - latency time {elapsed_time_fl} ms \n"
            
            print(output_string)

            throughtpu_total_time_list.append(elapsed_time_fl)
    
    else:
        print('transaction pool empty')

    throughtpu_total_time = sum(throughtpu_total_time_list)  
    throughtput = transaction_list_len/throughtpu_total_time
    avg_delay = throughtpu_total_time/transaction_list_len

    print("\nData inserting into BlockChainData db table........\n")
    
    print(f'total node - {nod}')
    print(f'total transaction - {transaction_list_len}')
    
    print(f'total time - {throughtpu_total_time} ms')
    print(f'throughput total time - {throughtpu_total_time} tps')
    
    print(f'faulty nodes - {faulty_nodes}')
    
    print(f'throughput - {throughtput} tps')
    print(f'avg. delay - {avg_delay} ms')

    
    insert_blockchain_data(nod, transaction_list_len, throughtput, avg_delay, datarate)
        
    return nod, backboneNodes, throughtput, avg_delay, transaction_list_len