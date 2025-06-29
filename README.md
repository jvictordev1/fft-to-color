# Analisador de Espectro e Osciloscópio com Raspberry Pi Pico

Este projeto transforma uma Raspberry Pi Pico em um instrumento de análise de áudio em tempo real. Utilizando um microfone, o sistema captura som e oferece duas visualizações distintas em um display OLED, alternáveis através de um botão.

## Funcionalidades

- **Análise de Áudio em Tempo Real:** Utiliza uma implementação da Transformada Rápida de Fourier (FFT) em MicroPython para decompor o som em suas frequências constituintes.
- **Visualização Dupla:** Alterne entre os modos com um clique de botão.
  - **Modo Analisador de Espectro:** Exibe um gráfico de linha das intensidades de frequência (graves à esquerda, agudos à direita) no display OLED.
  - **Modo Osciloscópio:** Exibe a forma de onda do áudio bruto no domínio do tempo.
- **Feedback de Cor Espectral:** Uma matriz de LEDs NeoPixel 5x5 acende com uma cor que corresponde à frequência dominante (o tom mais forte) do som capturado, seguindo o espectro de luz visível (vermelho para graves, azul/violeta para agudos).
- **Altamente Configurável:** Parâmetros de calibração fáceis de ajustar para sensibilidade de volume, escala do gráfico e mapeamento de cores.

## Hardware Necessário

- 1x Raspberry Pi Pico da BitDogLab

**Atenção:** A matriz NeoPixel pode consumir uma corrente significativa. Conectá-la ao pino `VBUS` (5V da USB) é mais seguro.

## Configuração do Software e Instalação

Este projeto foi desenvolvido para ser executado com o **Thonny IDE**.

### 1. Instale o Thonny IDE

