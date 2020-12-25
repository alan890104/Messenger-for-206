import os
print("Check dependency")
os.system("pip install -r requirement.txt")
import io
import zlib
import json
import threading
import socket
import select
import queue
import winsound
from io import BytesIO
from threading import RLock
from datetime import datetime
from PIL import Image, ImageTk
from utility.encrypt_decript import Ende
import multiprocessing
from multiprocessing import Process
import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askdirectory,askopenfilename
from tkinter import messagebox

from file_transfer import file_client,file_server
# tcp port 9487 to send file
# tcp port 3000 -> chatroom server side

with open('settings.json','r',encoding='utf8') as G:
    Settings = json.load(G)

Process_Queue = multiprocessing.Queue(maxsize=-1)
usr_ip = {"Fgjyh":"140.113.67.124","David":"140.113.67.122","Alan":"140.113.67.121"}
ip_to_usr = {"140.113.67.124":"Fgjyh","140.113.67.122":"David","140.113.67.121":"Alan"}
LOCK = RLock()
my_ip = socket.gethostbyname_ex(socket.gethostname())[-1][-1]
if my_ip not in ip_to_usr:
    messagebox.showerror("警告","你沒有權限使用這個應用程式，請註冊你的帳號")



def play_sound(soundpath:str):
    if Settings['sound']==1:
        try:
            winsound.PlaySound(soundpath, winsound.SND_FILENAME|winsound.SND_NOSTOP|winsound.SND_ASYNC)
        except RuntimeError:
            pass

def Pack_header(content,time=None,types='normal',name=None):
    '''
    # header格式:
    {
        time: 23:59
        types: 'code' >  'file' > 'pic' > 'normal'
        name: Alan Fgjyh David
        content: string or bytes
    }
    '''
    if time==None: 
        time = datetime.now().strftime("%H:%M")
    if name==None:
        name = ip_to_usr[my_ip]
    if types=='pic':
        # 如果要傳送圖片，則content中會放port number
        pass
    if types=='file':
        # 如果要傳送檔案，則content中不放東西
        pass
    packing = {"time":time,"types":types,"name":name,"content":content}
    return json.dumps(packing)

def Unpack_header(json_obj):
    json_obj = json.loads(json_obj)
    time=json_obj['time']
    types = json_obj['types']
    name = json_obj['name']
    content = json_obj['content']
    if types=='code':
        with LOCK:
            if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
            Show_Msg.insert('end'," {}[{}]: {}".format(name,time,content),'code')  
            Show_Msg.see("end")   
    elif types=='file':
        print('開啟新的process接收file')
        Process(target=file_client,args=(usr_ip[name],Process_Queue,)).start()
    elif types=='pic':
        print('open a thread to receive picture.')
        threading.Thread(target=picture_client,args=(usr_ip[name],int(content),name,)).start()
    elif name==ip_to_usr[my_ip]:
        with LOCK:
            if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
            Show_Msg.insert('end'," {}[{}]: {}".format(name,time,content),'myself')  
            Show_Msg.see("end")
    elif types=='normal':
        with LOCK:
            if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
            Show_Msg.insert('end'," {}[{}]: {}".format(name,time,content))  
            Show_Msg.see("end")
        threading.Thread(target=play_sound,args=("sound\m1.wav",)).start()
    else:
        print('error '+json_obj)


