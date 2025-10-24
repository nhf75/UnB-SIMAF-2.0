import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, CheckButtons
import csv
import queue  # Importe o módulo queue

MOVING_AVERAGE_SAMPLES = 80

def init_avg(line1_avg, line2_avg, line3_avg, current_text):
    line1_avg.set_data([], [])
    line2_avg.set_data([], [])
    line3_avg.set_data([], [])
    current_text.set_text('')
    return line1_avg, line2_avg, line3_avg, current_text

def run_animation_avg(q):
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    plt.subplots_adjust(bottom=0.25,top=0.9)

    line1_avg, = ax2.plot([], [], 'r-', label='X')
    line2_avg, = ax2.plot([], [], 'g-', label='Y')
    line3_avg, = ax2.plot([], [], 'b-', label='Z')

    x_data_avg, y_data_avg, z_data_avg = [], [], []  # Inicialize as listas aqui

    # Criar texto para exibir os valores atuais
    current_text = ax2.text(0.02, 0.80, '', transform=ax2.transAxes)

    class MovingAverage:
        def __init__(self, window_size=MOVING_AVERAGE_SAMPLES):
            self.window_size = window_size
            self.data = []

        def update(self, new_value):
            self.data.append(new_value)
            if len(self.data) > self.window_size:
                self.data.pop(0)
            return np.mean(self.data[-self.window_size:])

    moving_avg_x = MovingAverage()
    moving_avg_y = MovingAverage()
    moving_avg_z = MovingAverage()

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

    # Sliders para os parâmetros da média móvel
    axcolor = 'lightgoldenrodyellow'
    ax_window_size = plt.axes([0.15, 0.01, 0.70, 0.03], facecolor=axcolor)
    s_window_size = Slider(ax_window_size, 'Samples', 1, 100, valinit=MOVING_AVERAGE_SAMPLES, valstep=1)

    def update(val):
        # Atualize os parâmetros da média móvel com os valores dos sliders
        moving_avg_x.window_size = int(s_window_size.val)
        moving_avg_y.window_size = int(s_window_size.val)
        moving_avg_z.window_size = int(s_window_size.val)        
        fig2.canvas.draw_idle()
    
    s_window_size.on_changed(update)

    # Slider para o PERÍODO DE TEMPO
    ax_time_period = plt.axes([0.15, 0.05, 0.70, 0.03], facecolor=axcolor)
    s_time_period = Slider(ax_time_period, 'Time(s)', 1, 300, valinit=100)
    time_period = [100]

    def update(val):
        time_period[0] = int(s_time_period.val)
        fig2.canvas.draw_idle()
    
    s_time_period.on_changed(update)

    def animate_moving_average(i):
        nonlocal x_data_avg, y_data_avg, z_data_avg
        try:
            x_val, y_val, z_val = q.get_nowait()
        except queue.Empty:
            return line1_avg, line2_avg, line3_avg, current_text

        x_avg = moving_avg_x.update(x_val)
        y_avg = moving_avg_y.update(y_val)
        z_avg = moving_avg_z.update(z_val)

        x_data_avg.append(x_avg)
        y_data_avg.append(y_avg)
        z_data_avg.append(z_avg)

        if salvar_dados[0] == False:  # Apenas salva se estiver "On"
            if len(x_data_avg) > time_period[0]:
                x_data_avg = x_data_avg[-time_period[0]:]
                y_data_avg = y_data_avg[-time_period[0]:]
                z_data_avg = z_data_avg[-time_period[0]:]   

        line1_avg.set_data(range(len(x_data_avg)), x_data_avg)
        line2_avg.set_data(range(len(y_data_avg)), y_data_avg)
        line3_avg.set_data(range(len(z_data_avg)), z_data_avg)

        # Ajusta os limites do gráfico para mostrar os últimos time_period[0] pontos
                # Adjust the plot limits to show the last time_period[0] points
        if len(x_data_avg) >= time_period[0]:
            ax2.set_xlim(len(x_data_avg) - time_period[0], len(x_data_avg))
        else:
            ax2.set_xlim(0, time_period[0])

        # Cálculo da variação delta
        if len(x_data_avg) > time_period[0]:
            index_period = len(x_data_avg) - time_period[0]
            delta_x = x_data_avg[-1] - x_data_avg[index_period]
            delta_y = y_data_avg[-1] - y_data_avg[index_period]
            delta_z = z_data_avg[-1] - z_data_avg[index_period]
            current_text.set_text(f'X: {x_avg:.4f}, ΔX: {delta_x:.4f}\nY: {y_avg:.4f}, ΔY: {delta_y:.4f}\nZ: {z_avg:.4f}, ΔZ: {delta_z:.4f}')
        else:
            current_text.set_text(f'X: {x_avg:.4f}\nY: {y_avg:.4f}\nZ: {z_avg:.4f}')

        return line1_avg, line2_avg, line3_avg, current_text

    # Function to save Moving Average data to CSV
    def save_moving_average_data_to_csv(event):
        filename = 'Moving_Average_Data.csv'
        path = 'ExportData/'
        adress = path + filename
        with open(adress, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['X Moving Average Data', 'Y Moving Average Data', 'Z Moving Average Data'])
            for x, y, z in zip(x_data_avg, y_data_avg, z_data_avg):
                csvwriter.writerow([x, y, z])
        print(f'Dados salvos em {adress}')

    # Add button to save data
    ax_save_button = plt.axes([0.81, 0.1, 0.15, 0.04])
    save_button = Button(ax_save_button, 'Save CSV', color=axcolor, hovercolor='0.975')
    save_button.on_clicked(save_moving_average_data_to_csv)

    # Configurações do plot
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-360, 360)
    ax2.set_title("Moving Averange Filter")
    ax2.set_xlabel("Samples")
    ax2.set_ylabel("Angles (degree)")
    ax2.legend()
    # Iniciar animação
    ani_avg = animation.FuncAnimation(fig2, animate_moving_average,
                                       init_func=lambda: init_avg(line1_avg, line2_avg, line3_avg, current_text),
                                         frames=1000, interval=.5, blit=True)
 
    plt.show()