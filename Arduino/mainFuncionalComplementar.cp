// Arduino code and libraries are available to download - link below the video.

// Output for viewing with Serial Oscilloscope: accX,accY,magZ // gyrX, gyrY and gyrZ are commented out

/*
Arduino     MARG GY-85
  A5            SCL
  A4            SDA
  3.3V          VCC
  GND           GND
*/
#include <Arduino.h>
#include <Uduino.h>
#include <Wire.h>
#include <ADXL345.h>
#include <HMC5883L.h>
#include <ITG3200.h>

// Constants
const float GYRO_SCALE = (4 / 14.375 * PI / 180.0 / 1000000.0); // ITG3200   14.375 LSB = 1 deg/s;
const float DECLINATION_ANGLE = 0.0457;
const int NUM_SAMPLES = 500;        // Number of samples for Monte Carlo Calibration
const float alpha = 0.80;           // filtro constante
const float resolutionAcc = 1024.0; // filtro constante

// Sensor instances
Uduino uduino("BOMBARDA_UNO_1");
ADXL345 acc;
HMC5883L compass;
ITG3200 gyro = ITG3200();

// Variables
float gx, gy, gz;
float gx_rate, gy_rate, gz_rate;
float angleX = 0.0, angleY = 0.0, angleZ = 0.0;
int ax, ay, az;
float X, Y, Z;
float rollrad, pitchrad, yawrad;
float rolldeg, pitchdeg, yawchdeg;
unsigned long time, looptime;
MagnetometerScaled scaled;

// Monte Carlo Calibration variables
float calib_ax = 0, calib_ay = 0, calib_az = 0;
float calib_gx = 0, calib_gy = 0, calib_gz = 0;
float calib_mx = 0, calib_my = 0, calib_mz = 0;
// Média Móvel
const int N = 50; // Número de amostras para a média móvel

float angleXArray[N], angleYArray[N], angleZArray[N];
int angleXIndex = 0, angleYIndex = 0, angleZIndex = 0;
float angleXSum = 0, angleYSum = 0, angleZSum = 0;
float angleXMovAvg = 0, angleYMovAvg = 0, angleZMovAvg = 0;
//----------------------------------
void setup();
void monteCarloCalibration();
void loop();
void updateMovingAverage(float &sum, float newValue, float *array, int &index, int N);
void readAndProcessData();
void outputData();

void setup()
{
    Serial.begin(57600);
    while (!Serial)
        ;

    // Initialize and calibrate sensors
    acc.powerOn();
    Serial.println("Accelerometer initialized");

    compass = HMC5883L();
    Serial.println("Compass initialized");

    gyro.init(ITG3200_ADDR_AD0_LOW);
    gyro.zeroCalibrate(2500, 2);
    Serial.println("Gyro initialized");

    monteCarloCalibration();
}

void monteCarloCalibration()
{
    Serial.println("Starting Monte Carlo Calibration...");

    float sum_ax = 0, sum_ay = 0, sum_az = 0;
    float sum_gx = 0, sum_gy = 0, sum_gz = 0;
    float sum_mx = 0, sum_my = 0, sum_mz = 0;

    for (int i = 0; i < NUM_SAMPLES; i++)
    {
        acc.readAccel(&ax, &ay, &az);
        sum_ax += ax;
        sum_ay += ay;
        sum_az += az;

        gyro.readGyro(&gx, &gy, &gz);
        sum_gx += gx;
        sum_gy += gy;
        sum_gz += gz;

        scaled = compass.ReadScaledAxis();
        sum_mx += scaled.XAxis;
        sum_my += scaled.YAxis;
        sum_mz += scaled.ZAxis;

        delay(10);
    }

    calib_ax = sum_ax / NUM_SAMPLES;
    calib_ay = sum_ay / NUM_SAMPLES;
    calib_az = sum_az / NUM_SAMPLES;

    calib_gx = sum_gx / NUM_SAMPLES;
    calib_gy = sum_gy / NUM_SAMPLES;
    calib_gz = sum_gz / NUM_SAMPLES;

    calib_mx = sum_mx / NUM_SAMPLES;
    calib_my = sum_my / NUM_SAMPLES;
    calib_mz = sum_mz / NUM_SAMPLES;

    Serial.println("Monte Carlo Calibration completed.");
}

