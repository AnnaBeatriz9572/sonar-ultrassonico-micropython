# Firmware — Sonar Ultrassônico com Raspberry Pi Pico

Esta pasta contém os programas em **MicroPython** executados no **Raspberry Pi Pico (RP2040)**, responsáveis pela calibração do servomotor e pelo funcionamento da camada embarcada do sonar. A implementação corresponde ao protótipo descrito no artigo *Pensamento Computacional e Matemática Aplicada na Educação: Desenvolvimento de um Sonar Acessível Baseado em Raspberry Pi Pico*, apresentado no VII ENOPEM.

**[Voltar ao README principal](../README.md)**

## 1. Arquivos desta pasta

| Arquivo | Finalidade |
| --- | --- |
| [`calibracao.py`](calibracao.py) | Centraliza o servomotor para auxiliar o alinhamento mecânico do sensor antes da execução do sistema. |
| [`main.py`](main.py) | Controla o servomotor, mede distâncias com o HC-SR04, aciona o buzzer e transmite as medições ao computador. |

> Ambos os scripts utilizam `machine` e `utime`, módulos do **MicroPython**. Não devem ser executados no Python convencional do computador.

## 2. Componentes e conexões usadas pelo código

A camada embarcada utiliza o Raspberry Pi Pico, um sensor ultrassônico **HC-SR04**, um **servomotor compatível com PWM de 50 Hz** e um **buzzer piezoelétrico**.

| Componente | Sinal | GPIO do Pico | Configuração no código |
| --- | --- | --- | --- |
| HC-SR04 | Trigger | GP15 | Saída digital |
| HC-SR04 | Echo | GP14 | Entrada digital |
| Servomotor | Controle | GP16 | PWM a 50 Hz |
| Buzzer | Controle | GP19 | PWM com frequência e duty cycle variáveis |

**Cuidados elétricos:** os GPIOs do Raspberry Pi Pico trabalham com lógica de **3,3 V**. Se o sinal **Echo** do módulo HC-SR04 utilizado for de 5 V, é necessário adequá-lo antes de conectá-lo ao GP14. O servomotor requer alimentação compatível e uma referência de terra comum com o Pico. O artigo apresenta a montagem e a simulação, mas os trechos de código, isoladamente, não especificam o circuito completo de alimentação.

### Figuras originais do artigo

**Figura 1 — Etapa de pré-montagem e validação do circuito no Wokwi (artigo, p. 7)**

![Simulação original do circuito no Wokwi](../imagens/figura1-wokwi.jpg)

**Figura 2 — Montagem real do circuito em uma protoboard (artigo, p. 8)**

| Fotografia original da protoboard | Fotografia original do conjunto com o sensor |
| :---: | :---: |
| ![Montagem real na protoboard](../imagens/figura2-protoboard.jpg) | ![Sensor ultrassônico montado no servomotor](../imagens/figura2-sonar.jpg) |

As imagens acima são os arquivos extraídos das figuras do artigo, sem recriações ou edições de conteúdo.

## 3. Calibração do servomotor (`calibracao.py`)

Antes da varredura, o script inicializa o sinal PWM no **GP16**, com frequência de **50 Hz**, e estabelece o valor de **4915** na escala de 16 bits:

```python
servo = machine.PWM(machine.Pin(16))
servo.freq(50)
servo.duty_u16(4915)
```

Esse valor corresponde ao **ponto central da faixa de PWM adotada no projeto** e permite posicionar o suporte do sensor para alinhá-lo mecanicamente. O script mantém a posição solicitada em um laço contínuo; para executar o firmware principal, é necessário interrompê-lo ou substituí-lo pela execução de `main.py`.

> A posição mecânica exata pode variar com o modelo e a montagem do servo. O artigo descreve o uso desse valor na calibração do protótipo; isso não significa que ele seja universal para todos os servomotores.

## 4. Firmware principal (`main.py`)

O programa implementa quatro etapas integradas: **movimentação do sensor**, **medição ultrassônica**, **alerta sonoro** e **envio serial**.

### 4.1. Medição de distância

A função `medir_distancia()` gera um pulso de **10 µs** no pino Trigger, aguarda o Echo e mede sua duração usando `utime.ticks_us()` e `utime.ticks_diff()`. A distância em centímetros é calculada como:

```python
distancia = (duracao * 0.0343) / 2
```

