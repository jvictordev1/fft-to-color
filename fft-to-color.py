# -*- coding: utf-8 -*-

# --- Bibliotecas ---
import machine
import neopixel
import time
import math
import cmath
import array
from ssd1306 import SSD1306_I2C

# =================================================================
# --- CONSTANTES E CONFIGURAÇÕES ---
# =================================================================

# --- Pinos ---
MIC_PIN = 28
LED_PIN = 7
I2C_SDA_PIN = 14
I2C_SCL_PIN = 15
BUTTON_PIN = 5  # Botão A

# --- Hardware ---
LED_COUNT = 25

# --- Amostragem e FFT ---
SAMPLES = 64
SAMPLING_RATE = 2000

# --- Display OLED ---
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
NUM_GRAPH_POINTS_FFT = 32

# =================================================================
# --- CALIBRAÇÃO ---
# =================================================================
RMS_THRESHOLD = 350
MAGNITUDE_SCALE_DISPLAY = 200  # Valor menor para barras/linhas mais altas
DEBOUNCE_MS = 250  # Tempo para evitar múltiplos cliques no botão

# =================================================================
# --- INICIALIZAÇÃO DO HARDWARE ---
# =================================================================
adc = machine.ADC(machine.Pin(MIC_PIN))
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)
i2c = machine.I2C(1, scl=machine.Pin(I2C_SCL_PIN), sda=machine.Pin(I2C_SDA_PIN))
display = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)

# Configura o pino do botão como entrada com resistor pull-up
button_mode_toggle = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

print("Sistema Final Iniciado. Pressione o Botão A (GPIO 5) para alternar o modo.")

# =================================================================
# --- FUNÇÕES ---
# =================================================================

def draw_axes_and_labels(mode):
    """Desenha os eixos X e Y e os indicadores de texto no display."""
    display.fill(0)
    X_MARGIN, Y_MARGIN = 8, 5
    # Eixo Y (vertical) e Eixo X (horizontal)
    display.line(X_MARGIN, 0, X_MARGIN, SCREEN_HEIGHT - Y_MARGIN, 1)
    display.line(X_MARGIN, SCREEN_HEIGHT - Y_MARGIN, SCREEN_WIDTH - 1, SCREEN_HEIGHT - Y_MARGIN, 1)

    if mode == "FREQUENCY":
        max_freq = SAMPLING_RATE // 2
        display.text(f"{max_freq // 1000}k", SCREEN_WIDTH - 20, SCREEN_HEIGHT - 8, 1)
        display.text("Hz", SCREEN_WIDTH - 20, SCREEN_HEIGHT - 16, 1)
        display.text("V", 0, 0, 1)
    elif mode == "TIME":
        display.text("Tempo", SCREEN_WIDTH - 40, SCREEN_HEIGHT - 8, 1)
        display.text("V", 0, 0, 1)


def draw_frequency_plot(fft_result):
    """Desenha o gráfico do espectro de frequência (FFT) no display."""
    draw_axes_and_labels("FREQUENCY")
    GRAPH_START_X, GRAPH_WIDTH, GRAPH_BOTTOM_Y = 9, SCREEN_WIDTH - 9, SCREEN_HEIGHT - 6
    fft_bins_per_point = (SAMPLES // 2) // NUM_GRAPH_POINTS_FFT
    points = []

    for i in range(NUM_GRAPH_POINTS_FFT):
        start = i * fft_bins_per_point
        end = start + fft_bins_per_point
        max_mag = 0
        for j in range(max(1, start), end):
            mag = abs(fft_result[j])
            if mag > max_mag:
                max_mag = mag

        x = GRAPH_START_X + int((i / (NUM_GRAPH_POINTS_FFT - 1)) * (GRAPH_WIDTH - 1))
        h = int(max_mag / MAGNITUDE_SCALE_DISPLAY)
        if h > GRAPH_BOTTOM_Y:
            h = GRAPH_BOTTOM_Y
        points.append((x, GRAPH_BOTTOM_Y - h))

    for i in range(len(points) - 1):
        display.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 1)


def draw_time_plot(samples_buffer):
    """Desenha o gráfico do domínio do tempo (osciloscópio) no display."""
    draw_axes_and_labels("TIME")
    GRAPH_START_X, GRAPH_WIDTH, GRAPH_BOTTOM_Y = 9, SCREEN_WIDTH - 10, SCREEN_HEIGHT - 6
    points = []

    for i in range(len(samples_buffer)):
        x = GRAPH_START_X + int((i / (SAMPLES - 1)) * GRAPH_WIDTH)
        y = GRAPH_BOTTOM_Y - int((samples_buffer[i] / 65535) * GRAPH_BOTTOM_Y)
        points.append((x, y))

    for i in range(len(points) - 1):
        display.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 1)


@micropython.native
def fft_pure_python(samples_buffer):
    """Calcula a FFT de um sinal em Python puro (algoritmo Cooley-Tukey)."""
    N = len(samples_buffer)
    if N & (N - 1) != 0:
        return None

    mean = sum(samples_buffer) / N
    complex_samples = [complex(sample - mean, 0) for sample in samples_buffer]

    # Permutação de bit-reversal
    i = 0
    for j in range(1, N - 1):
        k = N >> 1
        while k > i:
            i ^= k
            k >>= 1
        if j > i:
            complex_samples[i], complex_samples[j] = complex_samples[j], complex_samples[i]

    # Loop principal da FFT (cálculos "borboleta")
    size = 2
    while size <= N:
        half_size = size // 2
        angle = -2 * math.pi / size
        w_step = cmath.exp(complex(0, angle))
        for i in range(0, N, size):
            w = complex(1, 0)
            for j in range(half_size):
                k = i + j
                l = k + half_size
                t = complex_samples[l] * w
                complex_samples[l] = complex_samples[k] - t
                complex_samples[k] += t
            w *= w_step
        size *= 2
    return complex_samples


def calculate_rms(samples_buffer):
    """Calcula o valor RMS (Root Mean Square) para medir o volume do sinal."""
    if not samples_buffer:
        return 0
    mean = sum(samples_buffer) / len(samples_buffer)
    sum_of_squares = sum((sample - mean) ** 2 for sample in samples_buffer)
    return math.sqrt(sum_of_squares / len(samples_buffer))


# =================================================================
# ---