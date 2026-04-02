#!/usr/bin/env python3
"""
Простой многопользовательский TCP-чат (сервер).
Запуск: python3 server.py [host] [port]
По умолчанию host='' (все интерфейсы), port=12000
"""
import socket
import threading
import sys

HOST = ''  # слушать все интерфейсы по умолчанию
PORT = 12000
if len(sys.argv) >= 2:
    HOST = sys.argv[1]
if len(sys.argv) >= 3:
    PORT = int(sys.argv[2])

clients_lock = threading.Lock()
clients = {}  # socket -> nickname

def broadcast(message: str, exclude_sock=None):
    """Отослать message (str) всем подключенным клиентам, кроме exclude_sock."""
    data = (message + '\n').encode('utf-8')
    with clients_lock:
        to_remove = []
        for sock in clients:
            if sock is exclude_sock:
                continue
            try:
                sock.sendall(data)
            except Exception:
                to_remove.append(sock)
        # удаляем отсоединившиеся
        for s in to_remove:
            nickname = clients.pop(s, None)
            try:
                s.close()
            except:
                pass
            if nickname:
                print(f"Клиент {nickname} отключился (ошибка отправки).")

def handle_client(conn: socket.socket, addr):
    """Обработчик соединения: сначала читаем ник, потом поток сообщений."""
    print(f"Подключен: {addr}")
    conn.settimeout(None)
    buffer = ""
    nickname = None
    try:
        # Ожидаем, что клиент первым пришлёт никнейм как отдельную строку
        while True:
            data = conn.recv(1024)
            print(data)
            if not data:
                # клиент закрыл соединение до отправки ника
                conn.close()
                return
            buffer += data.decode('utf-8', errors='replace')
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                nickname = line.strip()
                if nickname == "":
                    nickname = f"{addr[0]}:{addr[1]}"
                break

        with clients_lock:
            clients[conn] = nickname
        broadcast(f"*** {nickname} присоединился к чату ***", exclude_sock=None)
        print(f"Новый ник: {nickname} от {addr}")

        # основной цикл чтения сообщений от клиента
        while True:
            # собираем строки, разделённые '\n'
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                text = line.strip()
            else:
                
                data = conn.recv(1024)
                print(data == "true")
                if not data:
                    # клиент закрыл соединение
                    break
                buffer += data.decode('utf-8', errors='replace')
                continue

            if text.lower() == '/quit' or text.lower() == 'exit':
                break
            if text != "":
                broadcast(f"[{nickname}] {text}", exclude_sock=conn)

    except ConnectionResetError:
        pass
    except Exception as e:
        print("Ошибка в обработчике клиента:", e)
    finally:
        # очистка
        with clients_lock:
            if conn in clients:
                left_nick = clients.pop(conn)
            else:
                left_nick = nickname
        try:
            conn.close()
        except:
            pass
        if left_nick:
            broadcast(f"*** {left_nick} покинул(а) чат ***", exclude_sock=None)
            print(f"{left_nick} отключился")

def main():
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv.bind((HOST, PORT))
    serv.listen(5)
    print(f"Сервер запущен на {(HOST if HOST else '0.0.0.0')}:{PORT}")
    try:
        while True:
            conn, addr = serv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nОстанавливаем сервер...")
    finally:
        with clients_lock:
            for s in list(clients.keys()):
                try:
                    s.close()
                except:
                    pass
            clients.clear()
        serv.close()

if __name__ == '__main__':
    main()