O fator `0.0343` representa a velocidade aproximada do som em **cm/µs**, e a divisão por dois considera o trajeto de ida e volta da onda.

O firmware aplica um **timeout de 30.000 µs** durante as esperas pelo Echo. Se houver timeout ou se a distância calculada ultrapassar **100 cm**, a função retorna `100.0`. Portanto, esse valor também pode representar uma leitura fora do alcance configurado ou sem eco válido; o código não distingue esses casos.

### 4.2. Controle do servomotor

A função `controlar_servo(angulo_logico)` converte o ângulo lógico para a faixa física utilizada na montagem:

```python
angulo_fisico = angulo_logico + 90
min_duty = 1638
max_duty = 8192
duty = min_duty + (angulo_fisico / 180) * (max_duty - min_duty)
servo.duty_u16(int(duty))
```

O ângulo lógico varia de **−90° a +90°**, com o centro em **0°**, cobrindo aproximadamente **180°** de varredura. O código movimenta o servo em passos de **2°**, com pausa de **0,05 s** antes de cada medição.

A sequência de varredura foi implementada em três laços: **0° até +90°**, **+88° até −90°** e **−88° até −2°**; em seguida, o ciclo recomeça em 0°.

### 4.3. Alerta sonoro

A função `tocar_buzzer(distancia)` ajusta a frequência e o duty cycle do buzzer conforme os limiares definidos no código:

| Distância medida | Faixa | Frequência PWM | Duty cycle (`duty_u16`) |
| --- | --- | --- | --- |
| Menor que 30 cm | Zona Crítica | 1000 Hz | 32768 |
| De 30 a menos de 60 cm | Zona de Atenção | 750 Hz | 16384 |
| De 60 a menos de 100 cm | Zona de Detecção | 400 Hz | 8192 |
| 100 cm ou mais (incluindo leituras limitadas a 100 cm) | Caminho Livre / sem alerta | Sem nova frequência definida | 0 |

Esses números descrevem o **sinal PWM programado**, não medições instrumentais do volume acústico emitido.

### 4.4. Comunicação serial com o computador

Após posicionar o servomotor, medir a distância e atualizar o buzzer, o firmware envia uma linha com dois valores separados por vírgula:

```python
print(f"{angulo},{d}")
```

**Formato transmitido:** `angulo,distancia_cm` — por exemplo, `20,45.3` representa um ângulo lógico de 20° e uma distância de 45,3 cm.

Essas linhas são recebidas pelo programa [`Interface/tela_sonar.py`](../Interface/tela_sonar.py), que apresenta o radar em coordenadas polares. A interface disponibilizada está configurada para uma porta serial local `COM7` e `115200` baud, valores que devem ser verificados no computador usado.

## 5. Como executar no Raspberry Pi Pico

1. Monte e revise o circuito, principalmente as conexões de **alimentação, terra comum** e o nível lógico do **Echo**.
2. Instale o **MicroPython** no Raspberry Pi Pico e conecte-o ao computador por USB.
3. Abra `calibracao.py` em um ambiente compatível, como o **Thonny**, e execute-o **no Pico** para realizar o alinhamento mecânico.
4. Interrompa a calibração e execute `main.py` **no Pico** para iniciar a varredura, as leituras e o buzzer.
5. Para visualizar o radar no computador, siga as instruções do [README da interface](../Interface/README.md) e evite que um monitor serial mantenha a porta ocupada ao abrir a aplicação.

Se `main.py` for gravado com esse nome no sistema de arquivos do Pico, poderá ser executado automaticamente na inicialização do MicroPython. O arquivo de calibração não deve ficar rodando simultaneamente com o programa principal.

## 6. Escopo e limitações

O artigo relata uma **validação funcional exploratória em bancada** da integração entre firmware e interface. Não apresenta medições quantitativas de erro médio de distância, latência serial ou taxa de atualização; esses aspectos foram apontados para investigações futuras. O limite de 100 cm e as zonas de alerta são **configurações deste protótipo**, não garantias de precisão ou segurança para usos críticos.

**Referência:** *Pensamento Computacional e Matemática Aplicada na Educação: Desenvolvimento de um Sonar Acessível Baseado em Raspberry Pi Pico*, VII ENOPEM. Para autoria, objetivos e contexto da pesquisa, consulte o [README principal](../README.md).
