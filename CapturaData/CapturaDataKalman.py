# -*- coding: utf-8 -*-
import time
from serial import Serial


# Classe KalmanFilter
class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, initial_value=0, initial_estimate_error=1):
        self.estimate = initial_value
        self.estimate_error = initial_estimate_error
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance

    def update(self, measurement):
        prediction = self.estimate
        prediction_error = self.estimate_error + self.process_variance

        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimate

# Inicialize os filtros de Kalman para X, Y e Z
kalman_x = KalmanFilter(process_variance=0.1, measurement_variance=100)
kalman_y = KalmanFilter(process_variance=0.1, measurement_variance=100)
kalman_z = KalmanFilter(process_variance=0.1, measurement_variance=100)

# Inicializa os filtros de Kalman
def initialize_kalman_filter():
    kalman_x.process_variance = 0
    kalman_y.process_variance = 0
    kalman_z.process_variance = 0

    kalman_x.measurement_variance = 100
    kalman_y.measurement_variance = 100
    kalman_z.measurement_variance = 100

    kalman_x.estimate = 0
    kalman_y.estimate = 0
    kalman_z.estimate = 0

    kalman_x.estimate_error = 1
    kalman_y.estimate_error = 1
    kalman_z.estimate_error = 1
    return kalman_x, kalman_y, kalman_z

kalman_x, kalman_y, kalman_z = initialize_kalman_filter()

# Inicializar a conexão serial
ser = Serial('COM6', 57600)

# Função para calcular o offset
def calculate_offset(samples, ser):
    sum_x, sum_y, sum_z = 0, 0, 0
    for _ in range(samples):
        serial_line = ser.readline().decode('utf-8').strip()
        values_str = serial_line.split(',')
        if len(values_str) == 3:
            try:
                values_float = [float(value.strip()) for value in values_str]
                sum_x += values_float[0]
                sum_y += values_float[1]
                sum_z += values_float[2]
            except ValueError:
                pass
    return sum_x / samples, sum_y / samples, sum_z / samples

# Calcular offset
offset_samples = 1000  # Número de amostras para calcular o offset
print("Iniciando Calibração para zerar os valores!")
offset_x, offset_y, offset_z = calculate_offset(offset_samples, ser)
print("Calibração para zerar os valores finalizada!")

data_x, data_y, data_z = [], [], []

n = 0
total_dados = 1000000  # 1 milhão de leituras
inicio = time.time()

try:
    for _ in range(total_dados):  # 1 milhão de leituras
        serial_line = ser.readline().decode('utf-8').strip()
        values_str = serial_line.split(',')
        if len(values_str) == 3:
            try:
                values_float = [float(value.strip()) for value in values_str]

                # Subtrair o offset e aplicar o filtro de Kalman
                # x_kmn = kalman_x.update(values_float[0] - offset_x)
                # y_kmn = kalman_y.update(values_float[1] - offset_y)
                # z_kmn = kalman_z.update(values_float[2] - offset_z)
                # Subtrair o offset e manter o dado bruto
                x_kmn = values_float[0] - offset_x
                y_kmn = values_float[1] - offset_y
                z_kmn = values_float[2] - offset_z

                # Armazenar os dados filtrados
                data_x.append(x_kmn)
                data_y.append(y_kmn)
                data_z.append(z_kmn)

                # Calcular tempo estimado
                elapsed_time = time.time() - inicio
                taxa_coleta = (n + 1) / elapsed_time
                estimativa_restante = (total_dados - (n + 1)) / taxa_coleta

                # Imprimir dados com o tempo estimado
                print(f"{n}\tET:\t{estimativa_restante:.2f} sec\t{x_kmn:+.4f}\t{y_kmn:+.4f}\t{z_kmn:+.4f}")

                n += 1

            except ValueError:
                pass

except KeyboardInterrupt:
    print("Interrupção manual detectada.")

finally:
    ser.close()
    print("Conexão serial fechada.")

with open('sensor_data GY-87_1.txt', 'w') as file:
    for x, y, z in zip(data_x, data_y, data_z):
        file.write(f"{x}, {y}, {z}\n")
    print("Arquivo gravado com sucesso!")
