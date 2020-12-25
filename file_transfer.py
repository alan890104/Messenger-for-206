import socket
import os
from  datetime import datetime

def file_client(ip,Process_Queue):
    '''
    需要給SERVER的IP才能收檔案
    '''
    CHUNKSIZE = 1_000_000
    # 先建立一個資料夾
    new_folder = datetime.now().strftime("%Y%m%d-%H%M")
    os.makedirs(new_folder,exist_ok=True)
    sock = socket.socket()
    sock.settimeout(3)
    sock.connect((ip,5000))
    with sock,sock.makefile('rb') as clientfile:
        while True:
            try:
                raw = clientfile.readline()
                if not raw: break # no more files, server closed connection.

                filename = raw.strip().decode()
                length = int(clientfile.readline())
                print(f'Downloading {filename}...\n  Expecting {length:,} bytes...',end='',flush=True)

                path = os.path.join(new_folder,filename)
                os.makedirs(os.path.dirname(path),exist_ok=True)

                # Read the data in chunks so it can handle large files.
                with open(path,'wb') as f:
                    while length:
                        chunk = min(length,CHUNKSIZE)
                        data = clientfile.read(chunk)
                        if not data: break
                        f.write(data)
                        length -= len(data)
                    else: # only runs if while doesn't break and length==0
                        continue

                # socket was closed early.
                print('Incomplete')
                os.remove(new_folder) # remove directory
                break
            except socket.timeout:
                print('停止接收檔案')
                break
    Process_Queue.put([ip,'傳送檔案給你!'])

def file_server(main_directory,receiver_ip):
    CHUNKSIZE = 1_000_000

    sock = socket.socket()
    sock.settimeout(3)
    sock.bind(('',5000))
    sock.listen(1)

    while True:
        try:
            print('Waiting for a client...')
            client,address = sock.accept()
            print(f'Client joined from {address}')
            if address[0]!=receiver_ip:
                print('拒絕存取')
            else:
                with client:
                    for path,dirs,files in os.walk(main_directory):
                        for file in files:
                            filename = os.path.join(path,file)
                            relpath = os.path.relpath(filename,main_directory)
                            filesize = os.path.getsize(filename)

                            print(f'Sending {relpath}')

                            with open(filename,'rb') as f:
                                client.sendall(relpath.encode() + b'\n')
                                client.sendall(str(filesize).encode() + b'\n')

                                # Send the file in chunks so large files can be handled.
                                while True:
                                    data = f.read(CHUNKSIZE)
                                    if not data: break
                                    client.sendall(data)
                    print('檔案傳送完成.')
                    break
        except socket.timeout:
            print('停止傳送檔案')
            sock.close()
            break