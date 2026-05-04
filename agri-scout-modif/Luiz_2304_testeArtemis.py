import serial
import math

# Configura a porta serial da Raspberry Pi (Pinos GPIO 14 e 15)
# A taxa de 115200 é o padrão do firmware da OpenLog Artemis
porta_serial = '/dev/ttyS0'
baud_rate = 115200

try:
    ser = serial.Serial(porta_serial, baud_rate, timeout=1)
    print("Conectado à Artemis! Lendo dados...")
except Exception as e:
    print(f"Erro ao abrir a porta serial: {e}")
    exit()

while True:
    try:
        # Lê a linha da serial e remove espaços/quebras de linha
        linha = ser.readline().decode('utf-8').strip()
        
        # Ignora linhas vazias
        if not linha:
            continue
            
        # Divide a linha nas vírgulas
        dados = linha.split(',')
        
        # Garante que a linha tem dados suficientes antes de tentar ler
        if len(dados) >= 5:
            # Extrai Q1, Q2 e Q3 (que estão nos índices 2, 3 e 4)
            q1 = float(dados[2])
            q2 = float(dados[3])
            q3 = float(dados[4])
            
            # --- INÍCIO DA MATEMÁTICA (Traduzida do C++) ---
            
            # Calcula Q0: sqrt(1.0 - (q1^2 + q2^2 + q3^2))
            # O "max(0.0, ...)" evita erro de raiz negativa por imprecisão de float
            q0 = math.sqrt(max(0.0, 1.0 - ((q1 * q1) + (q2 * q2) + (q3 * q3))))
            
            q2sqr = q2 * q2

            # Roll (Rotação no eixo X)
            t0 = +2.0 * (q0 * q1 + q2 * q3)
            t1 = +1.0 - 2.0 * (q1 * q1 + q2sqr)
            roll = math.degrees(math.atan2(t0, t1))

            # Pitch (Rotação no eixo Y)
            t2 = +2.0 * (q0 * q2 - q3 * q1)
            t2 = max(-1.0, min(1.0, t2)) # Trava entre -1 e 1 (Gimbal lock prevention)
            pitch = math.degrees(math.asin(t2))

            # Yaw (Rotação no eixo Z)
            t3 = +2.0 * (q0 * q3 + q1 * q2)
            t4 = +1.0 - 2.0 * (q2sqr + q3 * q3)
            yaw = math.degrees(math.atan2(t3, t4))
            
            # --- FIM DA MATEMÁTICA BRUTA ---

            # --- APLICAÇÃO DA CALIBRAÇÃO / OFFSETS ---
            # O usuário reportou que a placa está montada de cabeça para baixo (Roll ~ 180) 
            # e que o Norte verdadeiro está caindo em 81.6.
            
            def wrap_180(angle):
                """Garante que o grau fique num espectro fechado de -180° a +180°"""
                while angle > 180.0: angle -= 360.0
                while angle <= -180.0: angle += 360.0
                return angle

            # Offset de -179.8 para colocar a tampa do carrinho "Reta" (plana = 0)
            roll_corrigido = wrap_180(roll - 179.8)
            
            # O Pitch ainda não precisa de tara reportada
            pitch_corrigido = pitch 
            
            # Subtraindo 81.6 forçamos o "Norte" (que lia 81.6) a ler exato "0.0"
            yaw_corrigido = wrap_180(yaw - 81.6)
            
            # Imprime os resultados formatados com 1 casa decimal
            print(f"Roll: {roll_corrigido:6.1f}° | Pitch: {pitch_corrigido:6.1f}° | Yaw (Bússola): {yaw_corrigido:6.1f}°")
            
    except ValueError:
        # Ignora linhas com lixo de inicialização que não podem ser convertidas para float
        pass
    except KeyboardInterrupt:
        print("\nLeitura encerrada.")
        break
