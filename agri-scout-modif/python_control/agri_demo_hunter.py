#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from rclpy.qos import QoSProfile, ReliabilityPolicy
from cv_bridge import CvBridge
import cv2
import numpy as np
import serial
import time
import math

class AgriDemoHunter(Node):
    def __init__(self):
        super().__init__('agri_demo_hunter')
        
        # --- 1. CONFIGURAÇÕES DA SERIAL E MÁQUINA DE ESTADO ---
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 9600
        self.state = "SEARCHING"
        self.lost_frames = 0
        
        # Target Color HSV (Vermelho vivo/Laranja - Ajustar na Demo)
        self.lower_color = np.array([0, 120, 70])
        self.upper_color = np.array([10, 255, 255])
        
        # O quão perto precisa estar para colher (Área do Objeto na Tela)
        # Ajustado para 15000 pois a nova resolução da câmera tem 4x menos total de pixels
        self.harvest_area_threshold = 15000 
        
        # --- 2. COMUNICAÇÃO SERIAL (ARDUINO) ---
        try:
            self.robot = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)
            self.get_logger().info("🔥 Conectado aos Motores no Arduino!")
        except Exception as e:
            self.get_logger().error(f"Falha ao conectar no Arduino: {e}")
            raise SystemExit

        self.last_command = ""
        self.last_cmd_time = time.time()

        # --- 3. LIDAR SAFETY OVERRIDE ---
        self.obstacle_ahead = False
        qos_lidar = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, depth=10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_cb, qos_lidar)

        # --- 4. CAMERA VISION ---
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, '/image_raw', self.image_cb, 1)
        
        self.get_logger().info("🎯 Sistema Hunter Ligado! Olhando pelo Campo...")

    def send_cmd(self, cmd):
        # Envia apenas se mudar, ou envia "heartbeat" a cada 0.3s
        if cmd != self.last_command or (time.time() - self.last_cmd_time) > 0.3:
            self.robot.write((cmd + '\n').encode('utf-8'))
            self.last_command = cmd
            self.last_cmd_time = time.time()

    def scan_cb(self, msg):
        # O Lidar RPLidar varre de 0 a 360. A frente costuma ser no ângulo 0 ou 180.
        # Vamos assumir Frente = 0 graus (+/- 20 graus).
        # Convertemos o array para filtrar os 20 graus da esquerda e 20 da direita
        ranges = msg.ranges
        num_points = len(ranges)
        
        if num_points < 100: return
        
        # Pega a "fatia" apontada para a frente
        front_slice = ranges[:20] + ranges[-20:]
        
        # Filtra lixos (0.0 m)
        valid_ranges = [r for r in front_slice if 0.1 < r < msg.range_max]
        
        if valid_ranges:
            min_dist = min(valid_ranges)
            if min_dist < 0.4:  # Menos de 40 centímetros!
                self.obstacle_ahead = True
            else:
                self.obstacle_ahead = False

    def image_cb(self, msg):
        if self.state == "HARVESTING":
            return # Se já achou, não processa visão

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Erro cv_bridge: {e}")
            return

        h, w, _ = cv_image.shape
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # Encontra a Cor (Thresholding)
        mask = cv2.inRange(hsv, self.lower_color, self.upper_color)
        
        # Pega o maior contorno (Nossa Bandeira/Token)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_found = False
        target_x, target_y, target_area = 0, 0, 0
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            target_area = cv2.contourArea(c)
            
            if target_area > 500: # Ignora pixels lixo falsos-positivos
                M = cv2.moments(c)
                if M["m00"] != 0:
                    target_x = int(M["m10"] / M["m00"])
                    target_y = int(M["m01"] / M["m00"])
                    target_found = True
                    cv2.drawContours(cv_image, [c], -1, (0, 255, 0), 3)
                    cv2.circle(cv_image, (target_x, target_y), 5, (255, 0, 0), -1)

        # ====== DECISÃO DA MENTEE (STATE MACHINE) ======
        
        # 1. PARADA DE EMERGÊNCIA (LIDAR)
        if self.obstacle_ahead:
            self.send_cmd("X")
            self.get_logger().warn("OBSTÁCULO NA FRENTE! Freios ativados.")
            cv2.putText(cv_image, "OBSTACLE WARNING/LIDAR", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        else:
            # 2. MODO BUSCA (Cão Rodando no Eixo)
            if not target_found:
                self.lost_frames += 1
                if self.lost_frames > 15: # Perdeu por 0.5 segundos? Gira pra procurar!
                    self.state = "SEARCHING"
                    self.send_cmd("R20") # Vira como um tanque devagar
                    cv2.putText(cv_image, "[STATE] SEARCHING", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # 3. MODO LOCK-ON E APROXIMAÇÃO
            else:
                self.lost_frames = 0
                
                # Se a área for gigante, chegou no destino!
                if target_area > self.harvest_area_threshold:
                    self.state = "HARVESTING"
                    self.get_logger().info("🔥 ALVO ATINGIDO!! INICIANDO PERFURAÇÃO...")
                    self.send_cmd("X")
                    self.harvest_routine() # Dispara a rotina mecânica síncrona
                    return
                
                self.state = "TRACKING"
                # Erro na tela: Esquerda(-) ou Direita(+)
                center_x = w // 2
                error_x = target_x - center_x
                
                cv2.putText(cv_image, f"[STATE] TRACKING (Erro: {error_x}) Area: {int(target_area)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Controlador Proporcional Rústico
                if error_x < -80:   # Muito à esquerda
                    self.send_cmd("L20")
                elif error_x > 80:  # Muito à direita
                    self.send_cmd("R20")
                else:               # No centro, acelera!
                    self.send_cmd("F25") # Frente e Avante
                    
        # --- MODO HEADLESS (Para SSH sem tela visual) ---
        # Removido temporariamente o cv2.imshow() para não travar num terminal sem monitor (X11 Header)
        # cv2.imshow("DEMO HUNTER VIEW", cv_image)
        # cv2.waitKey(1)

    def harvest_routine(self):
        # Trava rodas
        self.send_cmd("X")
        time.sleep(1)
        
        self.get_logger().info("👇 Sonda DESCENDO (-11000 Passos)")
        self.robot.write(b"S-11000\n")
        
        # Espera o tempo físico dela concluir o movimento
        # Dica: O loop fica travado aqui propositalmente na Demo
        time.sleep(15) 
        
        self.get_logger().info("👆 Sonda SUBINDO (11000 Passos)")
        self.robot.write(b"S11000\n")
        time.sleep(15)
        
        self.get_logger().info("✅ MISSÃO COMPLETA! Retornando ao ponto de busca.")
        # Retorna a caçar caso queira espalhar várias bandeiras no campo
        self.state = "SEARCHING"
        self.lost_frames = 50

def main(args=None):
    rclpy.init(args=args)
    node = AgriDemoHunter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Nó encerrado pela mão do desenvolvedor.")
        node.send_cmd("X")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
