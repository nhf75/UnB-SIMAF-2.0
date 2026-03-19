#include "I2Cdev.h"
#include "MPU6050.h"
#include "HMC5883L.h"
#include "Wire.h"

MPU6050 accelgyro;
HMC5883L mag;

int16_t ax, ay, az;
int16_t gx, gy, gz;
int16_t mx, my, mz;

double angleX = 0.0, angleY = 0.0, angleZ = 0.0;
const double alpha = 0.80;
const double ACCEL_SENS = 16384.0;
const double GYRO_SENS = 131.0;
const double DECLINATION_ANGLE = 23.83;

const int NUM_SAMPLES = 500;

double calib_ax = 0, calib_ay = 0, calib_az = 0;
double calib_gx = 0, calib_gy = 0, calib_gz = 0;
double calib_mx = 0, calib_my = 0, calib_mz = 0;

unsigned long previousSerialTime = 0;
const unsigned long serialInterval = 25;

void monteCarloCalibration();
void calibrarAcelerometro();
void setup()
{
    Serial.begin(57600);
    Wire.begin();

    Serial.println("🔄 Inicializando sensores...");

    // 1️⃣ - Scanner I2C antes de inicializar os sensores
    Serial.println("🔍 Buscando dispositivos I2C...");
    for (byte address = 1; address < 127; address++)
    {
        Wire.beginTransmission(address);
        if (Wire.endTransmission() == 0)
        {
            Serial.print("✅ Dispositivo encontrado no endereço 0x");
            Serial.println(address, HEX);
        }
    }

    // 2️⃣ - Inicializar MPU6050 corretamente
    accelgyro.reset();
    delay(200);
    accelgyro.initialize();
    delay(200);

    // 3️⃣ - Ativar o MPU6050 e configurar
    accelgyro.setSleepEnabled(false);
    delay(200);
    accelgyro.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
    accelgyro.setFullScaleGyroRange(MPU6050_GYRO_FS_250);

    // 4️⃣ - Ajustar Offset do acelerômetro manualmente
    // accelgyro.setZAccelOffset(940);
    calibrarAcelerometro();

    if (accelgyro.testConnection())
    {
        Serial.println("✅ MPU6050 conectado!");
    }
    else
    {
        Serial.println("❌ ERRO: MPU6050 não detectado!");
    }

    // 5️⃣ - Ativar Bypass Mode para comunicação direta com HMC5883L
    accelgyro.setI2CBypassEnabled(true);
    delay(200);

    // 6️⃣ - Inicializar Magnetômetro HMC5883L
    mag.initialize();
    delay(200);

    // Ajustar escala do magnetômetro
    mag.setGain(HMC5883L_GAIN_1090);
    delay(200);

    if (mag.testConnection())
    {
        Serial.println("✅ Magnetômetro conectado!");
    }
    else
    {
        Serial.println("❌ ERRO: Magnetômetro não detectado! Tentando reset...");

        // Tentar reiniciar o barramento I2C
        Wire.begin();
        delay(100);
        mag.initialize();
        delay(200);

        if (mag.testConnection())
        {
            Serial.println("🔄 Magnetômetro recuperado!");
        }
        else
        {
            Serial.println("❌ ERRO: Magnetômetro continua sem resposta.");
        }
    }

    Serial.println("✅ Sensores inicializados com sucesso!");

    // 7️⃣ - Executar calibração
    monteCarloCalibration();
}
void calibrarAcelerometro()
{
    Serial.println("🔄 Calibrando acelerômetro...");
    long sum_az = 0;
    const int num_samples = 500;

    for (int i = 0; i < num_samples; i++)
    {
        accelgyro.getAcceleration(&ax, &ay, &az);
        sum_az += az;
        delay(2);
    }

    int media_az = sum_az / num_samples;
    int z_offset = 16384 - media_az; // Ajuste para gravidade ser 1g (16384)
    accelgyro.setZAccelOffset(z_offset);

    Serial.print("✅ Novo Z Offset: ");
    Serial.println(z_offset);
}
void monteCarloCalibration()
{
    for (int i = 0; i < NUM_SAMPLES; i++)
    {
        accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        mag.getHeading(&mx, &my, &mz);

        calib_ax += ax;
        calib_ay += ay;
        calib_az += az;
        calib_gx += gx;
        calib_gy += gy;
        calib_gz += gz;
        calib_mx += mx;
        calib_my += my;
        calib_mz += mz;
    }

    calib_ax /= NUM_SAMPLES;
    calib_ay /= NUM_SAMPLES;
    calib_az /= NUM_SAMPLES;
    calib_gx /= NUM_SAMPLES;
    calib_gy /= NUM_SAMPLES;
    calib_gz /= NUM_SAMPLES;
    calib_mx /= NUM_SAMPLES;
    calib_my /= NUM_SAMPLES;
    calib_mz /= NUM_SAMPLES;
}

