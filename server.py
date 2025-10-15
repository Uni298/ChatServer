import socket
import threading

HOST = "0.0.0.0"
PORT = 50007
clients = []

def handle_client(conn, addr):
    print(f"接続: {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8")
            print(msg)
            broadcast(msg, conn)
        except:
            break
    conn.close()
    clients.remove(conn)
    print(f"切断: {addr}")

def broadcast(msg, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(msg.encode("utf-8"))
            except:
                pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"サーバー起動 {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
