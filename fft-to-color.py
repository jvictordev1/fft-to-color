# Projeto: Analisador de Espectro e Osciloscópio com Raspberry Pi Pico
# Descrição:
# Este código utiliza um microfone conectado a PI Pico para capturar áudio em tempo real.
# Ele oferece dois modos de visualização, alternáveis por um botão:
# 1. MODO FREQUÊNCIA: Calcula a Transformada Rápida de Fourier (FFT)
#    do sinal de áudio e exibe o espectro de frequência em um display
#    OLED, enquanto uma matriz de LEDs NeoPixel mostra a cor
#    correspondente à frequência dominante (tom mais forte).
# 2. MODO TEMPO: Funciona como um osciloscópio, mostrando a forma
#    de onda do sinal de áudio diretamente no display OLED.


# 'machine' nos dá acesso ao hardware (pinos, ADC, I2C).
# 'neopixel' controla a matriz de LEDs RGB.
# 'time', 'math', 'cmath' e 'array' são bibliotecas padrão para
# controle de tempo, matemática e manipulação de dados eficientes.
# 'ssd1306' é o driver para o nosso display OLED."
import machine
import neopixel
import time
import math
import cmath
import array
from ssd1306 import SSD1306_I2C

# Variáveis de configuração do projeto, calibrando o sistema.

# --- Configuração dos Pinos ---
MIC_PIN = 28        # Pino do ADC conectado à saída analógica do microfone
LED_PIN = 7         # Pino de dados para a matriz de LEDs NeoPixel
I2C_SDA_PIN = 14    # Pino SDA para a comunicação com o display OLED
I2C_SCL_PIN = 15    # Pino SCL para a comunicação com o display OLED
BUTTON_PIN = 5      # Pino do botão para alternar os modos

# --- Configuração do Hardware ---
LED_COUNT = 25      # Número de LEDs na matriz NeoPixel

# --- Configuração da Amostragem e FFT ---
# Aumentamos SAMPLES para ter mais resolução na frequência.
# Ajustamos SAMPLING_RATE para manter o sistema responsivo.
SAMPLES = 64       # Número de amostras de áudio por ciclo (deve ser potência de 2)
SAMPLING_RATE = 1200 # Taxa de amostragem em Hz (amostras por segundo)

# --- Configuração do Display ---
SCREEN_WIDTH = 128  # Largura do display em pixels
SCREEN_HEIGHT = 64  # Altura do display em pixels
NUM_GRAPH_POINTS_FFT = 32 # Quantos pontos/barras desenhar no gráfico da FFT

# --- Parâmetros de Calibração ---
# Estes valores devem ser ajustados para cada microfone e ambiente.
RMS_THRESHOLD = 150         # Nível mínimo de volume (RMS) para ativar a visualização
MAGNITUDE_SCALE_DISPLAY = 150 # Fator de escala para a altura do gráfico no display
DEBOUNCE_MS = 250           # Tempo (ms) para evitar leitura múltipla de um clique no botão

# --- Parâmetros de Mapeamento de Cor (Espectro) ---
MIN_FREQ_COLOR = 100.0   # Frequência (Hz) que corresponde ao início do espectro (Vermelho)
MAX_FREQ_COLOR = 700.0   # Frequência (Hz) que corresponde ao fim do espectro (Azul/Violeta)
NEOPIXEL_BRIGHTNESS = 0.4  # Brilho geral dos LEDs (de 0.0 a 1.0)

# INICIALIZAÇÃO DO HARDWARE
# Criação de objetos que representam o hardware.
# Instanciamos o ADC, a matriz NeoPixel, a comunicação I2C,
# o display e o botão, associando cada um aos seus pinos corretos."
adc = machine.ADC(machine.Pin(MIC_PIN))
np = neopixel.NeoPixel(machine.Pin(LED_PIN), LED_COUNT)
i2c = machine.I2C(1, scl=machine.Pin(I2C_SCL_PIN), sda=machine.Pin(I2C_SDA_PIN))
display = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)
button_mode_toggle = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

print("Sistema Iniciado.")
print("Pressione o Botão A para alternar o modo.")


# Funções auxiliares
def hsv_to_rgb(h, s, v):
    """
    Converte uma cor representada no modelo HSV (Hue/Matiz, Saturation/Saturação,
    Value/Brilho) para o modelo RGB (Red/Vermelho, Green/Verde, Blue/Azul),
    que é o formato que os LEDs NeoPixel entendem.

    Implementa o algoritmo padrão de conversão. O 'h' (matiz) é um valor
    de 0.0 a 1.0 que representa uma posição no círculo de cores (0.0=vermelho,
    0.33=verde, 0.66=azul). A função calcula os valores R, G, B
    correspondentes e os retorna como inteiros de 0 a 255.

    Parâmetros:
    - h, s, v: Floats entre 0.0 e 1.0 representando Matiz, Saturação e Brilho.
    """
    if s == 0.0: return int(v*255), int(v*255), int(v*255)
    i = int(h*6.0); f = (h*6.0) - i
    p, q, t = v*(1.0-s), v*(1.0-s*f), v*(1.0-s*(1.0-f))
    i %= 6
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return int(r*255), int(g*255), int(b*255)