class Chatting_server(threading.Thread):
    # Modify Show_Msg if receive some string
    def __init__(self):
        threading.Thread.__init__(self)
        self.status = "on"
        self.server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_soc.bind((my_ip, 3000))
        self.client_sock = [] # 存socket，負責傳送訊息(NO接收)
        self.inout = []
        self.Ende = Ende()
        if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
        Show_Msg.insert('end'," {}[{}]: {}".format("sys",datetime.now().strftime("%H:%M"),"您已經連線"),'system')  
        Show_Msg.see("end")
        

    def create_client_sock(self,ip=None):
        def judge(ipp,csa):
                for element in csa:
                    if ipp==element[0] and element[1]==3000:
                        return True
                return False
        if ip!=None:
            print("正在嘗試和指定的ip {}進行連線".format(ip))
            client_sock_addr = []
            for x in self.client_sock:
                try:
                    client_sock_addr.append(x.getpeername())
                except:
                    print('觀測到PEER關閉，即將開始回收port {}'.format(x))
                    x.close()
            if  self.status=="off" or judge(ip,client_sock_addr) or ip==self.server_soc.getsockname()[0]:
                print("無法建立已經存在的SOCKET",judge(ip,client_sock_addr))
                return
            with LOCK:
                tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tmp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:        
                    tmp.settimeout(1)
                    tmp.connect((ip,3000))
                except (socket.timeout,socket.error) as E:
                    print("error on",tmp,E)
                    tmp.close()
                else:
                    print("和{}建立連線成功".format(tmp.getpeername()))
                    tmp.setblocking(0)
                    self.inout.append(tmp)
                    self.client_sock.append(tmp)
        else:
            print("正在嘗試建立和所有人的連線")
            with LOCK:
                client_sock_addr=[]
                all_cs = self.client_sock
                for x in all_cs:
                    try:
                        client_sock_addr.append(x.getpeername())
                    except:
                        self.client_sock.remove(x)
                        print('觀測到PEER關閉，即將開始回收port {}'.format(x))
                        x.close()
                for x in ip_to_usr:
                    if self.status=="off": 
                        return # 不會讓它卡太久
                    if not judge(x,client_sock_addr) and x!=self.server_soc.getsockname()[0]: # 如果ip不在且ip不等於自己server的ip
                        tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tmp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        try:        
                            tmp.settimeout(0.5)
                            tmp.connect((x,3000))
                        except (socket.timeout,socket.error) as E:
                            print("error on",tmp,E)
                            tmp.close()
                        else:
                            tmp.setblocking(0)
                            print("和{}建立連線成功".format(tmp.getpeername()))
                            self.inout.append(tmp)
                            self.client_sock.append(tmp)
                    else:
                        print("失敗 client sock list:",self.client_sock)

    def send_to_every_one(self,msg,whos_ip=None):
        # whos_ip是一個ip, 傳送給指定的人
        if len(msg)>60000:
            messagebox.showerror("警告","一次不得傳送超過60000字")
            return
        if whos_ip==None:
            tmp_client_sock = self.client_sock
            for ss in tmp_client_sock:
                try:
                    if ss.getpeername()[0]!=self.server_soc.getsockname()[0]:
                        token = self.Ende.encrypt(msg.encode())
                        if len(token)>100:
                            token = zlib.compress(token,zlib.Z_BEST_COMPRESSION)
                        ss.sendall(token)
                except:
                    print("遠端{}已經不再運作".format(ss))
                    ss.close()
                    self.client_sock.remove(ss)
                    self.create_client_sock()
                    self.send_to_every_one(msg,whos_ip)
        else:
            tmp_client_sock = self.client_sock
            for ss in tmp_client_sock:
                try:
                    if ss.getpeername()[0]==whos_ip:
                        if ss.getpeername()[0]!=self.server_soc.getsockname()[0]:
                            token = self.Ende.encrypt(msg.encode())
                            if len(token)>100:
                                token = zlib.compress(token,zlib.Z_BEST_COMPRESSION)
                            ss.sendall(token)
                except:
                    print("遠端{}已經不再運作".format(ss))
                    ss.close()
                    self.client_sock.remove(ss)
                    self.create_client_sock()
                    self.send_to_every_one(msg,whos_ip)
                    


    def run(self):
        self.server_soc.setblocking(0)
        self.server_soc.listen(3)
        print("server open and listen on port",self.server_soc.getsockname())
        self.inout = [self.server_soc]
        for s in self.client_sock:
            self.inout.append(s)
        while True:
            if self.status=="off":    
                print('Close CHATROOM')
                for goodbye in self.inout:
                    goodbye.close()
                self.client_sock.clear()
                self.inout.clear()
                break

            if not Process_Queue.empty(): # 傳送檔案結束會發送訊息
                ip,text = Process_Queue.get_nowait()   
                now = datetime.now().strftime("%H:%M")
                with LOCK:
                    if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
                    Show_Msg.insert('end'," {}[{}]: {}".format(ip_to_usr[ip],now,text),'system')
                    Show_Msg.see("end")                
                threading.Thread(target=play_sound,args=("sound\m2.wav",)).start()

            readible,_,_ = select.select(self.inout,[],[],1)
            for s in readible:
                print(s)
                if s==self.server_soc:
                    try:
                        client_socket,addrs = s.accept()
                    except BlockingIOError:
                        continue
                    else:
                        client_socket.setblocking(0)
                        if client_socket.getsockname()[0] not in ip_to_usr: 
                            print(client_socket,"沒有權限加入")
                            continue
                        self.inout.append(client_socket)
                        now = datetime.now().strftime("%H:%M")
                        print("client {}  connect ".format(client_socket))
                        with LOCK:
                            self.create_client_sock(ip=client_socket.getpeername()[0]) # 有人與你連線，你也試圖與他進行互聯
                            if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
                            Show_Msg.insert('end'," {}[{}]: {}來了!".format("sys",now,ip_to_usr[addrs[0]]),'system')
                            Show_Msg.see("end") 
                elif s in self.client_sock:
                    try:
                        msg = s.recv(600)
                    except BlockingIOError:
                        continue
                    except (ConnectionResetError,BrokenPipeError):
                        s.close()
                        self.inout.remove(s)
                    else:
                        if msg==b"":
                            print("remove from client sock")
                            s.close()
                            self.client_sock.remove(s)
                            self.inout.remove(s)
                        else:
                            print("Clinet sock {} 收到 {}".format(s,msg))
                else:
                    try:
                        msg = s.recv(60000)
                    except BlockingIOError:
                        continue
                    else:
                        if msg==b"":
                            print('遠方{}關閉'.format(s))
                            s.close()
                            self.inout.remove(s)
                            with LOCK:
                                if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n") 
                                Show_Msg.insert('end'," {}[{}]: {}離我們而去QQ".format("sys",now,ip_to_usr[addrs[0]]),'system')
                                Show_Msg.see("end")
                        else:
                            try:
                                Unpack_header(self.Ende.decrypt(msg).decode())
                            except:
                                zobj = zlib.decompressobj()
                                Unpack_header(self.Ende.decrypt(zobj.decompress(msg)).decode())
                


