import machine
import utime

servo = machine.PWM(machine.Pin(16))
servo.freq(50)

# O valor 4915 é a energia exata para travar o motor em 90 graus (o centro absoluto)
servo.duty_u16(4915)

print("Motor travado no centro! Pode ajustar a peça de plástico.")
while True:
    utime.sleep(1)