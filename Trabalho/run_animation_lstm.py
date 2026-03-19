import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import os
import csv
from matplotlib.widgets import Slider, Button, CheckButtons
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import pickle
import numpy as np
import queue
import socket
import tkinter as tk
from tkinter import ttk

# Inicializa o contador de dados
data_counter = 10
modelos_disponiveis = []

# Função para carregar todos os modelos na pasta "Modelos/"
# Função para carregar todos os modelos na pasta "Modelos/"
def carregar_modelos():
    global modelos_disponiveis
    pasta_modelos = 'src/Trabalho/Modelos/'
    modelos_disponiveis = [f for f in os.listdir(pasta_modelos) if f.endswith('.keras')]
    if not modelos_disponiveis:
        print("No LSTM model found in the Models folder/")
        exit()
    print("Loaded Models:", modelos_disponiveis)
    
def carregar_modelo_compativel(caminho_modelo):
    try:
        # Tentativa padrão
        return load_model(caminho_modelo, compile=False)
    except (TypeError, ValueError) as e:
        print(f"Aviso: erro ao carregar modelo moderno:\n{e}")
        print("Tentando carregamento em modo legacy...")

        # Tentativa legacy
        try:
            from keras.saving.legacy.saved_model_load import load as legacy_load_model
            return legacy_load_model(caminho_modelo)
        except Exception as e_legacy:
            print(f"Erro no carregamento legacy:\n{e_legacy}")
            raise RuntimeError(f"Não foi possível carregar o modelo {caminho_modelo}")

def carregar_scaler():
    try:
        with open('src/Trabalho/Modelos/scaler.pkl', 'rb') as f:
            scalers = pickle.load(f)
        return scalers
    except FileNotFoundError as e:
        print(f"Erro ao carregar os scalers: {e}")
        raise

# Função para enviar dados para o Unity via Socket
def send_to_unity(data, counter):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        formatted_data = f"{counter}/{float(data[0]):.6f}/{float(data[1]):.6f}/{float(data[2]):.6f}"
        sock.sendto(formatted_data.encode('utf-8'), ('127.0.0.1', 65432))
        sock.close()
    except (socket.timeout, ConnectionRefusedError, ValueError) as e:
        print(f"Error sending data: {e}")