Se ainda não o tiver, baixe e instale a versão mais recente em [thonny.org](https://thonny.org/).

### 2. Configure o Interpretador

- Conecte sua Raspberry Pi Pico ao computador.
- No Thonny, vá em `Executar` > `Selecionar interpretador...`.
- Escolha **"MicroPython (Raspberry Pi Pico)"** e a porta serial correta. Clique em OK.
- O Shell no Thonny deve mostrar o prompt do MicroPython (`>>>`).

### 3. Copie os Arquivos para a Pico

Use o painel de arquivos do Thonny (`Exibir` > `Arquivos`) para transferir os arquivos do projeto para a placa.

1.  **Crie a pasta `lib`:** No painel de arquivos da "Raspberry Pi Pico", clique com o botão direito e escolha "Novo diretório". Dê o nome de `lib`.
2.  **Envie o driver do display:** No painel "Este computador", encontre o arquivo `ssd1306.py`. Clique com o botão direito sobre ele e escolha **`Fazer upload para /lib`**.
3.  **Envie o código principal:** No painel "Este computador", encontre o arquivo `fft_to_color.py`. Clique com o botão direito sobre ele e escolha **`Fazer upload para /`** (para a raiz da Pico).

Ao final, a estrutura de arquivos na sua Pico deve ser:
Com certeza! Um bom arquivo README.md é essencial para qualquer projeto, pois serve como um manual completo para que outras pessoas (ou você mesmo no futuro) possam entender, montar e executar o código.

Preparei um README detalhado e bem estruturado, pronto para ser adicionado ao seu repositório. Ele segue a estrutura de arquivos que você especificou e está focado no uso do Thonny IDE.

Você pode copiar e colar o texto abaixo em um novo arquivo e salvá-lo como README.md na raiz do seu projeto.
Markdown

# Analisador de Espectro e Osciloscópio com Raspberry Pi Pico

Este projeto transforma uma Raspberry Pi Pico em um instrumento de análise de áudio em tempo real. Utilizando um microfone, o sistema captura som e oferece duas visualizações distintas em um display OLED, alternáveis através de um botão.

Obrigado a Gemini, uma IA do Google, pela assistência e por todo o suporte durante a elaboração do código.

## Funcionalidades

- **Análise de Áudio em Tempo Real:** Utiliza uma implementação da Transformada Rápida de Fourier (FFT) em MicroPython para decompor o som em suas frequências constituintes.
- **Visualização Dupla:** Alterne entre os modos com um simples clique de botão.
  - **Modo Analisador de Espectro:** Exibe um gráfico de linha das intensidades de frequência (graves à esquerda, agudos à direita) no display OLED.
  - **Modo Osciloscópio:** Exibe a forma de onda do áudio bruto no domínio do tempo.
- **Feedback de Cor Espectral:** Uma matriz de LEDs NeoPixel 5x5 acende com uma cor que corresponde à frequência dominante (o tom mais forte) do som capturado, seguindo o espectro de luz visível (vermelho para graves, azul/violeta para agudos).
- **Altamente Configurável:** Parâmetros de calibração fáceis de ajustar para sensibilidade de volume, escala do gráfico e mapeamento de cores.

## Hardware Necessário

- 1x Raspberry Pi Pico
- 1x Módulo Microfone Eletreto com Amplificador (com saída analógica `AO`)
- 1x Display OLED 128x64 I2C (baseado no chip SSD1306)
- 1x Matriz de LEDs 5x5 NeoPixel (WS2812B) ou similar
- 1x Botão Táctil (Push Button)
- 1x Protoboard (Matriz de Contatos)
- Fios Jumper para as conexões

## Montagem e Conexões

Conecte os componentes à sua Raspberry Pi Pico conforme o esquema abaixo.

| Componente          | Pino do Componente | Pino da Raspberry Pi Pico | Descrição                                      |
| ------------------- | ------------------ | ------------------------- | ---------------------------------------------- |
| **Microfone**       | `GND`              | `GND` (ex: Pino 38)       | Terra                                          |
|                     | `VCC`              | `3V3 (OUT)` (Pino 36)     | Alimentação 3.3V                               |
|                     | `AO`               | `GP28` (Pino 34, ADC2)    | Saída Analógica para Leitura de Som            |
| **Display OLED**    | `GND`              | `GND` (ex: Pino 38)       | Terra                                          |
|                     | `VCC`              | `3V3 (OUT)` (Pino 36)     | Alimentação 3.3V                               |
|                     | `SDA`              | `GP14` (Pino 19)          | Linha de Dados I2C (I2C1 SDA)                  |
|                     | `SCL`              | `GP15` (Pino 20)          | Linha de Clock I2C (I2C1 SCL)                  |
| **Matriz NeoPixel** | `GND`              | `GND` (ex: Pino 38)       | Terra                                          |
|                     | `5V / VCC`         | `VBUS` (Pino 40)          | **Importante:** Usar 5V para alimentar os LEDs |
|                     | `DIN`              | `GP7` (Pino 10)           | Entrada de Dados dos LEDs                      |
| **Botão de Modo**   | Perna 1            | `GND` (ex: Pino 38)       | Terra                                          |
|                     | Perna 2            | `GP5` (Pino 7)            | Pino de Leitura do Botão                       |

**Atenção:** A matriz NeoPixel pode consumir uma corrente significativa. Conectá-la ao pino `VBUS` (5V da USB) é mais seguro do que usar o pino `3V3`.

## Configuração do Software e Instalação

Este projeto foi desenvolvido para ser executado com o **Thonny IDE**.

### 1. Instale o Thonny IDE

Se ainda não o tiver, baixe e instale a versão mais recente em [thonny.org](https://thonny.org/).

### 2. Configure o Interpretador

- Conecte sua Raspberry Pi Pico ao computador.
- No Thonny, vá em `Executar` > `Selecionar interpretador...`.
- Escolha **"MicroPython (Raspberry Pi Pico)"** e a porta serial correta. Clique em OK.
- O Shell no Thonny deve mostrar o prompt do MicroPython (`>>>`).

### 3. Copie os Arquivos para a Pico

Use o painel de arquivos do Thonny (`Exibir` > `Arquivos`) para transferir os arquivos do projeto para a placa.

1.  **Crie a pasta `lib`:** No painel de arquivos da "Raspberry Pi Pico", clique com o botão direito e escolha "Novo diretório". Dê o nome de `lib`.
2.  **Envie o driver do display:** No painel "Este computador", encontre o arquivo `ssd1306.py`. Clique com o botão direito sobre ele e escolha **`Fazer upload para /lib`**.
3.  **Envie o código principal:** No painel "Este computador", encontre o arquivo `fft_to_color.py`. Clique com o botão direito sobre ele e escolha **`Fazer upload para /`** (para a raiz da Pico).

Ao final, a estrutura de arquivos na sua Pico deve ser:

```
/ (Raiz da Pico)
|
|-- lib/
|   |-- ssd1306.py
|
|-- fft_to_color.py
```

## Como Executar o Projeto

1.  Com os arquivos já na Pico, dê um duplo clique em `fft_to_color.py` no painel de arquivos do Thonny para abri-lo no editor.
2.  Clique no botão verde "Executar" (ou pressione a tecla `F5`).
3.  O programa iniciará, e você verá a mensagem "Sistema Final Iniciado..." no Shell.

## Uso e Calibração

### Seleção de Modo

- Pressione o **Botão A** (conectado ao `GPIO 5`) para alternar a visualização no display entre o **Analisador de Espectro** e o **Osciloscópio**.

### Ajuste Fino (Calibração)

Para obter os melhores resultados, ajuste as constantes na seção de calibração no topo do arquivo `fft_to_color.py`:

- `RMS_THRESHOLD`: Aumente este valor se o sistema estiver reagindo a ruído de fundo. Diminua se ele não estiver detectando sua voz.
- `MAGNITUDE_SCALE_DISPLAY`: Controle a "sensibilidade" vertical do gráfico no display. Se as linhas estiverem muito altas, aumente este número. Se estiverem muito baixas, diminua-o.
- `MIN_FREQ_COLOR` e `MAX_FREQ_COLOR`: Defina a faixa de frequências (em Hz) que será mapeada ao espectro de cores completo, do vermelho ao violeta.
- `NEOPIXEL_BRIGHTNESS`: Ajuste o brilho geral da matriz de LEDs (um valor entre 0.0 e 1.0).
