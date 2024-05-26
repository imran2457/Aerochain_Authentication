import os
import glob
import secrets
import shutil
import string
import sys
import uuid
import pandas as pd
from functools import reduce
import ns.core
import ns.network
import ns.internet
import ns.wifi
import ns.csma
import ns.mobility
import ns.applications
import ns.flow_monitor
import ns.netanim
import ns.olsr
from blockchain import *
from store_data_in_db import *
import sys
from HmacAuthentication import *
from utils import *

def InitializeNetwork(nod, datarate, packetSize):

    # Set the time resolution to nanoseconds
    #ns.core.Time.SetResolution(ns.core.Time.NS)

    # Create nodes (1 AP + multiple STAs)
    ap_node = ns.network.NodeContainer()
    ap_node.Create(1)

    num_stas = nod
    sta_nodes = ns.network.NodeContainer()
    sta_nodes.Create(num_stas)

    all_nodes = ns.network.NodeContainer()
    all_nodes.Add(ap_node)
    all_nodes.Add(sta_nodes)

    # Set up Wi-Fi channel
    channel = ns.wifi.YansWifiChannelHelper.Default()
    phy_helper = ns.wifi.YansWifiPhyHelper()
    phy_helper.SetChannel(channel.Create())

    # Set up Wi-Fi MAC and configure for AP and STA
    ssid = ns.wifi.Ssid("ns-3-wifi")
    mac = ns.wifi.WifiMacHelper()
    wifi_helper = ns.wifi.WifiHelper()

    dataRate = 'OfdmRate'+datarate+'Mbps'
    5
    wifi_helper.SetRemoteStationManager("ns3::ConstantRateWifiManager", "DataMode", ns.core.StringValue(dataRate))
    phy_helper.SetPcapDataLinkType(phy_helper.DLT_IEEE802_11_RADIO)
     
    csma = ns.csma.CsmaHelper()
    internet = ns.internet.InternetStackHelper()
    # Configure AP
    mac.SetType("ns3::ApWifiMac", "Ssid", ns.wifi.SsidValue(ssid))
    ap_device = wifi_helper.Install(phy_helper, mac, ap_node)

    # Configure STAs
    mac.SetType("ns3::StaWifiMac", "Ssid", ns.wifi.SsidValue(ssid), "ActiveProbing", ns.core.BooleanValue(False))
    sta_devices = wifi_helper.Install(phy_helper, mac, sta_nodes)


    minX = 100
    maxX = 200
    minY = 100
    maxY = 200
    minZ = 100
    maxZ = 200

    area = (maxX - minX) * (maxY - minY)
    height = maxZ - minZ

    area_string = str(minX) + "|" + str(maxX) + "|" + str(minY) + "|" + str(maxY) + "|" + str(minZ) + "|" + str(maxZ)

    # Set mobility model

    '''
    mobility = ns.mobility.MobilityHelper()
    mobility.SetPositionAllocator("ns3::GridPositionAllocator",
                                  "MinX", ns.core.DoubleValue(0.0),
                                  "MinY", ns.core.DoubleValue(0.0),
                                  "DeltaX", ns.core.DoubleValue(5.0),
                                  "DeltaY", ns.core.DoubleValue(5.0),
                                  "GridWidth", ns.core.UintegerValue(1),
                                  "LayoutType", ns.core.StringValue("RowFirst"))
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    mobility.Install(all_nodes)

    '''
    
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel("ns3::GaussMarkovMobilityModel",
                                  "Bounds", ns.core.StringValue(area_string),
                                  "TimeStep", ns.core.TimeValue(ns.core.Seconds(0.5)),
                                  "Alpha", ns.core.DoubleValue(0.85),
                                  "MeanVelocity", ns.core.StringValue("ns3::UniformRandomVariable[Min=800|Max=1200]"),
                                  "MeanDirection", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=6.283185307]"),
                                  "MeanPitch", ns.core.StringValue("ns3::UniformRandomVariable[Min=0.05|Max=0.05]"),
                                  "NormalVelocity", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.0|Bound=0.0]"),
                                  "NormalDirection", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.2|Bound=0.4]"),
                                  "NormalPitch", ns.core.StringValue("ns3::NormalRandomVariable[Mean=0.0|Variance=0.02|Bound=0.04]"))

    mobility.SetPositionAllocator("ns3::RandomBoxPositionAllocator",
                                      "X", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"),
                                      "Y", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"),
                                      "Z", ns.core.StringValue("ns3::UniformRandomVariable[Min=0|Max=100]"))

    mobility.Install(all_nodes)    

    # Install Internet stack
    stack = ns.internet.InternetStackHelper()
    stack.Install(all_nodes)

    # Assign IP addresses
    address = ns.internet.Ipv4AddressHelper()
    address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))
    ap_interface = address.Assign(ap_device)
    sta_interfaces = address.Assign(sta_devices)

    #Getting blockchain size 
    
    #packetSize = blockchain(transaction_pool_len, nod, transaction_pool, directory_log, nodi, req_n, transaction_list_len, f_node_list)
    
    # Set up applications (UDP echo client/server)
    port = 9
    echoServer = ns.applications.UdpEchoServerHelper(port)
    serverApps = echoServer.Install(ap_node.Get(0))
    serverApps.Start(ns.core.Seconds(1.0))
    serverApps.Stop(ns.core.Seconds(10.0))

    echoClient = ns.applications.UdpEchoClientHelper(ap_interface.GetAddress(0), port)
    echoClient.SetAttribute("MaxPackets", ns.core.UintegerValue(100))
    echoClient.SetAttribute("Interval", ns.core.TimeValue(ns.core.Seconds(0.1)))
    # packetSize - we need use the block size as packet size
    echoClient.SetAttribute("PacketSize", ns.core.UintegerValue(packetSize))

    clientApps = echoClient.Install(sta_nodes)
    clientApps.Start(ns.core.Seconds(2.0))
    clientApps.Stop(ns.core.Seconds(10.0))

    print("\n---------Configure Tracing for network data------------------")

    anim = ns.netanim.AnimationInterface("NetworkData-Animation.xml")
    ascii = ns.network.AsciiTraceHelper()

    stream = ascii.CreateFileStream("NetworkData-tracefile.tr")
    phy_helper.EnableAsciiAll(stream)
    phy_helper.EnablePcap("apgc-data", ap_device)
    phy_helper.EnablePcap("standardnode-data", sta_devices)

    csma.EnableAsciiAll(stream)
    internet.EnableAsciiIpv4All(stream)
    csma.EnablePcapAll("csma-pcap", False)


    # Flow Monitor
    flowmon_helper = ns.flow_monitor.FlowMonitorHelper()
    monitor = flowmon_helper.InstallAll()

    # Set FlowMonitor attributes
    monitor.SetAttribute("DelayBinWidth", ns.core.DoubleValue(0.001))
    monitor.SetAttribute("JitterBinWidth", ns.core.DoubleValue(0.001))
    monitor.SetAttribute("PacketSizeBinWidth", ns.core.DoubleValue(20))

    # Run simulation
    ns.core.Simulator.Stop(ns.core.Seconds(100))
    ns.core.Simulator.Run()

    # Collect and print statistics
    total_throughput_list = []
    total_delay_list = []

    def print_stats(st):
        rxBytes = st.rxBytes
        txTime = st.timeLastRxPacket.GetSeconds() - st.timeFirstTxPacket.GetSeconds()
        throughput = (rxBytes * 8) / txTime / 1e6  # Mbps
        total_throughput_list.append(throughput)

        if st.rxPackets > 0:
            delay = st.delaySum.GetSeconds() / st.rxPackets
            total_delay_list.append(delay)

    monitor.CheckForLostPackets()
    classifier = flowmon_helper.GetClassifier()
    stats = monitor.GetFlowStats()

    for flow_id, flow_stats in stats:
        print(f"Flow ID: {flow_id}, Rx Bytes: {flow_stats.rxBytes}")
        print_stats(flow_stats)

    totalTP = sum(total_throughput_list)
    totalDelay = sum(total_delay_list) 
    avg_throughput = sum(total_throughput_list) / len(total_throughput_list) if total_throughput_list else 0
    avg_delay = sum(total_delay_list) / len(total_delay_list) if total_delay_list else 0

    print("\nNetwork Data is below: ")
    print(f"\nDatarate: {datarate} Mbps")
    print(f"\nTotal Throughput: {totalTP} Mbps")
    print(f"Total Delay: {totalDelay} s")

    print(f"\nAverage Throughput: {avg_throughput} Mbps")
    print(f"Average Delay: {avg_delay} s")

    print("\nAll nodes are in "+ str(area) + " m3 and height from ground " + str(height) + " m")
    # Cleanup
    ns.core.Simulator.Destroy()

    # numberofNode, numberoftrans
    return nod, packetSize, totalTP, avg_throughput, totalDelay, avg_delay, area, height


