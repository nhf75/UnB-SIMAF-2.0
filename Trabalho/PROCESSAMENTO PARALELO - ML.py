# -*- coding: utf-8 -*-
import serial
import multiprocessing
from multiprocessing import Process, Queue, Manager
import matplotlib
matplotlib.use('TkAgg')  # Escolha o backend apropriado
import run_animation_raw
import run_animation_avg
import run_animation_kmn
import run_animation_lstm
import tkinter as tk
import numpy as np

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def read_from_serial(q, offset, history):
    try:
        ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=1) # /dev/ttyACM0 OU /dev/ttyUSB0
        # ser.reset_input_buffer()
        # ser.reset_output_buffer()
        while True:
            try:
                serial_line = ser.readline().decode('utf-8').strip()
            except UnicodeDecodeError:
                serial_line = ser.readline().decode('latin1').strip()

            values = serial_line.split(', ')
            if len(values) == 3 and all(is_float(val) for val in    values):
                x, y, z = (float(values[0]), float(values[1]), float(values[2]))
                history.append((x, y, z))
                q.put((x - offset[0], y - offset[1], z - offset[2]))
                if len(history) > 1000:
                    history.pop(0)
            else:
                print("Step: ", serial_line)
    except KeyboardInterrupt:
        print("Leitura da serial interrompida.")
    finally:
        ser.close()
def calculate_offset(history_list):
    if not history_list:
        print("Nao ha dados suficientes para calcular os offsets")
        return [0, 0, 0]
    # Agora usa a lista para as operacoes subsequentes
    last_values = history_list[-100:] if len(history_list) >= 100 else history_list
    x_vals, y_vals, z_vals = zip(*last_values)
    return np.mean(x_vals), np.mean(y_vals), np.mean(z_vals)

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')  # method: spawn ou fork
    manager = Manager()
    q = Queue()
    kalman_q = Queue()  # Fila para os valores do Kalman
    history = manager.list()
    offset = manager.list([0, 0, 0])

    # ---- processos ---------------------------------------------------------
    reader = Process(target=read_from_serial, args=(q, offset, history))
    p1 = Process(target=run_animation_raw.run_animation_raw, args=(q,))
    p2 = Process(target=run_animation_avg.run_animation_avg, args=(q,))
    p3 = Process(target=run_animation_kmn.run_animation_kmn, args=(q, kalman_q))
    p4 = Process(target=run_animation_lstm.run_animation_lstm, args=(q,))    
    for p in (reader, p1, p2, p3, p4):
        p.start()

    # ---- Tkinter: hot-key Ctrl+M -------------------------------------------
    def on_ctrl_n(event=None):
        history_list = list(history)
        new_offset   = calculate_offset(history_list)
        offset[:]    = new_offset
        print("► Offset atualizado:", new_offset)
    
    root = tk.Tk()
    root.title("Em foco")                                  # título da janela
    root.geometry("250x120+100+100")          # janela mínima (pode ser minimizada) # root.withdraw()                    # oculta janela principal
    root.bind('<Control-n>', on_ctrl_n)
    # Texto interno
    label = tk.Label(root, text="Para offset, digite Ctrl + N", font=("Arial", 12))
    label.pack(expand=True, padx=10, pady=30)
    # opcional: manter minimizada
    # root.iconify()

    try:
        root.mainloop()                 # mantém aplicação viva
    except KeyboardInterrupt:
        print("Interrupção solicitada – encerrando.")

    # --- encerramento  -------------------------------------------------
    for p in (reader, p1, p2, p3, p4):
        p.join(timeout=1)        # evita bloqueio eterno 