def draw_axes_and_labels(mode):
    """
    Prepara o display para um novo quadro, desenhando a interface
    estática, que consiste nos eixos X e Y e seus respectivos textos.

    Primeiro, limpa toda a tela com `display.fill(0)`. Depois, usa a função
    `display.line()` para desenhar uma linha vertical à esquerda (eixo Y)
    e uma horizontal na base (eixo X). Por fim, usa `display.text()` para
    escrever os indicadores ("V" de magnitude, "Hz" de frequência)
    dependendo do modo de visualização atual.
    """
    display.fill(0)
    X_MARGIN, Y_MARGIN = 8, 5
    display.line(X_MARGIN, 0, X_MARGIN, SCREEN_HEIGHT - Y_MARGIN, 1)
    display.line(X_MARGIN, SCREEN_HEIGHT - Y_MARGIN, SCREEN_WIDTH - 1, SCREEN_HEIGHT - Y_MARGIN, 1)
    if mode == "FREQUENCY":
        max_freq = SAMPLING_RATE // 2
        display.text(f"{max_freq/1000:.1f}k", SCREEN_WIDTH - 30, SCREEN_HEIGHT - 8, 1)
        display.text("V", 0, 0, 1)
    elif mode == "TIME":
        display.text("Tempo", SCREEN_WIDTH - 40, SCREEN_HEIGHT - 8, 1)
        display.text("V", 0, 0, 1)

def draw_frequency_plot(fft_result):
    """
    Processa o resultado bruto da FFT e o traduz em um gráfico de
    espectro de frequência (um analisador de espectro) no display.

    1. Chama `draw_axes_and_labels` para preparar o fundo.
    2. Agrupa os resultados da FFT em um número menor de "barras" visuais
       (`NUM_GRAPH_POINTS_FFT`) para simplificar o gráfico.
    3. Para cada "barra", ele encontra a magnitude (volume) do pico de frequência
       naquele segmento do espectro.
    4. Mapeia essa magnitude para uma altura em pixels, usando a constante
       de calibração `MAGNITUDE_SCALE_DISPLAY`.
    5. Calcula as coordenadas (x, y) de cada ponto do gráfico.
    6. Conecta todos os pontos com linhas (`display.line()`) para formar o gráfico.
    """
    draw_axes_and_labels("FREQUENCY")
    GRAPH_START_X, GRAPH_WIDTH, GRAPH_BOTTOM_Y = 9, SCREEN_WIDTH - 10, SCREEN_HEIGHT - 6
    fft_bins_per_point = (SAMPLES // 2) // NUM_GRAPH_POINTS_FFT
    points = []
    for i in range(NUM_GRAPH_POINTS_FFT):
        start, end = i * fft_bins_per_point, (i + 1) * fft_bins_per_point
        max_mag = 0
        for j in range(max(1, start), end):
            mag = abs(fft_result[j])
            if mag > max_mag: max_mag = mag
        x = GRAPH_START_X + int((i / (NUM_GRAPH_POINTS_FFT - 1)) * GRAPH_WIDTH)
        h = int(max_mag / MAGNITUDE_SCALE_DISPLAY)
        if h > GRAPH_BOTTOM_Y: h = GRAPH_BOTTOM_Y
        points.append((x, GRAPH_BOTTOM_Y - h))
    for i in range(len(points) - 1):
        display.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 1)

def draw_time_plot(samples_buffer):
    """
    Desenha a forma de onda do áudio capturado diretamente no display,
    funcionando como um simples osciloscópio.

    1. Chama `draw_axes_and_labels` para preparar o fundo.
    2. Itera por cada uma das amostras de áudio no `samples_buffer`.
    3. Mapeia o índice de cada amostra para uma posição X na tela e o
       valor da amostra (0 a 65535) para uma posição Y.
    4. Conecta todos os pontos resultantes com linhas, recriando a
       forma de onda visualmente.
    """
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
    """
    É o motor matemático do projeto. Executa a Transformada Rápida de Fourier
    (FFT), convertendo um sinal do domínio do tempo (uma série de amostras
    de volume) para o domínio da frequência (quais frequências compõem o som).

    Implementa o algoritmo 'Cooley-Tukey Radix-2'. Este processo envolve
    matemática com números complexos para decompor a forma de onda em suas
    componentes de seno e cosseno, resultando em uma lista que representa
    a intensidade de cada "faixa" de frequência no sinal original. O decorador
    `@micropython.native` otimiza a velocidade desta função.
    """
    N = len(samples_buffer)
    if N & (N - 1) != 0: return None
    mean = sum(samples_buffer) / N
    complex_samples = [complex(s - mean, 0) for s in samples_buffer]
    i=0
    for j in range(1, N - 1):
        k = N >> 1
        while k > i: i ^= k; k >>= 1
        if j > i: complex_samples[i], complex_samples[j] = complex_samples[j], complex_samples[i]
    size = 2
    while size <= N:
        half, angle = size // 2, -2*math.pi/size; w_step = cmath.exp(complex(0, angle))
        for i in range(0, N, size):
            w = complex(1, 0)
            for j in range(half):
                k=i+j; l=k+half; t=complex_samples[l]*w
                complex_samples[l] = complex_samples[k] - t
                complex_samples[k] += t
            w *= w_step
        size *= 2
    return complex_samples

