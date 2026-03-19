import platform
import time
import numpy as np
import random

# Define if using dummy sensor data (True for testing, False for real sensor)
use_dummy_sensor = platform.system() == "Windows"  # Usar dados fictícios se estiver no Windows

if not use_dummy_sensor:
  try:
      import smbus2
  except ModuleNotFoundError:
      print("smbus2 não está instalado. Tentando instalar...")
      try:
          import subprocess
          import sys
          subprocess.check_call([sys.executable, "-m", "pip", "install", "smbus2"])
          import smbus2
      except subprocess.CalledProcessError as e:
          print(f"Erro ao instalar smbus2: {e}")
          raise  # Re-raise the exception to halt execution

# Endereço I2C do MPU6050
PWR_MGMT_1 = 0x6B
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
INT_ENABLE = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47
Device_Address = 0x68   # endereço do dispositivo

# Endereço I2C do HMC5883L
HMC5883L_ADDRESS = 0x1E
HMC5883L_CRA = 0x00
HMC5883L_CRB = 0x01
HMC5883L_MODE = 0x02
HMC5883L_DO_X_H = 0x03

if not use_dummy_sensor:
  # Inicializa o barramento I2C (adapte o número do barramento se necessário)
  try:
      bus = smbus2.SMBus(1)  # Tente usar o barramento 1
  except FileNotFoundError:
      print("Barramento I2C 1 não encontrado. Tentando barramento 0...")
      try:
          bus = smbus2.SMBus(0)  # Tente usar o barramento 0
      except Exception as e:
          print(f"Erro ao inicializar o barramento I2C: {e}")
          exit(1)

  def MPU_Init():
      bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
      bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
      bus.write_byte_data(Device_Address, CONFIG, 0)
      bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
      bus.write_byte_data(Device_Address, INT_ENABLE, 1)

  def read_raw_data(addr):
      high = bus.read_byte_data(Device_Address, addr)
      low = bus.read_byte_data(Device_Address, addr + 1)
      value = (high << 8) | low
      if value > 32768:
          value -= 65536
      return value

  def HMC5883L_Init():
      bus.write_byte_data(HMC5883L_ADDRESS, HMC5883L_CRA, 0b01110000)  # 8-average, 15 Hz default, normal measurement
      bus.write_byte_data(HMC5883L_ADDRESS, HMC5883L_CRB, 0b00100000)  # Gain=5
      bus.write_byte_data(HMC5883L_ADDRESS, HMC5883L_MODE, 0b00000000)  # Continuous-measurement mode

  def read_HMC5883L():
      mx = (bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H) << 8) | bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H + 1)
      my = (bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H + 2) << 8) | bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H + 3)
      mz = (bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H + 4) << 8) | bus.read_byte_data(HMC5883L_ADDRESS, HMC5883L_DO_X_H + 5)
      return mx, my, mz

else:  # Dummy sensor functions
  def read_raw_data(addr):
      return random.randint(-32768, 32767)

  def read_HMC5883L():
      return random.randint(-1000, 1000), random.randint(-1000, 1000), random.randint(-1000, 1000)

  def MPU_Init():
      pass  # No initialization needed for dummy sensor

  def HMC5883L_Init():
      pass  # No initialization needed for dummy sensor

if not use_dummy_sensor:
  MPU_Init()
  HMC5883L_Init()

print("Lendo dados do sensor GY-87")

num_samples = 100  # Número de amostras para calibração

# Arrays para armazenar as amostras
accel_x_offset = np.zeros(num_samples)
accel_y_offset = np.zeros(num_samples)
accel_z_offset = np.zeros(num_samples)

gyro_x_offset = np.zeros(num_samples)
gyro_y_offset = np.zeros(num_samples)
gyro_z_offset = np.zeros(num_samples)

mag_x_offset = np.zeros(num_samples)
mag_y_offset = np.zeros(num_samples)
mag_z_offset = np.zeros(num_samples)

for i in range(num_samples):
  # Leitura dos dados do acelerômetro
  acc_x = read_raw_data(ACCEL_XOUT_H)
  acc_y = read_raw_data(ACCEL_YOUT_H)
  acc_z = read_raw_data(ACCEL_ZOUT_H)

  # Leitura dos dados do giroscópio
  gyro_x = read_raw_data(GYRO_XOUT_H)
  gyro_y = read_raw_data(GYRO_YOUT_H)
  gyro_z = read_raw_data(GYRO_ZOUT_H)

  # Leitura dos dados do magnetômetro
  mag_x, mag_y, mag_z = read_HMC5883L()

  # Armazenar as amostras nos arrays
  accel_x_offset[i] = acc_x
  accel_y_offset[i] = acc_y
  accel_z_offset[i] = acc_z

  gyro_x_offset[i] = gyro_x
  gyro_y_offset[i] = gyro_y
  gyro_z_offset[i] = gyro_z

  mag_x_offset[i] = mag_x
  mag_y_offset[i] = mag_y
  mag_z_offset[i] = mag_z

  time.sleep(0.02)  # Pequeno atraso entre as leituras

# Calcular as médias (offsets)
accel_x_offset_mean = np.mean(accel_x_offset)
accel_y_offset_mean = np.mean(accel_y_offset)
accel_z_offset_mean = np.mean(accel_z_offset) - 16384.0 if not use_dummy_sensor else np.mean(accel_z_offset)  # Ajuste para a gravidade (apenas sensor real)

gyro_x_offset_mean = np.mean(gyro_x_offset)
gyro_y_offset_mean = np.mean(gyro_y_offset)
gyro_z_offset_mean = np.mean(gyro_z_offset)

mag_x_offset_mean = np.mean(mag_x_offset)
mag_y_offset_mean = np.mean(mag_y_offset)
mag_z_offset_mean = np.mean(mag_z_offset)

print("Acelerômetro X offset : %.2f" % accel_x_offset_mean)
print("Acelerômetro Y offset : %.2f" % accel_y_offset_mean)
print("Acelerômetro Z offset : %.2f" % accel_z_offset_mean)

print("Giroscópio X offset : %.2f" % gyro_x_offset_mean)
print("Giroscópio Y offset : %.2f" % gyro_y_offset_mean)
print("Giroscópio Z offset : %.2f" % gyro_z_offset_mean)

print("Magnetômetro X offset : %.2f" % mag_x_offset_mean)
print("Magnetômetro Y offset : %.2f" % mag_y_offset_mean)
print("Magnetômetro Z offset : %.2f" % mag_z_offset_mean)