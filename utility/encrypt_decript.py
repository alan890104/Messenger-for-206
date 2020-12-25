from cryptography.fernet import Fernet

class Ende():
    def __init__(self):
        try :
            self.key =  "GlsohVwGSNSwuKXx_uVLtaFPHCoRC4pdKC5BzkHD7yY=" # open('key.txt','rb').read()
        except FileExistsError: 
            self.key = self.generate_key()
    def encrypt(self,message: bytes) -> bytes:
        return Fernet(self.key).encrypt(message)
    def decrypt(self,token: bytes) -> bytes:
        return Fernet(self.key).decrypt(token,ttl=None)
    def generate_key(self):
        KEYS = Fernet.generate_key()
        with open('key.txt','wb') as F : F.write(KEYS)
        print("Your new key : ",KEYS.decode())
        return KEYS

# if __name__=='__main__':
#     mp = MSG_process()
#     encrypt_message = mp.encrypt("菜蔬為是低能兒".encode())
#     print(mp.decrypt(encrypt_message).decode())