void loop()
{
    readAndProcessData();

    // Atualizar a média móvel de X
    updateMovingAverage(angleXSum, angleX, angleXArray, angleXIndex, N);
    angleXMovAvg = angleXSum / N;

    // Atualizar a média móvel de Y
    updateMovingAverage(angleYSum, angleY, angleYArray, angleYIndex, N);
    angleYMovAvg = angleYSum / N;

    // Atualizar a média móvel de Z
    updateMovingAverage(angleZSum, angleZ, angleZArray, angleZIndex, N);
    angleZMovAvg = angleZSum / N;

    outputData();
    // qualquer outro código que você queira executar em cada iteração do loop
}

// Função para atualizar a média móvel
void updateMovingAverage(float &sum, float newValue, float *array, int &index, int N)
{
    sum -= array[index];
    array[index] = newValue;
    sum += array[index];

    index = (index + 1) % N;
}

void readAndProcessData()
{
    time = millis();
    uduino.update();

    // Read and process accelerometer data
    acc.readAccel(&ax, &ay, &az);
    X = (ax - calib_ax) / resolutionAcc;
    Y = (ay - calib_ay) / resolutionAcc;
    Z = (az - calib_az) / resolutionAcc;
    rollrad = atan2(Y, Z);
    pitchrad = atan2(-X, sqrt(Y * Y + Z * Z));
    rolldeg = rollrad * RAD_TO_DEG;
    pitchdeg = pitchrad * RAD_TO_DEG;

    // Read and process magnetometer data
    scaled = compass.ReadScaledAxis();
    scaled.XAxis -= calib_mx; // Apply Monte Carlo calibration
    scaled.YAxis -= calib_my;
    scaled.ZAxis -= calib_mz;
    float heading = atan2(scaled.YAxis, scaled.XAxis) + DECLINATION_ANGLE;
    if (heading < 0)
        heading += 2 * PI;
    if (heading > 2 * PI)
        heading -= 2 * PI;

    delay(90);
    // Read and process gyroscope data
    gyro.readGyro(&gx, &gy, &gz);

    looptime = ((millis() - time) / 1000.0); // Convert looptime to seconds

    // Calculate time since last loop

    // Process gyroscope data
    gx_rate = (gx - calib_gx) / GYRO_SCALE;
    gy_rate = (gy - calib_gy) / GYRO_SCALE;
    gz_rate = (gz - calib_gz) / GYRO_SCALE;

    // Filtro complementar
    angleX = alpha * (angleX + gx_rate * looptime) + (1 - alpha) * rolldeg;
    angleY = alpha * (angleY + gy_rate * looptime) + (1 - alpha) * pitchdeg;
    angleZ = alpha * (angleZ + gz_rate * looptime) + (1 - alpha) * heading;
}

void outputData()
{
    Serial.print(angleX,20);
    Serial.print(", ");
    Serial.print(angleY,20);
    Serial.print(", ");
    Serial.println(angleZ,20);

    // Serial.print("Angles: ");
    // Serial.print(angleX);
    // Serial.print(", ");
    // Serial.print(angleY);
    // Serial.print(", ");
    // Serial.println(angleZ);

    // Serial.print("Accelerometer: ");
    // Serial.print(pitchdeg);
    // Serial.print(", ");
    // Serial.print(yawchdeg);
    // Serial.print(", ");
    // Serial.println(rolldeg);

    // Serial.print("Raw Magnetometer: ");
    // Serial.print(scaled.XAxis);
    // Serial.print(", ");
    // Serial.print(scaled.YAxis);
    // Serial.print(", ");
    // Serial.println(scaled.ZAxis);

    // Serial.print("Raw Gyro: ");
    // Serial.print(gx);
    // Serial.print(", ");
    // Serial.print(gy);
    // Serial.print(", ");
    // Serial.println(gz);
}