class App():
    def __init__(self, root):
        global font_setting,Send_Btn,Text_Entry,Add_file,which_ip,folder_path,Show_Msg
        font_setting = tkFont.Font(family='Microsoft JhengHei',size=12)
        self.name = ip_to_usr[my_ip]
        self.image = []
        #setting title
        root.title("file_transfer 2.0")
        #setting window size
        width=556
        height=701
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.configure(background='orange')
        root.geometry(alignstr)
        root.resizable(width=False, height=False)
        # 傳送按鈕
        Send_Btn=tk.Button(root)
        Send_Btn["bg"] = "#ffffff"
        Send_Btn["font"] = font_setting
        Send_Btn["fg"] = "#ff7800"
        Send_Btn["justify"] = "center"
        Send_Btn["text"] = "傳送"
        Send_Btn.place(x=440,y=650,width=108,height=39)
        Send_Btn["command"] = self.Send_Btn_command
        
        # 輸入欄位
        Text_Entry=tk.Text(root)
        y_scroll = tk.Scrollbar(root) # 顯示框的垂直scroll bar
        y_scroll.place(x=436,y=650,width=10,height=40)
        y_scroll.config(command=Text_Entry.yview)
        Text_Entry["bg"] = "#ffffff"
        Text_Entry["borderwidth"] = "3px"
        Text_Entry["font"] = font_setting
        Text_Entry["yscrollcommand"] = y_scroll.set
        Text_Entry["fg"] = "#000000"
        Text_Entry.place(x=70,y=650,width=366,height=40)
        Text_Entry.bind('<Control-s>',self.Send_Btn_command)
        # 傳送檔案
        which_ip = tk.StringVar() # ip
        which_ip.set("140.113.67.124")

        folder_path = tk.StringVar() # directory

        Add_file=tk.Button(root)
        Add_file["bg"] = "#efefef"
        Add_file["font"] = font_setting
        Add_file["fg"] = "#000000"
        Add_file["justify"] = "center"
        Add_file["text"] = "選擇.."
        Add_file.place(x=10,y=650,width=50,height=40)
        Add_file["command"] = self.Add_file_command
        # 顯示資料
        Show_Msg=tk.Text(root)
        Show_Msg.delete("1.0",'end')
                
        Vertical_scroll = tk.Scrollbar(root) # 顯示框的垂直scroll bar
        Vertical_scroll.place(x=536,y=60,width=10,height=582)
        Vertical_scroll.config(command=Show_Msg.yview)
         
        Show_Msg.tag_config('code', background="black", foreground="white",font=("Times New Roman", "12", "bold")) # code
        Show_Msg.tag_config('system', background="#f2e3bb", foreground="green") # 系統字體
        Show_Msg.tag_config('myself', background="#f2e3bb", foreground="red") # 讓自己的字更改顏色以區別
        Show_Msg.tag_raise("sel") # 把select的優先度上升 這樣就不會被其他蓋掉了 超關鍵
        Show_Msg["bg"] = "#f2e3bb"
        Show_Msg["borderwidth"] = "1px"
        Show_Msg["font"] = font_setting
        Show_Msg["fg"] = "#333333"
        Show_Msg["yscrollcommand"] = Vertical_scroll.set
        Show_Msg["wrap"] = tk.WORD
        Show_Msg.place(x=10,y=60,width=536,height=582)


        # 清除按鈕
        Clear_Btn=tk.Button(root)
        Clear_Btn["bg"] = "#ffffff"
        Clear_Btn["font"] = font_setting
        Clear_Btn["fg"] = "blue"
        Clear_Btn["justify"] = "center"
        Clear_Btn["text"] = "清除"
        Clear_Btn.place(x=428,y=20,width=108,height=40)
        Clear_Btn["command"] = self.clear_screen

        # 附加圖案或表情
        Insert_pic_Btn=tk.Button(root)
        Insert_pic_Btn["bg"] = "#ffffff"
        Insert_pic_Btn["font"] = font_setting
        Insert_pic_Btn["fg"] = "red"
        Insert_pic_Btn["justify"] = "center"
        Insert_pic_Btn["text"] = "附加"
        Insert_pic_Btn.place(x=10,y=20,width=108,height=40)
        Insert_pic_Btn["command"] = self.Insert_picture

        # 連線至其他人
        connect_Btn=tk.Button(root)
        connect_Btn["bg"] = "#ffffff"
        connect_Btn["font"] = font_setting
        connect_Btn["fg"] = "red"
        connect_Btn["justify"] = "center"
        connect_Btn["text"] = "重新連線"
        connect_Btn.place(x=118,y=20,width=108,height=40)
        connect_Btn["command"] = self.connect_to_other

        # 下線
        disconnect_Btn=tk.Button(root)
        disconnect_Btn["bg"] = "#ffffff"
        disconnect_Btn["font"] = font_setting
        disconnect_Btn["fg"] = "red"
        disconnect_Btn["justify"] = "center"
        disconnect_Btn["text"] = "下線"
        disconnect_Btn.place(x=226,y=20,width=108,height=40)
        disconnect_Btn["command"] = self.disconnect

    def disconnect(self):
        with LOCK:
            cht_ser.status="off"
        cht_ser.join()
        if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
        Show_Msg.insert('end'," {}[{}]: {}".format("sys",datetime.now().strftime("%H:%M"),"您已經關閉連線"),'system')  
        Show_Msg.see("end")
        messagebox.showinfo("提示","您已經離線")

    def connect_to_other(self):
        global cht_ser
        if not cht_ser.is_alive():
            with LOCK:
                cht_ser = Chatting_server()
                cht_ser.start()
        else:
            print('Thread is alive')

        # 檢查是否還有連線
        if len(cht_ser.client_sock)<2:
            cht_ser.create_client_sock()
        else:
            print('You can only connect two peers')
            
    
    def Insert_picture(self):
        # 允許使用者選擇圖片路徑或是選擇表情
        Top_pop = tk.Toplevel()
        Top_pop.focus_force()
        width=450
        height=300
        screenwidth = Top_pop.winfo_screenwidth()
        screenheight = Top_pop.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        Top_pop.geometry(alignstr)
        Top_pop.resizable(width=False, height=False)
        # 選擇要傳送給誰的LABEL
        lab_ask = tk.Label(Top_pop, text = '傳送圖片:', justify=tk.CENTER, width=50,font=font_setting)
        lab_ask.place(x=10, y=50, width=100, height=20)
        # 顯示選擇的路徑的顯示欄
        selected_path = tk.Text(Top_pop,width = 100,font=font_setting)
        selected_path.delete("1.0", 'end')
        selected_path.insert('end','')
        selected_path.place(x=130, y=50, width=240, height=30)
        # 按鈕以詢問路徑
        def ask_dir(panel,selected_path):
            selected_path.delete("1.0", 'end')
            reply = askopenfilename(parent=panel,title="請選擇一個檔案:")
            selected_path.insert('end',reply)
        tk.Button(Top_pop,text="...",command=lambda:ask_dir(Top_pop,selected_path),font=font_setting).place(x=380, y=50,width=20,height=30)
        # 確認按鈕
        def update_value(s_path,Top_pop):
            # 有字的時候更新啦
            if s_path!="":  
                # 確認圖片路徑有存在
                if os.path.exists(s_path):
                    now = datetime.now().strftime("%H:%M")
                    threading.Thread(target=picture_server,args=(s_path,)).start() # 開啟一個THREAD負責處理圖片傳送
                    with LOCK:
                        Show_Msg.insert('end',"\n {}[{}]:\n".format(self.name,now),'myself')
                        self.image.append(ImageTk.PhotoImage(Image.open(s_path).resize((300, 300))))
                        Show_Msg.image_create("end",image=self.image[-1])
                        Show_Msg.see("end")
                        print("OK")
                else:
                    messagebox.showerror("錯誤","路徑不存在")
            Top_pop.destroy()
            Top_pop.update()
        tk.Button(Top_pop,text="確認",command=lambda:update_value(selected_path.get("1.0","end").strip(),Top_pop),font=font_setting).place(x=225-20, y=250,width=40,height=30)


    def clear_screen(self):
        Show_Msg.delete("1.0", 'end')
        self.image.clear()
        Show_Msg.see("end")

    def Send_Btn_command(self,event=None):
        text = Text_Entry.get("1.0","end").strip()
        if len(text)>0: # 只有當有字的時候才會送出
            time = datetime.now().strftime("%H:%M")
            if text[:7]=='//code_':
                cht_ser.send_to_every_one(Pack_header(text[7:],time,'code'))
                with LOCK:
                    if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
                    Show_Msg.insert('end'," {}[{}]: {}".format(self.name,time,text[7:]),'code')  
                    Show_Msg.see("end")
            else:
                cht_ser.send_to_every_one(Pack_header(text,time,'normal'))
                with LOCK:
                    if len(Show_Msg.get("1.0","end").strip())>0: Show_Msg.insert('end',"\n")
                    Show_Msg.insert('end'," {}[{}]: {}".format(self.name,time,text),'myself')  
                    Show_Msg.see("end")
            with LOCK:
                Text_Entry.delete("1.0", 'end')
        else:
            print("send button")


    def Add_file_command(self):
        # 彈出視窗 
        Top_pop = tk.Toplevel()
        Top_pop.focus_force()
        width=450
        height=300
        screenwidth = Top_pop.winfo_screenwidth()
        screenheight = Top_pop.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        Top_pop.geometry(alignstr)
        Top_pop.resizable(width=False, height=False)
        # 選擇要傳送給誰
        lab_ask = tk.Label(Top_pop, text = '傳送檔案給:', justify=tk.CENTER, width=50,font=font_setting)
        lab_ask.place(x=10, y=100, width=100, height=20)

        for dis,usr_ in enumerate(usr_ip):
            rad = tk.Radiobutton(Top_pop, variable=which_ip, value=usr_ip[usr_],text=usr_,font=font_setting)
            rad.place(x=110+dis*90, y=95, width=100)

        # 選擇路徑
        lab_ask = tk.Label(Top_pop, text = '檔案路徑是:', justify=tk.CENTER, width=50,font=font_setting)
        lab_ask.place(x=10, y=150, width=100, height=20)
        # 顯示選擇的路徑
        selected_path = tk.Text(Top_pop,width = 100,font=font_setting)
        selected_path.delete("1.0", 'end')
        selected_path.insert('end','')
        selected_path.place(x=130, y=150, width=240, height=30)
        # 按鈕以詢問路徑
        def ask_dir(panel,selected_path):
            selected_path.delete("1.0", 'end')
            reply = askdirectory(parent=panel,title="請選擇一個資料夾:")
            selected_path.insert('end',reply)
        tk.Button(Top_pop,text="...",command=lambda:ask_dir(Top_pop,selected_path),font=font_setting).place(x=380, y=150,width=20,height=30)

        # 確認按鈕
        def update_value(s_path,Top_pop):
            # 有字的時候更新啦
            if s_path!="":  
                # 確認目錄有存在
                if os.path.exists(s_path):
                    folder_path.set(s_path)
                    now = datetime.now().strftime("%H:%M")
                    cht_ser.send_to_every_one(Pack_header('',types='file'),which_ip.get())
                    cht_ser.send_to_every_one(Pack_header('傳送了一個檔案給你!'),which_ip.get())
                    Process(target=file_server,args=(s_path,which_ip.get(),)).start()
                    text = "您傳送了一個檔案"
                    with LOCK:
                        Show_Msg.insert('end',"\n {}[{}]: {}".format("system",now,text),'system')
                        Show_Msg.see("end")
                else:
                    messagebox.showerror("錯誤","路徑不存在")
            Top_pop.destroy()
            Top_pop.update()

        tk.Button(Top_pop,text="確認",command=lambda:update_value(selected_path.get("1.0","end").strip(),Top_pop),font=font_setting).place(x=225-20, y=250,width=40,height=30)


