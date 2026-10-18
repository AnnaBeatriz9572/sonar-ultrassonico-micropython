import machine 
import utime 

trigger = machine.Pin(15, machine.Pin.OUT) 
echo = machine.Pin(14, machine.Pin.IN) 
servo = machine.PWM(machine.Pin(16)) 
servo.freq(50) 
buzzer = machine.PWM(machine.Pin(19)) 

def medir_distancia():
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(10)
    trigger.low()

    timeout_start = utime.ticks_us()
    timeout_us = 30000 

    while echo.value() == 0:
        if utime.ticks_diff(utime.ticks_us(), timeout_start) > timeout_us:
            return 100.0  

    inicio = utime.ticks_us()

    while echo.value() == 1:
        if utime.ticks_diff(utime.ticks_us(), inicio) > timeout_us:
            return 100.0

    fim = utime.ticks_us()
    duracao = utime.ticks_diff(fim, inicio)
    distancia = (duracao * 0.0343) / 2
    
    if distancia > 100:
        return 100.0
        
    return distancia

def controlar_servo(angulo_logico):
    angulo_fisico = angulo_logico + 90 
    
    min_duty = 1638  
    max_duty = 8192  
    duty = min_duty + (angulo_fisico / 180) * (max_duty - min_duty) 
    servo.duty_u16(int(duty)) 

# --- AQUI ESTÁ A CORREÇÃO DO ALARME ---
def tocar_buzzer(distancia):
    if distancia < 30:
        # Zona Crítica (Muito Perto)
        buzzer.freq(1000) 
        buzzer.duty_u16(32768) # Volume alto
    elif distancia < 60:
        # Zona de Atenção (Metade do Caminho)
        buzzer.freq(750) 
        buzzer.duty_u16(16384) # Volume médio
    elif distancia < 100:
        # Zona de Detecção (Até 1 metro)
        buzzer.freq(400) 
        buzzer.duty_u16(8192)  # Volume baixo/grave
    else:
        # Caminho Livre (Mais de 1 metro)
        buzzer.duty_u16(0) 

controlar_servo(0)
utime.sleep(1) 

while True:
    for angulo in range(0, 91, 2):
        controlar_servo(angulo)
        utime.sleep(0.05) 
        d = medir_distancia() 
        tocar_buzzer(d) 
        print(f"{angulo},{d}") 

    for angulo in range(88, -91, -2):
        controlar_servo(angulo)
        utime.sleep(0.05) 
        d = medir_distancia() 
        tocar_buzzer(d) 
        print(f"{angulo},{d}") 
        
    for angulo in range(-88, -1, 2):
        controlar_servo(angulo)
        utime.sleep(0.05) 
        d = medir_distancia() 
        tocar_buzzer(d) 
        print(f"{angulo},{d}")