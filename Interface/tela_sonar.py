import serial
import math
import matplotlib.pyplot as plt
import threading
import queue
import time

PORTA = 'COM7'
BAUD_RATE = 115200

try:
    placa = serial.Serial(PORTA, BAUD_RATE, timeout=0.1)
    print(f"[{PORTA}] Conexão estabelecida com sucesso!")
except serial.SerialException:
    print(f"Erro: Não foi possível abrir a {PORTA}.")
    exit()

# Configuração da Interface Gráfica
plt.ion()
plt.style.use('dark_background')
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(9, 6))
fig.canvas.manager.set_window_title('Sonar Tático')

# Limites do Gráfico (1 Metro / 100 cm)
ax.set_ylim(0, 100) 
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(-90)
ax.set_thetamax(90)
ax.set_facecolor('#001500') 
ax.tick_params(colors='#00FF00')
ax.grid(color='#00FF00', alpha=0.3)
ax.spines['polar'].set_color('#00FF00')
ax.set_title("Varredura do Sensor Frontal (1 Metro)", color='#00FF00', va='bottom', weight='bold')

linha_varredura, = ax.plot([], [], color='#00FF00', linewidth=3)
pontos_alvo = ax.scatter([], [], c='red', s=80, marker='o')

# ==========================================
# ARQUITETURA MULTITHREADING
# ==========================================
fila_dados = queue.Queue()
executando = True

def ler_porta_serial():
    while executando:
        try:
            if placa.in_waiting > 0:
                dado = placa.readline().decode('utf-8', errors='ignore').strip()
                if ',' in dado:
                    valores = dado.split(',')
                    if len(valores) == 2: 
                        try:
                            angulo_graus = float(valores[0])
                            distancia_cm = float(valores[1])
                            fila_dados.put((angulo_graus, distancia_cm))
                        except ValueError:
                            pass 
        except Exception:
            pass 
        time.sleep(0.001) 

thread_leitura = threading.Thread(target=ler_porta_serial, daemon=True)
thread_leitura.start()

print("Lendo coordenadas... (Feche a janela do gráfico para encerrar)")

historico_pontos = [] 
TAXA_DECAIMENTO = 0.05 

plt.show(block=False)

try:
    while True:
        if not plt.fignum_exists(fig.number):
            break
            
        while not fila_dados.empty():
            angulo_graus, distancia_cm = fila_dados.get()
            
            angulo_rad = math.radians(angulo_graus)
            linha_varredura.set_data([0, angulo_rad], [0, distancia_cm])
            
            if 2 < distancia_cm < 100:
                historico_pontos.append({'ang': angulo_rad, 'dist': distancia_cm, 'vida': 1.0})

        # 1. Primeiro nós tiramos a vida e removemos quem já sumiu
        for ponto in historico_pontos:
            ponto['vida'] -= TAXA_DECAIMENTO
        historico_pontos = [p for p in historico_pontos if p['vida'] > 0]

        # 2. DEPOIS verificamos se sobrou alguém para enviar ao gráfico
        if len(historico_pontos) > 0:
            angulos = [p['ang'] for p in historico_pontos]
            distancias = [p['dist'] for p in historico_pontos]
            cores = [(1.0, 0.0, 0.0, max(0, p['vida'])) for p in historico_pontos]
            
            pontos_alvo.set_offsets(list(zip(angulos, distancias)))
            pontos_alvo.set_facecolors(cores)
            pontos_alvo.set_edgecolors(cores)
        else:
            # Envia um ponto zerado para não quebrar a biblioteca
            pontos_alvo.set_offsets([[0, 0]])
            pontos_alvo.set_facecolors([(0, 0, 0, 0)]) 
            pontos_alvo.set_edgecolors([(0, 0, 0, 0)]) 

        plt.pause(0.03)

except KeyboardInterrupt:
    pass
finally:
    print("Encerrando o Sonar Tático...")
    executando = False
    thread_leitura.join(timeout=1.0)
    placa.close()
    plt.ioff()