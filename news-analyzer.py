import json
import socket
import traceback

AWS_EC2_IP = "18.224.137.35"

def processMessageIfPossible(buffer):
	while True:
		if not buffer:
			return buffer
		else:
			firstBracketIdx = buffer.find("{")
			if firstBracketIdx == -1:
				return buffer
			nextBracketIdx = buffer.find("}")
			if nextBracketIdx != -1:
				completeMessage = buffer[firstBracketIdx:nextBracketIdx+1]
				print(json.loads(completeMessage))
				buffer = buffer[nextBracketIdx+1:]
			else:
				return buffer

def analyzeNews():
	sockValid = False
	buffer = ""
	while True:
		if sockValid:
			try:
				data = sock.recv(1024)
				if not data:
					sockValid = False
					sock.close()
				else:
					buffer += data.decode()
					buffer = processMessageIfPossible(buffer)
			except Exception as e:
				sockValid = False
				sock.close()
				traceback.print_exc()
		else:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect((AWS_EC2_IP, 23456))
				sockValid = True
			except Exception as e:
				sock.close()
				traceback.print_exc()

analyzeNews()
