import glob
import os
import csv
from hashlib import sha256
import secrets
import shutil
import string


# check if dir exist if not create it
def check_dir(file_name):
    directory = os.path.dirname(file_name)
    # print(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)


def save(file_name, records):
    check_dir(file_name)
    csv_file = open(file_name, 'w+')
    csvWriter = csv.writer(csv_file, delimiter=',')
    count = 0
    for record in records:
        csvWriter.writerow([record])
        count += 1

    # print(count, " record saved to ",file_name)
    return count


def save_um(file_name, record):
    check_dir(file_name)
    csv_file = open(file_name, 'w+')
    csvWriter = csv.writer(csv_file)
    csvWriter.writerow([record])


def read_um(filename):
    if os.stat(filename).st_size == 0:
        row = ''
        return row
    else:
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            row1 = next(reader)
            return row1[0]


def empty_file(filename):
    f = open(filename, "w+")
    f.close()


def empty_first_line(filename):
    csv_file_name = filename

    file = open(csv_file_name)
    csvreader = csv.reader(file)

    # # store headers and rows
    # header = next(csvreader)

    # ignore first row 
    next(csvreader)

    # store other rows
    rows = []
    for row in csvreader:
        rows.append(row)

    file.close()

    with open(csv_file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        # # write the header
        # writer.writerow(header)

        # write multiple rows
        writer.writerows(rows)


# manual add delay        
def SHA256(text):
    return sha256(text.encode("ascii")).hexdigest()


def no_of_node_input(node_max_len):
    while True:
        try:
            nod = int(input('number of node: '))
        except ValueError:
            print("please inter number only")
            continue

        if nod > node_max_len:
            print(f"max. length is {node_max_len}")
            continue
        else:
            return nod


def y_n_input():
    while True:
        y_n = input('Do you want to continue: [Y/N]- ')
        y_n = y_n.lower()

        if y_n == 'y' or y_n == 'n':
            return y_n
        else:
            print(f"value must be Y or N")
            continue


def proposer_input(node_max_len):
    while True:
        try:
            nod = int(input('proposer node: '))
        except ValueError:
            print("please inter number only")
            continue

        if nod > int(node_max_len):
            print(f"proposer node cannot be more then   {node_max_len}")
            continue
        else:
            return nod


def transaction_node_input(node_max_len):
    while True:
        try:
            nod = int(input('transaction from which node: '))
        except ValueError:
            print("please inter number only")
            continue

        if nod > node_max_len:
            print(f"max. length is {node_max_len}")
            continue
        else:
            return nod


def filter_list(full_list, excludes):
    s = set(excludes)
    return (x for x in full_list if x not in s)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def round_robin_gen(a, b):
    matches = []

    b_len = len(b)
    b_len = b_len + 1

    if a > b_len:
        for i in range(1, b_len):
            i_less = i - 1
            matches.append(f"{i}-{b[i_less]}")
            print()
    else:
        x = list(divide_chunks(b, a))
        # print(x)
        x_len = len(x)

        for i in range(x_len):
            # print(x[i])
            x_i_len = len(x[i])
            x_i_len = x_i_len + 1
            for j in range(1, x_i_len):
                j_less = j - 1
                matches.append(f"{j}-{x[i][j_less]}")

    return matches


def round_robin_gen_2(nod, transaction_list, f_node_list):
    matches = []

    transaction_list_len = len(transaction_list)
    transaction_list_len = transaction_list_len + 1

    # node list create
    nodi = nod + 1
    node_list = []
    for i in range(1, nodi):
        if i in f_node_list:
            continue
        else:
            node_list.append(i)

    node_list_len = len(node_list)
    node_list_len = node_list_len - 1

    n = 0

    for i in range(1, transaction_list_len):
        i_less = i - 1
        n_less = n

        if n_less >= node_list_len:
            n = 0
        else:
            n = n + 1

        p = n_less

        matches.append(f"{node_list[p]}-{transaction_list[i_less]}")

    return matches


def round_robin_gen_for_single_transaction(number_of_node, transaction_data):
    matches = []
    number_of_node_inc = number_of_node + 1

    for i in range(1, number_of_node_inc):
        matches.append(f"{i}-{transaction_data}")
    return matches


transactions = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']


# transactions = ["a","b","c","d"]        

def ConvertToList(string):
    #li = list(string.split(","))
    li = [item.strip() for item in string.split(",")]
    return li

COUNTER_FILE = "run_counter.txt"
def get_next_run_id():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as f:
            f.write('1')
        return 1
    else:
        with open(COUNTER_FILE, 'r+') as f:
            run_id = int(f.read().strip())
            next_run_id = run_id + 1
            f.seek(0)
            f.write(str(next_run_id))
        return next_run_id
    

def move_files(source_dir, target_dir, extensions):
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Move each file with the specified extensions
    for ext in extensions:
        pattern = os.path.join(source_dir, f"*.{ext}")
        files = glob.glob(pattern)
        for file in files:
            shutil.move(file, target_dir)
            print(f"Moved {file} to {target_dir}")
            
def generate_secret_key(length=32):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # secrets module
    secret_key = ''.join(secrets.choice(alphabet) for i in range(length))
    return secret_key

def save_secret_key_to_file(secret_key, directory, filename="secret_key.txt"):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as f:
        f.write(secret_key)
    print(f"\nSecret key saved to {file_path}")

def create_BlockchainNode(directory, nodeNumber):
    blockDatafileName = "/blockchain_1.csv"
    logfileName = "/node_1.log"
    directoryFile = directory + blockDatafileName
    directoryLogFile = directory + logfileName
    # Check if the file exists
    if not os.path.isfile(directoryFile):
        print(f"The file {directoryFile} does not exist.")
        return
    
    if not os.path.isfile(directoryLogFile):
        print(f"The log file {directoryLogFile} does not exist.")
        return
    
  # Construct the new file paths
    new_file_path = os.path.join(directory, f"blockchain_{str(nodeNumber)}.csv")
    new_log_file_path = os.path.join(directory, f"node_{str(nodeNumber)}.log")
    
    # Copy and rename the files
    shutil.copyfile(directoryFile, new_file_path)
    shutil.copyfile(directoryLogFile, new_log_file_path)

    print("\nNode added in the blockchain node cluster.")
        