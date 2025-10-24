import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, CheckButtons
import csv
import queue  # Importe o modulo queue

def init_kmn(line1_kmn, line2_kmn, line3_kmn, current_text):
    line1_kmn.set_data([], [])
    line2_kmn.set_data([], [])
    line3_kmn.set_data([], [])
    current_text.set_text('')
    return line1_kmn, line2_kmn, line3_kmn, current_text

def run_animation_kmn(q, kalman_q):
    fig3, ax3 = plt.subplots(figsize=(6, 5))
    plt.subplots_adjust(bottom=0.25,top=0.9)

    line1_kmn, = ax3.plot([], [], 'r-', label='X')
    line2_kmn, = ax3.plot([], [], 'g-', label='Y')
    line3_kmn, = ax3.plot([], [], 'b-', label='Z')

    x_data_kmn, y_data_kmn, z_data_kmn = [], [], []  # Inicialize as listas aqui


    axcolor = 'lightgoldenrodyellow'
    # Função para alternar entre salvar e não salvar os dados
    # Iniciar com salvar_dados como True
    salvar_dados = [True]
    def toggle_save(label):
        salvar_dados[0] = not salvar_dados[0]
        print("Save Data:", "On" if salvar_dados[0] else "Off")

    # Adicionando a caixa de marcar
    ax_checkbox = plt.axes([0.1, 0.14, 0.23, 0.06])
    check_button = CheckButtons(ax_checkbox, ['Save Data'], [salvar_dados[0]])
    check_button.on_clicked(toggle_save)

    # Adicionando slider para time_period
    ax_time_period = plt.axes([0.15, 0.09, 0.70, 0.03], facecolor=axcolor)
    s_time_period = Slider(ax_time_period, 'Time(s)', 1, 10000, valinit=100)

    time_period = [100]  # Lista para armazenar o valor do periodo selecionado no slider
    def update_time_period(val):
        time_period[0] = int(s_time_period.val)
    s_time_period.on_changed(update_time_period)

    # Criar texto para exibir os valores atuais
    current_text = ax3.text(0.02, 0.80, '', transform=ax3.transAxes)

    # Definição da classe KalmanFilter
    class KalmanFilter:
        # Inicializador da classe com parâmetros para o filtro de Kalman
        def __init__(self, D, M, Sigma_d, Sigma_m, x_0, Sigma_0):
            self.D = D          # Matriz de transição de estado
            self.M = M          # Matriz de medição
            self.Sigma_d = Sigma_d  # Covariância do processo
            self.Sigma_m = Sigma_m  # Covariância da medição
            self.x = x_0           # Valor inicial do estado
            self.Sigma = Sigma_0   # Covariância inicial do estado
    
        # Função de atualização do filtro de Kalman
        def update(self, y):
            # Predição
            x_pred = self.D @ self.x
            Sigma_pred = self.Sigma_d + self.D @ self.Sigma @ self.D.T

            # Correção                               |   Covariância predita no espaço de medição  |
            K = Sigma_pred @ self.M.T @ np.linalg.inv(self.M @ Sigma_pred @ self.M.T + self.Sigma_m)
            self.x = x_pred + K @ (y - self.M @ x_pred)
            self.Sigma = (np.identity(self.D.shape[0]) - K @ self.M) @ Sigma_pred

            return self.x[0]

    # Criação dos filtros de Kalman para X, Y e Z
    D = np.identity(1)#/.9  # Matriz de identidade
    M = np.identity(1)  # Matriz de identidade
    x_0 = np.array([0])  # Valor inicial do estado
    Sigma_0 = np.array([[1]])  # Covariância inicial do estado

    # Inicialização dos filtros com valores padrão
    kalman_x = KalmanFilter(D, M, 1, 10, x_0, Sigma_0)
    kalman_y = KalmanFilter(D, M, 1, 10, x_0, Sigma_0)
    kalman_z = KalmanFilter(D, M, 1, 10, x_0, Sigma_0)

    def animate_kalman_filter(i):
        nonlocal x_data_kmn, y_data_kmn, z_data_kmn
        try:
            x_val, y_val, z_val = q.get_nowait()
        except queue.Empty:
            return line1_kmn, line2_kmn, line3_kmn, current_text

        x_kmn = kalman_x.update(x_val)
        y_kmn = kalman_y.update(y_val)
        z_kmn = kalman_z.update(z_val)

        kalman_q.put((x_kmn, y_kmn, z_kmn))
        
        x_data_kmn.append(x_kmn)
        y_data_kmn.append(y_kmn)
        z_data_kmn.append(z_kmn)

        if salvar_dados[0] == False:  # Apenas salva se estiver "On"
            if len(x_data_kmn) > time_period[0]:
                x_data_kmn = x_data_kmn[-time_period[0]:]
                y_data_kmn = y_data_kmn[-time_period[0]:]
                z_data_kmn = z_data_kmn[-time_period[0]:]

        line1_kmn.set_data(range(len(x_data_kmn)), x_data_kmn)
        line2_kmn.set_data(range(len(y_data_kmn)), y_data_kmn)
        line3_kmn.set_data(range(len(z_data_kmn)), z_data_kmn)

        # Ajustar os limites do grafico para mostrar os ultimos 100 pontos
        if len(x_data_kmn) >= 100:
            ax3.set_xlim(len(x_data_kmn) - 100, len(x_data_kmn))
        else:
            ax3.set_xlim(0, 100)

        # Atualizar texto com os valores atuais
        current_text.set_text(f'X: {x_data_kmn[-1]:.4f}\nY: {y_data_kmn[-1]:.4f}\nZ: {z_data_kmn[-1]:.4f}')

        # Calculo da Taxa de variacao angular
        if len(x_data_kmn) > time_period[0]:
            index_period = len(x_data_kmn) - time_period[0]        
            delta_x = x_data_kmn[-1] - x_data_kmn[index_period]
            delta_y = y_data_kmn[-1] - y_data_kmn[index_period]
            delta_z = z_data_kmn[-1] - z_data_kmn[index_period]
            
            current_text.set_text(f'X: {x_data_kmn[-1]:.4f}, ΔX: {delta_x:.4f}\nY: {y_data_kmn[-1]:.4f}, ΔY: {delta_y:.4f}\nZ: {z_data_kmn[-1]:.4f}, ΔZ: {delta_z:.4f}')

        return line1_kmn, line2_kmn, line3_kmn, current_text


    # Criação dos sliders para ajustar os parâmetros do filtro de Kalman
    ax_process_var = plt.axes([0.15, 0.01, 0.70, 0.03], facecolor=axcolor)
    ax_measure_var = plt.axes([0.15, 0.05, 0.70, 0.03], facecolor=axcolor)

    s_process_var = Slider(ax_process_var, 'Process Var', 0.1, 10.0, valinit=1)
    s_measure_var = Slider(ax_measure_var, 'Samples', 1.0, 200.0, valinit=100)

    # Função para atualizar os valores dos filtros de Kalman com base nos sliders
    def update(val):
        kalman_x.Sigma_d = np.array([[s_process_var.val]])
        kalman_y.Sigma_d = np.array([[s_process_var.val]])
        kalman_z.Sigma_d = np.array([[s_process_var.val]])

        kalman_x.Sigma_m = np.array([[s_measure_var.val]])
        kalman_y.Sigma_m = np.array([[s_measure_var.val]])
        kalman_z.Sigma_m = np.array([[s_measure_var.val]])

        fig3.canvas.draw_idle()

    s_process_var.on_changed(update)
    s_measure_var.on_changed(update)

    # Atualiza os filtros de Kalman com os valores iniciais dos sliders
    update(None)

    # Function to save Kalman data to CSV
    def save_kalman_data_to_csv(event):
        filename = 'Kalman_Data.csv'
        path = 'ExportData/'
        adress = path + filename
        with open(adress, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['X Kalman Data', 'Y Kalman Data', 'Z Kalman Data'])
            for x, y, z in zip(x_data_kmn, y_data_kmn, z_data_kmn):
                csvwriter.writerow([x, y, z])
        print(f'Dados salvos em {adress}')

    # Add button to save data
    #                         | X |  Y  |largura|altura|
    ax_save_button = plt.axes([0.81, 0.14, 0.15, 0.04])
    save_button = Button(ax_save_button, 'Save CSV', color=axcolor, hovercolor='0.975')
    save_button.on_clicked(save_kalman_data_to_csv)

    # Fim dos sliders para todos os parametros do filtro de Kalman    
    ax3.set_xlim(0, 100)
    ax3.set_ylim(-360, 360)
    ax3.set_title("Kalman Filter")
    ax3.set_xlabel("Samples")
    ax3.set_ylabel("Angles (degree)")
    ax3.legend()
    ani_kmn = animation.FuncAnimation(fig3, lambda i: animate_kalman_filter(i), init_func=lambda: init_kmn(line1_kmn, line2_kmn, line3_kmn, current_text), frames=1000, interval=.5, blit=True)
 
    plt.show()