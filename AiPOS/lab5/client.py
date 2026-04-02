#!/usr/bin/env python3
"""
TCP-клиент для чата.
Запуск: python3 client.py server_host [port]
По умолчанию port=12000
После запуска введите ник (отправится серверу как первая строка).
Команды:
  /quit  или  exit  -- выйти из чата
"""
import socket
import threading
import sys

if len(sys.argv) < 2:
    print("Использование: python3 client.py server_host [port]")
    sys.exit(1)

SERVER_HOST = sys.argv[1]
SERVER_PORT = int(sys.argv[2]) if len(sys.argv) >= 3 else 12000

def receive_loop(sock: socket.socket):
    """Поток, который постоянно читает данные от сервера и печатает."""
    buffer = ""
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("\nСоединение разорвано сервером.")
                break
            buffer += data.decode('utf-8', errors='replace')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                print(line)
    except Exception as e:
        print("\nОшибка при получении:", e)
    finally:
        try:
            sock.close()
        except:
            pass
        # завершаем программу
        sys.exit(0)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
    except Exception as e:
        print("Не удалось подключиться:", e)
        return

    nickname = input("Введите ваш никнейм: ").strip()
    if nickname == "":
        nickname = f"user-{sock.getsockname()[1]}"

    # отправляем ник как первая строка (разделитель '\n')
    try:
        sock.sendall((nickname + '\n').encode('utf-8'))
    except Exception as e:
        print("Ошибка при отправке ника:", e)
        sock.close()
        return

    # запускаем поток для приёма сообщений
    t = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    t.start()

    # основной цикл ввода сообщений
    try:
        while True:
            msg = input()
            if msg.lower() in ('/quit', 'exit'):
                try:
                    sock.sendall(('/quit\n').encode('utf-8'))
                except:
                    pass
                break
            # отправляем сообщение
            try:
                sock.sendall((msg + '\n').encode('utf-8'))
            except Exception as e:
                print("Ошибка при отправке:", e)
                break
    except KeyboardInterrupt:
        print("\nВыход...")
    finally:
        try:
            sock.close()
        except:
            pass
        sys.exit(0)

if __name__ == '__main__':
    main()
