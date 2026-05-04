import serial
import time
import sys

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

def main():
    print("========================================")
    print(" CALIBRADOR DE PRECISÃO DA SONDA (LIMITES MECÂNICOS)")
    print("========================================")
    print("ALERTA: Para evitar a quebra da estrutura, o carro deve")
    print("estar suspenso ou em terreno livre de pedras grandes.\n")
    
    try:
        robot = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Aguarda reset do Arduino
        print("[SUCESSO] Conectado ao Arduino.")
    except Exception as e:
        print(f"[ERRO] Não foi possível plugar na porta {SERIAL_PORT}: {e}")
        sys.exit(1)

    # Limpa buffer inicial
    robot.reset_input_buffer()

    posicao_maxima_sonda = 0

    print("\nINSTRUÇÕES:")
    print("- Digite um número POSITIVO (ex: 50) para descer a sonda.")
    print("- Digite um número NEGATIVO (ex: -50) para subir a sonda.")
    print("- Use valores pequenos (como 10 ou 20) quando estiver chegando perto da base.")
    print("- Digite '0' ou pressione Ctrl+C para sair.\n")
    print(f"--> Posição Atual do Trilho: {posicao_maxima_sonda} Passos.")

    try:
        while True:
            comando = input("\n[DIGITE OS PASSOS]: ").strip()
            
            if not comando:
                continue

            try:
                passos = int(comando)
            except ValueError:
                print("Por favor, digite apenas números válidos.")
                continue

            if passos == 0:
                print("Saindo do calibrador...")
                break

            # Envia o comando S (Step Control)
            msg = f"S{passos}\n"
            robot.write(msg.encode('utf-8'))
            
            print("Aguardando motor...")
            
            # Lê o feedback do Arduino até dar Complete
            while True:
                linha = robot.readline().decode('utf-8').strip()
                if linha:
                    print(f" > {linha}")
                    if "Probe movement complete" in linha:
                        break
            
            # Atualiza a contagem cega com base no que foi comandado (Open-Loop Step Tracking)
            posicao_maxima_sonda += passos
            
            print("="*40)
            print(f"🧭 DISTÂNCIA RELATIVA CONTADA ATÉ AQUI: {posicao_maxima_sonda} Passos")
            print("="*40)
            print("Anote este número de Posição se a sonda acabou de encostar no fundo!")

    except KeyboardInterrupt:
        print("\n[Parada de Emergência] Calibrador encerrado pelo usuário.")
    finally:
        robot.close()
        print(f"\n--- CALIBRAÇÃO FINAL ---\nA profundidade total ou curso máximo medido foi de: {posicao_maxima_sonda} Anote isso!")

if __name__ == '__main__':
    main()