def GenerateBlockChainAndReturnBlockSize(transaction_pool_len, nod, transaction_pool, directory_log, nodi, req_n, transaction_list_len, f_node_list, datarate, csvFilePath):
    
    packetSize = 0
    nod, backboneNodes, throughtput, avg_delay, num_of_transation = compute_blockchain(transaction_pool_len, nod, transaction_pool, directory_log, nodi, req_n, transaction_list_len, f_node_list, datarate)

    #csv_file_path = '/home/isuvo/ns-allinone-3.36.1/ns-3.36.1/test_logs/blockchain_1.csv'

    if os.path.exists(csvFilePath):
        packetSize = os.path.getsize(csvFilePath)
    else:
        print(f"The file '{csvFilePath}' does not exist.")

    print("\nBlockchain Data --> Above result is for " + str(nod) + " nodes and " + str(num_of_transation) + " transactions and packet size : " + str(packetSize) + " bytes(size/logfile)")
    #print(str(num_of_transation))
    return packetSize


def main():

    payloadSize = 0

    """
    current_directory = os.getcwd()
    directory_main = current_directory+'/test'
    directory_log = current_directory+'/test_logs'

    pat = current_directory+'/test_logs_pool/*'
    pat_r = glob.glob(pat)
    for i in pat_r:
        os.remove(i)
    """
    
    # Generate a unique directory name using the current timestamp and an incrementing counter
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    run_id = get_next_run_id()
    current_directory = os.getcwd()
    unique_dir_name = f'Log_{timestamp}_{run_id}'

    #directory_main = os.path.join(current_directory, unique_dir_name, 'test')
    directory_log = os.path.join(current_directory, unique_dir_name)
    directory_networkdata = os.path.join(current_directory, unique_dir_name, 'NetworkData')
    directory_secretKey = os.path.join(current_directory, unique_dir_name, 'SecretKey')
    # Create the directories
    #os.makedirs(directory_main, exist_ok=True)
    os.makedirs(directory_log, exist_ok=True)
    
    file_node_1 = directory_log+"/blockchain_"+str(1)+".csv"
    isExist = os.path.exists(file_node_1)

    log_node_1 = directory_log+"/node_"+str(1)+".log"
    isExistLog = os.path.exists(log_node_1)
    node_max_len = 100

    nod = no_of_node_input(node_max_len)
    nodi = nod + 1

    """DEFINED TRANSACTION POOL DATA NO NEED TO PRINT 

    transaction_pool_directory = open(directory_main+"/transaction_pool.log", "r")
    transaction_content = transaction_pool_directory.read()
    #transaction_pool_directory.close()

    """
    
    num_tran = input("Enter number of transaction : ")
    datarate = input("Enter Datarate (for OfdmRate - 6,9,12,18,24,36,48,54) : ")

    transaction_list = [i for i in range(0, int(num_tran))]
    transaction_list_len = len(transaction_list) #number of transactions 

    #transaction_list = ConvertToList(transaction_content)
    #transaction_list_len = len(transaction_list)

    f_node_list = []

    # print(f"Transactions from transaction pool: {transaction_content} \n")

    print("--------starting block chain---------- \n")
    transaction_pool = round_robin_gen_2(nod, transaction_list, f_node_list)
    print(f"Round Robin Transaction pool: {transaction_pool} \n")
    print(f"Round Robin Transaction list: {transaction_list} \n")

    transaction_pool_len = len(transaction_pool)
    transaction_pool_len_inc = transaction_pool_len + 1

    if not isExist:
        myblockchain = Blockchain()
        myblockchain.generate_genesis_block()
        main_chain = myblockchain.get_chain()

        for x in range(1, nodi):
            save(directory_log+"/blockchain_"+str(x)+".csv", main_chain)
    else:
        dl_chain = directory_log+"/blockchain_1.csv"
        chain_results = pd.read_csv(dl_chain)

        for x in range(1, nodi):
            if x in f_node_list:
                continue
            else:
                dl_chain_w = directory_log+"/blockchain_"+str(x)+".csv"
                chain_results.to_csv(dl_chain_w, index=False)

    if not isExistLog:
        for x in range(1, nodi):
            f = open(directory_log+"/node_"+str(x)+".log", "w")
            f.write('')
            f.close()

    f = (nod-1) / 3
    req_n = (2*f) + 1

    #Generate block chain and Get the block size 
    csvFilePath = directory_log+"/blockchain_1.csv"
    packetSize = GenerateBlockChainAndReturnBlockSize(transaction_pool_len, nod, transaction_pool, directory_log, nodi, req_n, transaction_list_len, f_node_list, datarate, csvFilePath)

    print("\nManupulating Network and Ready to colleact network data. Please wait")
    
    numberOfNode, packetSize, totalTP, avg_throughput, totalDelay, avg_delay, area, height = InitializeNetwork(nod,datarate, packetSize)
    
    #InsertNetworkData(numberOfNode, transaction_list_len, packetSize, totalTP, avg_throughput, totalDelay, avg_delay)
    if totalTP != 0 and totalDelay != 0:
        insert_network_data(numberOfNode, transaction_list_len, packetSize, totalTP, avg_throughput, totalDelay, avg_delay, area, height)
    else: 
        print("\nException------> Restart the program.")
    print("\nData inserted into NetworkData database table ----  Execution completed successully.")

    return nod, datarate, packetSize, directory_log, directory_networkdata, directory_secretKey




