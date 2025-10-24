# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, CheckButtons
import queue  # Importe o módulo queue
import csv

def init_raw(line1_raw, line2_raw, line3_raw, current_text):
    line1_raw.set_data([], [])
    line2_raw.set_data([], [])
    line3_raw.set_data([], [])
    current_text.set_text('')
    return line1_raw, line2_raw, line3_raw, current_text

def run_animation_raw(q):
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    plt.subplots_adjust(bottom=0.25,top=0.9)
    line1_raw, = ax1.plot([], [], 'r-', label='X')
    line2_raw, = ax1.plot([], [], 'g-', label='Y')
    line3_raw, = ax1.plot([], [], 'b-', label='Z')

    x_data_raw, y_data_raw, z_data_raw = [], [], []  # Inicialize as listas aqui

    # Criar texto para exibir os valores atuais
    current_text = ax1.text(0.02, 0.85, '', transform=ax1.transAxes)

    # Função para alternar entre salvar e não salvar os dados
    # Iniciar com salvar_dados como True
    salvar_dados = [True]
    def toggle_save(label):
        salvar_dados[0] = not salvar_dados[0]
        print("Save Data:", "On" if salvar_dados[0] else "Off")

    # Adicionando a caixa de marcar
    ax_checkbox = plt.axes([0.1, 0.1, 0.23, 0.06])  # Posição da caixa de marcar
    check_button = CheckButtons(ax_checkbox, ['Save Data'], [salvar_dados[0]])
    check_button.on_clicked(toggle_save)

    def animate_raw_data(i):
        nonlocal  x_data_raw, y_data_raw, z_data_raw
        try:
            x_val, y_val, z_val = q.get_nowait()
            x_data_raw.append(x_val)
            y_data_raw.append(y_val)
            z_data_raw.append(z_val)
        except queue.Empty:
            pass

        if salvar_dados[0] == False:  # Apenas salva se estiver "On"
            if len(x_data_raw) > 100:
                x_data_raw = x_data_raw[-100:]
                y_data_raw = y_data_raw[-100:]
                z_data_raw = z_data_raw[-100:]   

        line1_raw.set_data(range(len(x_data_raw)), x_data_raw)
        line2_raw.set_data(range(len(y_data_raw)), y_data_raw)
        line3_raw.set_data(range(len(z_data_raw)), z_data_raw)

        # Adjust the plot limits to show the last time_period[0] points
        if len(y_data_raw) >= 100:
            ax1.set_xlim(len(y_data_raw) - 100, len(y_data_raw))
        else:
            ax1.set_xlim(0, 100)
            
        # Atualizar texto com os valores atuais
        if x_data_raw and y_data_raw and z_data_raw:
            current_text.set_text(f'X: {x_data_raw[-1]:.4f}\nY: {y_data_raw[-1]:.4f}\nZ: {z_data_raw[-1]:.4f}')

        return line1_raw, line2_raw, line3_raw, current_text

    # Function to save raw data to CSV
    def save_raw_data_to_csv(event):
        filename = 'Raw_Data.csv'
        path = 'ExportData/'
        adress = path + filename
        with open(adress, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['X Raw Data', 'Y Raw Data', 'Z Raw Data'])
            for x, y, z in zip(x_data_raw, y_data_raw, z_data_raw):
                csvwriter.writerow([x, y, z])
        print(f'Dados salvos em {adress}')

    # Add button to save data
    ax_save_button = plt.axes([0.81, 0.1, 0.15, 0.04])
    save_button = Button(ax_save_button, 'Save CSV', color='lightgoldenrodyellow', hovercolor='0.975')
    save_button.on_clicked(save_raw_data_to_csv)


    ax1.set_ylim(-360, 360)
    ax1.set_title("IMU")
    ax1.set_xlabel("Samples")
    ax1.set_ylabel("Angles (degree)")
    ax1.legend()
    ani_raw = animation.FuncAnimation(fig1, lambda i: animate_raw_data(i),
                                       init_func=lambda: init_raw(line1_raw, line2_raw, line3_raw, current_text),
                                         frames=1000, interval=.5, blit=True)
 
    plt.show()