# 接收圖片的
def picture_client(ip,port,name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((ip,port))
    s.settimeout(5)
    BUF=b""
    while True:
        try:
            data = s.recv(500)
            if not data:
                break
            BUF+=data
        except socket.timeout:
            pass
        else:
            with LOCK:
                Show_Msg.insert('end',"\n {}[{}]:\n".format(name,datetime.now().strftime("%H:%M")))
                app.image.append(ImageTk.PhotoImage(Image.open(io.BytesIO(BUF)).resize((300, 300))))
                Show_Msg.image_create("end",image=app.image[-1])
                Show_Msg.see("end")
            threading.Thread(target=play_sound,args=("sound\m1.wav",)).start()

# 接收傳送圖片請求的
def picture_server(path):
    if not cht_ser.is_alive():
        print('PICTURE CANNOT SEND , you need to connect')
    elif len(cht_ser.client_sock)==0:
        print('empty client socket')
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 0)) 
        pic_server_port = str(s.getsockname()[1])
        # 先告知對方SERVER3000即將開始傳送訊息
        cht_ser.send_to_every_one(Pack_header(pic_server_port,types='pic'))
        s.listen(2)
        s.settimeout(5)
        try:
            for _ in range(len(cht_ser.client_sock)):
                client_socket,_ = s.accept()
                threading.Thread(target=picture_server_handle,args=(path,client_socket,)).start()
                print('open thread')
        except socket.timeout:
            pass

# 主要來傳圖片的
def picture_server_handle(path,cs):
    with open(path,'rb') as G:
        while True:
            data = G.read(8192)
            if not data: break
            cs.sendall(data)
        cs.close()        

def on_closing(cht_ser):
    if messagebox.askokcancel("Quit", "你是否要離開?"):
        cht_ser.status = "off"
        cht_ser.join()
        root.destroy()

if __name__ == "__main__":
    global cht_ser,app
    root = tk.Tk()
    app = App(root)
    cht_ser = Chatting_server()
    cht_ser.create_client_sock()
    cht_ser.start()

    
    root.protocol("WM_DELETE_WINDOW", lambda:on_closing(cht_ser))
    root.mainloop()