def run_animation_lstm(originalData, lstm_q):  # Adicione lstm_q como parâmetro
    # Carrega os modelos disponíveis
    carregar_modelos()
    # Carrega o scaler
    scaler = carregar_scaler()

    # Variável para armazenar o modelo atual
    modelo_atual = [modelos_disponiveis[0]]  # Inicialmente o primeiro modelo carregado
    model = carregar_modelo_compativel(os.path.join('src/Trabalho/Modelos', modelo_atual[0]))
    n_timesteps = 80  # Mesmo número de timesteps usado durante o treinamento
    fator_correcao = [1.0]  # Fator de correção inicial

    # Função para atualizar o modelo LSTM selecionado
    def selecionar_modelo(event):
        modelo_atual[0] = dropdown_var.get()
        print(f"Selected LSTM Model: {modelo_atual[0]}")
        # Carrega o novo modelo
        nonlocal model
        model = carregar_modelo_compativel(os.path.join('src/Trabalho/Modelos', modelo_atual[0]))

    # Configuração do gráfico
    fig, ax = plt.subplots(figsize=(6, 5))
    plt.subplots_adjust(bottom=0.25, top=0.9)
    ax.set_title('LSTM')
    ax.set_xlabel("Samples")
    ax.set_ylabel("Angles (degree)")
    ax.set_xlim(0, 100)
    ax.set_ylim(-360, 360)

    # Linhas dos dados brutos e corrigidos
    line_x, = ax.plot([], [], 'r.', label='X')
    line_y, = ax.plot([], [], 'g.', label='Y')
    line_z, = ax.plot([], [], 'b.', label='Z')
    line_x_corr, = ax.plot([], [], 'r-', label='X Corrigido')
    line_y_corr, = ax.plot([], [], 'g-', label='Y Corrigido')
    line_z_corr, = ax.plot([], [], 'b-', label='Z Corrigido')

    xOriginalData, yOriginalData, zOriginalData = [], [], []
    xLSTM_Data, yLSTM_Data, zLSTM_Data = [], [], []
    xLSTM_Data_Save, yLSTM_Data_Save, zLSTM_Data_Save = [], [], []
    current_text = ax.text(0.02, 0.85, '', transform=ax.transAxes)

    axcolor = 'lightgoldenrodyellow'
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
    #-----------------------------------------------------------
    # Adicionando slider para ajustar parâmetro FATOR DE CORREÇÃO
    ax_fator_correcao = plt.axes([0.15, 0.01, 0.70, 0.03], facecolor=axcolor)
    s_fator_correcao = Slider(ax_fator_correcao, 'FCorr', 0.1, 1.0, valinit=fator_correcao[0])

    def update_fator_correcao(val):
        fator_correcao[0] = s_fator_correcao.val
        fig.canvas.draw_idle()
    s_fator_correcao.on_changed(update_fator_correcao)
    #-----------------------------------------------------------
    
    # Adicionando slider para ajustar parâmetro PERIODO DE TEMPO
    ax_time_period = plt.axes([0.15, 0.05, 0.70, 0.03], facecolor=axcolor)
    s_time_period = Slider(ax_time_period, 'Time(s)', n_timesteps, 300, valinit=100) #o mínimo não pode ser menos que n_timesteps para não parar de fazer previsão
    time_period = [100]

    def update_time_period(val):
        time_period[0] = int(s_time_period.val)
    s_time_period.on_changed(update_time_period)
    #-----------------------------------------------------------
    # Configuração do Tkinter para o dropdown
    root = tk.Tk()
    root.title("LSTM Model Selection")
    root.geometry("350x100")
    
    dropdown_var = tk.StringVar(root)
    dropdown_var.set(modelos_disponiveis[0])  # Valor padrão do dropdown

    label = tk.Label(root, text="Select the Model:")
    label.pack()

    dropdown = ttk.Combobox(root, textvariable=dropdown_var, values=modelos_disponiveis, width = 43)
    dropdown.pack()
    dropdown.bind("<<ComboboxSelected>>", selecionar_modelo)
    #-----------------------------------------------------------


    # Inicializa o gráfico
    def init():
        line_x.set_data([], [])
        line_y.set_data([], [])
        line_z.set_data([], [])
        line_x_corr.set_data([], [])
        line_y_corr.set_data([], [])
        line_z_corr.set_data([], [])
        current_text.set_text('')
        return line_x, line_y, line_z, line_x_corr, line_y_corr, line_z_corr, current_text

    # Função de animação
    def animate_lstm(i):
        nonlocal xOriginalData, yOriginalData, zOriginalData
        nonlocal xLSTM_Data, yLSTM_Data, zLSTM_Data
        try:
            # Recebe os dados originais da fila
            x_val, y_val, z_val = originalData.get_nowait()
        except queue.Empty:
            return line_x, line_y, line_z, line_x_corr, line_y_corr, line_z_corr, current_text
                
        # Atualiza os dados brutos
        xOriginalData.append(x_val)
        yOriginalData.append(y_val)
        zOriginalData.append(z_val)

        # Limita os arrays aos últimos 100 elementos
        if len(xOriginalData) > time_period[0]:
            xOriginalData = xOriginalData[-time_period[0]:]
            yOriginalData = yOriginalData[-time_period[0]:]
            zOriginalData = zOriginalData[-time_period[0]:]

        corrected_values = None
        
        def SalvarDados(corrected_values):
            # Verifica se os dados devem ser salvos
            if salvar_dados[0]:  # Apenas salva se estiver "On"
                xLSTM_Data_Save.append(corrected_values[0])
                yLSTM_Data_Save.append(corrected_values[1])
                zLSTM_Data_Save.append(corrected_values[2])
            else:  # Limpa os arrays caso esteja "Off"
                xLSTM_Data_Save.clear()
                yLSTM_Data_Save.clear()
                zLSTM_Data_Save.clear()
                
        # Processar os dados com o LSTM quando houver dados suficientes
        if len(xOriginalData) >= n_timesteps:
            input_sensor = np.array([
                xOriginalData[-n_timesteps:],
                yOriginalData[-n_timesteps:],
                zOriginalData[-n_timesteps:]]).T
            input_sensor_df = pd.DataFrame(input_sensor, columns=['X', 'Y', 'Z'])
            input_sensor_normalized = scaler.transform(input_sensor_df)
            input_sensor_normalized = input_sensor_normalized.reshape(1, n_timesteps, 3)
            # Faz a previsão do erro
            predicted_error = model.predict(input_sensor_normalized, verbose=0)[0]

            # Inverte a normalização da saída
            predicted_error_df = pd.DataFrame(predicted_error.reshape(1, -1), columns=['X', 'Y', 'Z'])
            predicted_error = scaler.inverse_transform(predicted_error_df)[0]

            # APLICA A CORREÇÃO *************************************************************************
            corrected_values = np.array([x_val, y_val, z_val]) - (predicted_error * fator_correcao[0])
            # APLICA A CORREÇÃO *************************************************************************

            # Atualiza os dados corrigidos
            xLSTM_Data.append(corrected_values[0])
            yLSTM_Data.append(corrected_values[1])
            zLSTM_Data.append(corrected_values[2])

            # **ADICIONE ESTA LINHA: Envia os valores corrigidos para a fila**
            lstm_q.put((corrected_values[0], corrected_values[1], corrected_values[2]))

            if len(xLSTM_Data) > time_period[0]:
                xLSTM_Data = xLSTM_Data[-time_period[0]:]
                yLSTM_Data = yLSTM_Data[-time_period[0]:]
                zLSTM_Data = zLSTM_Data[-time_period[0]:]

            send_to_unity(corrected_values, data_counter)
        else:
            xLSTM_Data.append(x_val)
            yLSTM_Data.append(y_val)
            zLSTM_Data.append(z_val)
            
            # **ADICIONE ESTA LINHA: Envia os valores originais quando não há correção**
            lstm_q.put((x_val, y_val, z_val))
            
            if len(xLSTM_Data) > time_period[0]:
                xLSTM_Data = xLSTM_Data[-time_period[0]:]
                yLSTM_Data = yLSTM_Data[-time_period[0]:]
                zLSTM_Data = zLSTM_Data[-time_period[0]:]
        
        # Verifica se os dados devem ser salvos
        if corrected_values is not None:
            SalvarDados(corrected_values)

        # Atualiza os gráficos
        line_x.set_data(range(len(xOriginalData)), xOriginalData)
        line_y.set_data(range(len(yOriginalData)), yOriginalData)
        line_z.set_data(range(len(zOriginalData)), zOriginalData)
        line_x_corr.set_data(range(len(xLSTM_Data)), xLSTM_Data)
        line_y_corr.set_data(range(len(yLSTM_Data)), yLSTM_Data)
        line_z_corr.set_data(range(len(zLSTM_Data)), zLSTM_Data)

        # Ajusta os limites do gráfico para mostrar os últimos time_period[0] pontos
        if len(xLSTM_Data) >= time_period[0]:
            ax.set_xlim(len(xLSTM_Data) - time_period[0], len(xLSTM_Data))
        else:
            ax.set_xlim(0, time_period[0])

        # Calcula a taxa de variação angular (Delta)
        if len(xLSTM_Data) >= time_period[0]:
            index_period = len(xLSTM_Data) - time_period[0]
            delta_x = xLSTM_Data[-1] - xLSTM_Data[index_period]
            delta_y = yLSTM_Data[-1] - yLSTM_Data[index_period]
            delta_z = zLSTM_Data[-1] - zLSTM_Data[index_period]
            current_text.set_text(f'X: {xLSTM_Data[-1]:.4f}, ΔX: {delta_x:.4f}\nY: {yLSTM_Data[-1]:.4f}, ΔY: {delta_y:.4f}\nZ: {zLSTM_Data[-1]:.4f}, ΔZ: {delta_z:.4f}')
        else:
            current_text.set_text(f'X: {xLSTM_Data[-1]:.4f}\nY: {yLSTM_Data[-1]:.4f}\nZ: {zLSTM_Data[-1]:.4f}')

        return line_x, line_y, line_z, line_x_corr, line_y_corr, line_z_corr, current_text

    # Função para salvar os dados em um arquivo CSV
    def save_data_to_csv(event):
        # Nome do arquivo
        filename = 'LSTM_Data.csv'
        path = 'ExportData/'
        adress = path + filename
        # Salva os dados em um arquivo CSV
        with open(adress, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Cabeçalho
            csvwriter.writerow(['X LSTM Data', 'Y LSTM Data', 'Z LSTM Data'])
            # Escreve os dados linha por linha
            for x, y, z in zip(xLSTM_Data_Save, yLSTM_Data_Save, zLSTM_Data_Save):
                csvwriter.writerow([x, y, z])
        print(f'Dados salvos em {adress}')

    # Adiciona o botão para salvar os dados
    #                         | X |  Y  |largura|altura|
    ax_save_button = plt.axes([0.81, 0.1, 0.15, 0.04])  # Posição do botão na tela
    save_button = Button(ax_save_button, 'Save CSV', color=axcolor, hovercolor='0.975')

    # Conecta o botão à função de salvar os dados
    save_button.on_clicked(save_data_to_csv)

    # Inicia a animação e o loop do Tkinter
    ani_lstm = animation.FuncAnimation(fig, animate_lstm, init_func=init, frames=1000, interval=0.5, blit=True)
    plt.show()
    root.mainloop()