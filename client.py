# -*- coding: utf-8 -*-
import socket
from threading import Thread

HOST = "localhost"
PORT = 8080

def rcvMsg(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("---연결이 종료되었습니다---")
                break
            
            print('{}'.format(data.decode()))
        except Exception as e:
            print(f"---메시지 수신 중 오류 발생---\n{e}")
            break

def runChat():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        
        t = Thread(target=rcvMsg, args=(sock,))
        t.daemon = True
        t.start()

        while True:
            msg = input(">> ")
            if msg.strip() == '':
                continue
            if msg == '/q':
                sock.send(msg.encode())
                break
            sock.send(msg.encode())

        t.join()  # 수신 스레드 종료까지 대기

if __name__ == "__main__":
    runChat()