void loop()
{
    static unsigned long lastTime = millis();
    unsigned long currentTime = millis();
    double dt = (currentTime - lastTime) / 1000.0;
    lastTime = currentTime;

    // 1. Obter dados do giroscópio e acelerômetro
    accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    gx -= calib_gx;
    gy -= calib_gy;
    gz -= calib_gz; // Offset do giroscópio

    double gx_rad_s = (gx / GYRO_SENS) * (M_PI / 180.0); // Convertendo para rad/s
    double gy_rad_s = (gy / GYRO_SENS) * (M_PI / 180.0);
    double gz_rad_s = (gz / GYRO_SENS) * (M_PI / 180.0);

    double ax_g = ax / ACCEL_SENS;
    double ay_g = ay / ACCEL_SENS;
    double az_g = az / ACCEL_SENS;

    // 2. Calcular Roll e Pitch do Acelerômetro (referência de longo prazo)
    double roll_accel = atan2(ay_g, az_g) * 180.0 / M_PI;
    double pitch_accel = atan2(-ax_g, sqrt(ay_g * ay_g + az_g * az_g)) * 180.0 / M_PI;

    // 3. Calcular Yaw (Heading) do Magnetômetro (referência de longo prazo)
    mag.getHeading(&mx, &my, &mz);
    mx -= calib_mx;
    my -= calib_my;
    mz -= calib_mz; // Offset do magnetômetro

    // **Compensação de inclinação para o magnetômetro (IMPORTANTE para Yaw preciso)**
    // Isso é crucial para que o magnetômetro não seja afetado por roll e pitch
    // Convertendo para radianos para as funções trigonométricas
    double roll_rad = angleX * M_PI / 180.0;
    double pitch_rad = angleY * M_PI / 180.0;

    // Compensação de inclinação (Tilt Compensation)
    double mag_x_comp = mx * cos(pitch_rad) + my * sin(roll_rad) * sin(pitch_rad) + mz * cos(roll_rad) * sin(pitch_rad);
    double mag_y_comp = my * cos(roll_rad) - mz * sin(roll_rad);

    double yaw_mag = atan2(mag_y_comp, mag_x_comp) * 180.0 / M_PI;

    // Adicionar declinação magnética
    yaw_mag += DECLINATION_ANGLE;
    if (yaw_mag < 0) yaw_mag += 360.0;
    if (yaw_mag >= 360.0) yaw_mag -= 360.0;

    // 4. Aplicar Filtro Complementar
    // Para Roll e Pitch: Giroscópio (curto prazo) + Acelerômetro (longo prazo)
    angleX = alpha * (angleX + gx_rad_s * dt * 180.0 / M_PI) + (1.0 - alpha) * roll_accel;
    angleY = alpha * (angleY + gy_rad_s * dt * 180.0 / M_PI) + (1.0 - alpha) * pitch_accel;

    // Para Yaw: Giroscópio (curto prazo) + Magnetômetro (longo prazo)
    // Note que gz_rad_s é a taxa de rotação em torno do eixo Z
    angleZ = alpha * (angleZ + gz_rad_s * dt * 180.0 / M_PI) + (1.0 - alpha) * yaw_mag;

    // Normalizar ângulos (opcional, dependendo do uso)
    // Para Roll e Pitch, geralmente -180 a 180 é o esperado
    // Para Yaw, 0 a 360 é mais comum
    if (angleZ < 0) angleZ += 360.0;
    if (angleZ >= 360.0) angleZ -= 360.0;

    if (currentTime - previousSerialTime >= serialInterval)
    {
        previousSerialTime = currentTime;

        Serial.print(angleX, 20);
        Serial.print(", ");
        Serial.print(angleY, 20);
        Serial.print(", ");
        Serial.println(angleZ, 20);

        // Serial.print(angleX, 20);
        // Serial.print(",\t");
        // Serial.print(angleY, 20);
        // Serial.print(",\t");
        // Serial.println(angleZ, 20);

        // Serial.print(roll, 20);
        // Serial.print(",\t");
        // Serial.print(pitch, 20);
        // Serial.print(",\t");
        // Serial.println(yaw, 20);

        // Serial.print(ax_pass, 20);
        // Serial.print(",\t");
        // Serial.print(ay_pass, 20);
        // Serial.print(",\t");
        // Serial.println(az_pass, 20);

        // Serial.print(mx, 20);
        // Serial.print(",\t");
        // Serial.print(my, 20);
        // Serial.print(",\t");
        // Serial.println(mz, 20);

        // Serial.print(ax, 20);
        // Serial.print(",\t");
        // Serial.print(ay, 20);
        // Serial.print(",\t");
        // Serial.println(az, 20);
    }
}