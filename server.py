import socketserver
import threading

HOST = "localhost"
PORT = 8080
lock = threading.Lock()


class UserManager:
    """유저 등록/제거, 브로드캐스팅, 유저 커맨드 처리"""

    def __init__(self):
        self.users = {}  # 유저 정보(소켓 객체/ ip 주소) 관리

    def add_user(self, username, conn, addr):
        """중복된 닉네임 없을 때 유저 등록"""
        if username in self.users:
            conn.send('---중복된 아이디입니다.---'.encode())
            return None
            
        with lock:
            self.users[username] = (conn, addr) 

        # 새로운 유저 입장 공지
        self.send_message_to_all('---[{}]님이 입장했습니다---'.format(username))
        print(f'---채팅 중 유저---\n{list(self.users.keys())}')

        return username

    def remove_user(self, username):
        """유저 정보 제거 & 퇴장 공지"""
        if username not in self.users:
            return

        with lock:
            del self.users[username]

        # 유저 퇴장 공지
        self.send_message_to_all('[{}]님이 퇴장했습니다.'.format(username))
        print(f'---채팅 중 유저---\n{list(self.users.keys())}')

    def message_handler(self, username, msg):
        """메세지 처리(명령어면 실행, 일반적인 메세지면 모든 유저들에게 송신)"""
        if not msg:
            return None

        if msg[0] != '/':
            self.send_message_to_all(f'[{username}]: {msg}')
            return None

        # 명령어 실행('/q')
        if msg.strip() == '/q':
            self.remove_user(username)
            return -1  # 연결 종료

    def send_message_to_all(self, msg):
        """모든 유저들에게 메시지 송신"""
        with lock:
            for conn, addr in self.users.values():
                try:
                    conn.send(msg.encode())
                except Exception as e:
                    print(f"---{addr}로의 송신 중 에러 발생---\n{e}")  # 송신 에러 처리


class TcpHandler(socketserver.BaseRequestHandler):
    """클라이언트 연결, 송수신 처리"""
    
    user_manager = UserManager()

    def handle(self):
        """새 클라이언트 연결 처리"""
        print(f'---{self.client_address[0]} 연결됨---')

        try:
            username = self.register_username()
            print(f"---새로운 유저 등록됨({username})---")

            while True:
                msg = self.request.recv(1024)
                if not msg:
                    break
                decoded_msg = msg.decode().strip()
                print(f'[{username}] {decoded_msg}')

                if self.user_manager.message_handler(username, decoded_msg) == -1:
                    self.request.close()
                    break

        except Exception as e:
            print(f"Error handling client {self.client_address}: {e}")
        finally:
            # 의도치 않게 연결 해제 됐을 때('/q' 안치고 연결 종료) 유저 제거
            self.user_manager.remove_user(username)

    def register_username(self):
        """닉네임 등록"""
        while True:
            self.request.send("새로운 닉네임: ".encode())
            username = self.request.recv(1024).decode().strip()
            if self.user_manager.add_user(username, self.request, self.client_address):
                return username


class ChattingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """한 프로세스 안 1대N 통신 처리(멀티쓰레드 기능)"""
    pass


def run_server():
    """소켓 서버 설정/실행/종료"""
    print('서버 시작')
    server = None
    try:
        server = ChattingServer((HOST, PORT), TcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('서버 종료')
        if server:
            server.shutdown()
            server.server_close()

run_server()
