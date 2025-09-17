from datetime import datetime
import sqlite3
import os.path



def InserGraphData(node, packet_size, delay, throughput, num_transaction, datarate):

    #BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    #db_path = os.path.join(BASE_DIR, "throughput_delay_data.db")
    #with sqlite3.connect(db_path) as db:


    conn = sqlite3.connect('/home/isuvo/ns-allinone-3.36.1/ns-3.36.1/scratch/throughput_delay_data.db')
    cursor = conn.cursor()
    data_to_insert = (node, packet_size, delay, throughput, num_transaction, datarate)
    cursor.execute('INSERT INTO MultipleDatarate (node, packet_size, delay, throughput, num_transaction, datarate) VALUES (?, ?, ?, ?, ?, ?)', (data_to_insert))
   
    conn.commit()
    conn.close()
    
def check_duplicate_data(node, packet_size):
    conn = sqlite3.connect('throughput_delay_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM NetFixTransaction WHERE node = ? AND packet_size = ?', (node, packet_size))
    result = cursor.fetchone()
    
    conn.close()
    
    return result is not None


def insert_network_data(number_of_nodes, number_of_transactions, packet_size, total_throughput, avg_throughput, total_delay, avg_delay, area, height):
    # Connect to the SQLite database
    conn = sqlite3.connect('/home/imran/ns-allinone-3.36.1/ns-3.36.1/scratch/throughput_delay_data.db', timeout=10)
    cursor = conn.cursor()

    # Create the NetworkData table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NetworkData (
            NumberOfNodes INTEGER,
            NumberOfTransactions INTEGER,
            PacketSize INTEGER,
            TotalThroughput REAL,
            AvgThroughput REAL,
            TotalDelay REAL,
            AvgDelay REAL,
            Area REAL,
            Height REAL,
            DateTime TEXT
        )
    ''')

    # Get the current date and time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert the data into the NetworkData table
    cursor.execute('''
        INSERT INTO NetworkData (NumberOfNodes, NumberOfTransactions, PacketSize, TotalThroughput, AvgThroughput, TotalDelay, AvgDelay, Area, Height, DateTime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (number_of_nodes, number_of_transactions, packet_size, total_throughput, avg_throughput, total_delay, avg_delay, area, height, current_time))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def insert_blockchain_data(number_of_nodes, number_of_transactions, total_throughput, avg_delay, datarate):
    # Connect to the SQLite database
    conn = sqlite3.connect('/home/imran/ns-allinone-3.36.1/ns-3.36.1/scratch/throughput_delay_data.db', timeout=10)
    cursor = conn.cursor()

    # Create the BlockchainData table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BlockChainData (
            DataRate INTEGER,       
            NumberOfNodes INTEGER,
            NumberOfTransactions INTEGER,
            TotalThroughput REAL,
            AvgDelay REAL,
            CurrentTime TEXT
        )
    ''')

    # Get the current date and time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert the data into the BlockchainData table
    cursor.execute('''
        INSERT INTO BlockChainData (DataRate, NumberOfNodes, NumberOfTransactions, TotalThroughput, AvgDelay, CurrentTime)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datarate, number_of_nodes, number_of_transactions, total_throughput, avg_delay, current_time))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