def calculate_rms(samples_buffer):
    """
    Calcula o valor RMS (Root Mean Square), que é uma medida estatística
    robusta para determinar o volume ou a "energia" geral de um sinal de áudio.

    Eleva cada amostra ao quadrado, calcula a média de todos esses quadrados
    e, por fim, tira a raiz quadrada do resultado. Isso nos dá um valor
    estável que representa a amplitude média do som, usado como nosso
    "gatilho de volume".
    """
    if not samples_buffer: return 0
    mean = sum(samples_buffer) / len(samples_buffer)
    sum_sq = sum((s - mean)**2 for s in samples_buffer)
    return math.sqrt(sum_sq / len(samples_buffer))

# Loop infinito que continuamente
# executa uma sequência de tarefas: checa a entrada do usuário,
# captura o áudio, processa os dados e atualiza as saídas visuais.
display_mode = "FREQUENCY"
last_press_time = 0
sampling_period_us = round(1_000_000 / SAMPLING_RATE)
adc_buffer = array.array('H', (0 for _ in range(SAMPLES)))
log_min = math.log10(MIN_FREQ_COLOR)
log_range = math.log10(MAX_FREQ_COLOR) - log_min

while True:
    # Checa se o botão foi pressionado, com um "debounce" para evitar
    # múltiplos registros de um único clique.
    current_time = time.ticks_ms()
    if button_mode_toggle.value() == 0 and time.ticks_diff(current_time, last_press_time) > DEBOUNCE_MS:
        display_mode = "TIME" if display_mode == "FREQUENCY" else "FREQUENCY"
        print(f"Modo alterado para: {display_mode}")
        last_press_time = current_time

    # Coleta um número definido de amostras de áudio do microfone (ADC)
    # em uma taxa de amostragem precisa.
    for i in range(SAMPLES):
        adc_buffer[i] = adc.read_u16()
        time.sleep_us(sampling_period_us)

    # Decide qual visualização mostrar com base no modo selecionado.
    if display_mode == "FREQUENCY":
        # No modo frequência, primeiro verificamos se o som é alto o suficiente.
        rms_value = calculate_rms(adc_buffer)
        if rms_value < RMS_THRESHOLD:
            np.fill((0, 0, 0)); np.write() # Desliga os LEDs
            # Mantém o último gráfico na tela (não limpa)
            continue
        
        # Se o som for alto, calculamos a FFT.
        fft_result = fft_pure_python(adc_buffer)
        if not fft_result: continue
        
        # Desenhamos o gráfico do espectro no display.
        draw_frequency_plot(fft_result)
        
        # Encontramos a frequência dominante para definir a cor dos LEDs.
        max_magnitude, dominant_freq_index = 0, 0
        for i in range(1, SAMPLES // 2):
            if abs(fft_result[i]) > max_magnitude:
                max_magnitude, dominant_freq_index = abs(fft_result[i]), i
        
        dominant_frequency = dominant_freq_index * (SAMPLING_RATE / SAMPLES)
        
        # Mapeia a frequência dominante para uma cor no espectro HSV.
        color_to_show = (0, 0, 0)
        if MIN_FREQ_COLOR <= dominant_frequency <= MAX_FREQ_COLOR:
            value = (dominant_frequency - MIN_FREQ_COLOR) / (MAX_FREQ_COLOR - MIN_FREQ_COLOR)
            hue = value * 0.75  # Mapeia de 0.0 (Vermelho) a 0.75 (Violeta)
            r, g, b = hsv_to_rgb(hue, 1.0, NEOPIXEL_BRIGHTNESS)
            color_to_show = (r, g, b)
        np.fill(color_to_show)

    elif display_mode == "TIME":
        # No modo tempo, simplesmente desenha a forma de onda capturada.
        draw_time_plot(adc_buffer)
        np.fill((0, 0, 0))  # LEDs ficam desligados neste modo.

    # Envia os comandos finais para a matriz de LEDs e para o display.
    np.write()
    display.show()
