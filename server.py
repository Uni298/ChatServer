import socket
import threading
import json
import time
from datetime import datetime

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.usernames = {}
        self.running = True
        
    def start_server(self):
        """サーバーを起動する"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"サーバーが起動しました {self.host}:{self.port}")
            print("サーバーを停止するには 'stop' と入力してください")
            
            # サーバー停止用のスレッド
            stop_thread = threading.Thread(target=self.stop_listener, daemon=True)
            stop_thread.start()
            
            # クライアント接続待機
            self.accept_clients()
            
        except Exception as e:
            print(f"サーバー起動エラー: {e}")
        finally:
            self.server_socket.close()
    
    def stop_listener(self):
        """サーバー停止コマンドを監視する"""
        while self.running:
            cmd = input()
            if cmd.lower() == 'stop':
                self.broadcast_message("SERVER", "サーバーが停止します")
                self.running = False
                self.server_socket.close()
                break
    
    def accept_clients(self):
        """クライアントの接続を受け付ける"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"新しい接続: {address}")
                
                # 新しいクライアント用のスレッドを開始
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except OSError:
                break
    
    def handle_client(self, client_socket, address):
        """クライアントのメッセージを処理する"""
        username = None
        
        try:
            # ユーザー名の受信
            username_data = client_socket.recv(1024).decode('utf-8')
            if username_data:
                join_data = json.loads(username_data)
                username = join_data.get('username', 'Unknown')
                
                # ユーザー名の重複チェック
                original_username = username
                counter = 1
                while username in self.usernames.values():
                    username = f"{original_username}_{counter}"
                    counter += 1
                
                self.usernames[client_socket] = username
                self.clients.append(client_socket)
                
                print(f"{username} が参加しました")
                self.broadcast_message("SERVER", f"{username} が参加しました")
                
                # 参加メッセージを送信
                welcome_msg = {
                    'type': 'system',
                    'username': 'SERVER',
                    'message': f'チャットに参加しました。現在の参加者: {len(self.clients)}人',
                    'timestamp': self.get_timestamp()
                }
                client_socket.send(json.dumps(welcome_msg).encode('utf-8'))
            
            # メッセージ受信ループ
            while self.running:
                try:
                    message_data = client_socket.recv(1024).decode('utf-8')
                    if not message_data:
                        break
                    
                    data = json.loads(message_data)
                    message_type = data.get('type', 'message')
                    
                    if message_type == 'message':
                        username = self.usernames.get(client_socket, 'Unknown')
                        message = data.get('message', '')
                        
                        print(f"{username}: {message}")
                        self.broadcast_message(username, message)
                        
                except (json.JSONDecodeError, ConnectionResetError):
                    break
                    
        except Exception as e:
            print(f"クライアント処理エラー: {e}")
        finally:
            # クライアント切断処理
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                if client_socket in self.usernames:
                    username = self.usernames[client_socket]
                    del self.usernames[client_socket]
                    print(f"{username} が退出しました")
                    self.broadcast_message("SERVER", f"{username} が退出しました")
            client_socket.close()
    
    def broadcast_message(self, username, message):
        """全クライアントにメッセージを送信する"""
        message_data = {
            'type': 'message',
            'username': username,
            'message': message,
            'timestamp': self.get_timestamp()
        }
        
        data_str = json.dumps(message_data)
        disconnected_clients = []
        
        for client in self.clients:
            try:
                client.send(data_str.encode('utf-8'))
            except:
                disconnected_clients.append(client)
        
        # 切断されたクライアントを削除
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
            if client in self.usernames:
                del self.usernames[client]
    
    def get_timestamp(self):
        """現在のタイムスタンプを取得"""
        return datetime.now().strftime("%H:%M:%S")
    
    def stop_server(self):
        """サーバーを停止する"""
        self.running = False
        for client in self.clients:
            client.close()
        self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start_server()
