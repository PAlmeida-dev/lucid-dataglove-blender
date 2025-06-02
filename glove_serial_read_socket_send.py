import serial
import socket
import re
import time  # Importa o módulo time

# Replace with your actual serial port and baud rate
SERIAL_PORT = 'COM5'   # e.g., 'COM3' on Windows or '/dev/ttyUSB0' on Linux
BAUD_RATE = 115200
HOST = '127.0.0.1'
PORT = 65432

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)

previous_time = time.perf_counter()  # Tempo da leitura anterior com alta precisão

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                current_time = time.perf_counter()
                delta_time = current_time - previous_time
                previous_time = current_time

                print(f"Tempo entre leituras: {delta_time * 1000:.3f} ms")  # Mostra em milissegundos

                matches = re.findall(r'([A-Z])(\d+)', line)
                data = {label: int(value) for label, value in matches if label in 'ABCDE'}
                print(data)
                message = ",".join(f"{k}:{v}" for k, v in data.items())
                sock.sendto(message.encode(), (HOST, PORT))
        except Exception as e:
            print("Erro:", e)