if __name__ == "__main__":
    
    nod, datarate, packetsize, blockchainDatadirectory, networkDatadirectory, secretKeydirectory = main()
    while True:    
        #main()
        print("\nDo you want to add more nodes to test? (Yes/No)")
        ans = input().lower()

        if ans == 'yes' or ans == 'y':            
            # Authentication 
            secret_key = generate_secret_key()
            #print("Generated secret key:", secret_key)
            save_secret_key_to_file(secret_key, secretKeydirectory)
            IsAuthenticated = authenticate_node(secretKeydirectory)

            if IsAuthenticated:
                #Generate blockchain 
                next_node_number = nod + 1
                create_BlockchainNode(blockchainDatadirectory, next_node_number)
                print("initiating  network")
                numberOfNode, packetSize, totalTP, avg_throughput, totalDelay, avg_delay, area, height = InitializeNetwork(next_node_number ,datarate, packetsize)
                totalNode = nod + 1 
                print(f"\nOperation Exucuted. Total number of node in the network: {totalNode}" )
            else:
                print(f"\nAuthentication failed. Incoming node failed to authenticate!" )
            
        else:
            source_dir = "/home/imran/ns-allinone-3.36.1/ns-3.36.1"
            target_dir = networkDatadirectory            
            extensions = ["xml", "pcap", "tr"]
            move_files(source_dir, target_dir, extensions)
            print(f"\nAll network files have been moved here: {networkDatadirectory}")
            print("Exiting Simulation...")
            sys.exit(0)
