#!/usr/bin/env python3
"""
agri_line_follower.py
Agricultural outdoor line-follower — camera + LiDAR + serial Arduino.

[UPDATED: SERIAL DEADLOCK FIX]
- Added input buffer clearing to prevent Arduino TX blocking Pi RX.
- Added write_timeout to prevent main thread freezing.
- Standardized steering math (Right = Positive Error -> Command R).
"""

import time
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
import cv2
import numpy as np
import serial

cv2.setNumThreads(1)

START_BYTE = 0x3C # '<'
END_BYTE = 0x3E   # '>'

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

class AgriLineFollower(Node):
    def __init__(self):
        super().__init__('agri_line_follower')

        # Vision
        self.declare_parameter('img_width',  160)      
        self.declare_parameter('img_height', 120)      
        self.declare_parameter('roi_fraction', 0.50)   
        self.declare_parameter('frame_skip', 3)        
        self.declare_parameter('debug_skip', 15)       
        self.declare_parameter('min_line_area', 50)    

        # HSV
        self.declare_parameter('line_h_lo',   0);   self.declare_parameter('line_s_lo',   0)
        self.declare_parameter('line_v_lo', 160);   self.declare_parameter('line_h_hi', 255)
        self.declare_parameter('line_s_hi',  60);   self.declare_parameter('line_v_hi', 255)

        self.declare_parameter('red_h_lo',   0);    self.declare_parameter('red_s_lo', 120)
        self.declare_parameter('red_v_lo',  70);    self.declare_parameter('red_h_hi',  10)
        self.declare_parameter('red_s_hi', 255);    self.declare_parameter('red_v_hi', 255)

        self.declare_parameter('harvest_area_threshold', 500)

        # PD controller 
        self.declare_parameter('base_speed', 0.45)   
        self.declare_parameter('min_speed',  0.35)   
        self.declare_parameter('kp', 0.55)           
        self.declare_parameter('kd', 0.12)           
        self.declare_parameter('max_steer', 0.90)    
        self.declare_parameter('deadband', 0.03)     

        # Safety
        self.declare_parameter('line_timeout',     15.0)   
        self.declare_parameter('lost_frame_limit',  15)   
        self.declare_parameter('lidar_stop_dist',  0.20)  
        self.declare_parameter('lidar_front_deg',  30)    

        self.declare_parameter('pwm_forward_range', 100)  

        # ------------------------------------------------------------------ #
        # Timer de Automação da Sonda                                        #
        # ------------------------------------------------------------------ #
        self.harvest_in_progress = False
        # Cria um timer que chama a função a cada 30.0 segundos
        self.auto_probe_timer = self.create_timer(30.0, self.auto_probe_callback)
        
        self.get_logger().info("⏳ Automação: Sonda programada para cada 30s.") 

        # Serial Connection (FIXED TIMEOUTS)
        self.robot = None
        for port in ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']:
            try:
                # ADICIONADO write_timeout=0.5 para impedir que a Thread congele
                self.robot = serial.Serial(port, 9600, timeout=0.1, write_timeout=0.5)
                time.sleep(2)
                self.get_logger().info(f"✅ Arduino connected on {port}")
                break
            except Exception:
                pass

        if self.robot is None:
            self.get_logger().fatal("Arduino not found on any USB port — aborting.")
            raise SystemExit

        self._last_action = ('X', 0)
        self._last_cmd_time = time.monotonic()
        
        self.robot.reset_input_buffer()
        self.send_secure_command('X', 0)
        time.sleep(0.5)

        self.prev_error        = 0.0
        self.last_control_time = time.monotonic()
        self.last_line_time    = None   

        self.frame_counter = 0
        self.lost_frames   = 0
        self.state         = "FOLLOWING"
        self.obstacle_ahead = False

        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, '/image_raw', self.image_cb, qos_profile_sensor_data)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_cb, qos_profile_sensor_data)
        self.debug_pub = self.create_publisher(Image, '/agri_debug', 1)

        self.create_timer(0.1, self.watchdog_cb)

        self.get_logger().info("🌾 AgriLineFollower ready — PD + Secure Protocol active.")

    def send_secure_command(self, cmd_char: str, value: int = 0):
        now = time.monotonic()
        if (cmd_char, value) != self._last_action or (now - self._last_cmd_time) > 0.4:
            
            # --- CORREÇÃO DO DEADLOCK SERIAL ---
            # Limpa o "lixo" que o Arduino enviou para não congestionar a porta USB
            try:
                if self.robot.in_waiting > 0:
                    self.robot.reset_input_buffer()
            except Exception:
                pass
            # -----------------------------------

            cmd_byte = ord(cmd_char)
            checksum = cmd_byte ^ value
            packet = bytearray([START_BYTE, cmd_byte, value, checksum, END_BYTE])
            
            try:
                self.robot.write(packet)
            except serial.SerialTimeoutException:
                self.get_logger().error("Serial Write Timeout! Arduino might be frozen.", throttle_duration_sec=2.0)
            except serial.SerialException as exc:
                self.get_logger().error(f"Serial write failed: {exc}", throttle_duration_sec=2.0)
            
            self._last_action = (cmd_char, value)
            self._last_cmd_time = now
            self.last_line_time = time.monotonic()

    def scan_cb(self, msg: LaserScan):
        n = len(msg.ranges)
        if n < 100: return
        deg = self.get_parameter('lidar_front_deg').value
        idx = int(deg / 360.0 * n)
        front = list(msg.ranges[:idx]) + list(msg.ranges[-idx:])
        valid = [r for r in front if 0.1 < r < msg.range_max]
        if valid:
            dist = self.get_parameter('lidar_stop_dist').value
            self.obstacle_ahead = min(valid) < dist

    def watchdog_cb(self):
        if self.state == "HARVESTING" or self.last_line_time is None:
            return

        timeout = self.get_parameter('line_timeout').value
        now = time.monotonic()
        
        if now - self.last_line_time > timeout:
            self.get_logger().warn("CRITICAL: Camera/Serial frozen for too long — stopping.", throttle_duration_sec=5.0)
            try:
                self.robot.write(bytearray([START_BYTE, ord('X'), 0, ord('X') ^ 0, END_BYTE]))
            except:
                pass
            self.prev_error = 0.0
            self.last_control_time = now

    def image_cb(self, msg: Image):
        if self.state == "HARVESTING": return

        self.last_line_time = time.monotonic() 

        self.frame_counter += 1
        if self.frame_counter % self.get_parameter('frame_skip').value != 0: return

        if getattr(self, '_first_frame_logged', False) is False:
            self.get_logger().info("📷 First camera frame received.")
            self._first_frame_logged = True
            self.last_control_time = time.monotonic()

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as exc:
            self.get_logger().error(f"cv_bridge error: {exc}", throttle_duration_sec=2.0)
            return

        w, h = self.get_parameter('img_width').value, self.get_parameter('img_height').value
        cv_image = cv2.resize(cv_image, (w, h), interpolation=cv2.INTER_NEAREST)

        img_h, img_w = cv_image.shape[:2]
        roi_start = int(img_h * (1.0 - self.get_parameter('roi_fraction').value))
        roi = cv_image[roi_start:, :]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 1. Harvest
        mask_red = cv2.inRange(hsv_roi, *self._red_bounds())
        cnts_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts_red:
            best_red = max(cnts_red, key=cv2.contourArea)
            if cv2.contourArea(best_red) > self.get_parameter('harvest_area_threshold').value:
                self.state = "HARVESTING"
                self.harvest_routine()
                return

        # 2. Obstacle
        if self.obstacle_ahead:
            self.send_secure_command('X', 0)
            self.get_logger().warn("Obstacle detected — waiting.", throttle_duration_sec=0.5)
            return

        # 3. Line Follower
        mask_line = cv2.inRange(hsv_roi, *self._line_bounds())
        cnts_line, _ = cv2.findContours(mask_line, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        line_found = False

        if cnts_line:
            best = max(cnts_line, key=cv2.contourArea)
            if cv2.contourArea(best) > self.get_parameter('min_line_area').value:
                M = cv2.moments(best)
                if M["m00"] != 0:
                    line_found = True
                    self.lost_frames = 0
                    
                    # CORREÇÃO DA DIREÇÃO (Sem sinal negativo no início)
                    # Linha na direita = cx maior = Erro Positivo.
                    cx = M["m10"] / M["m00"]
                    error = (cx - roi.shape[1] / 2.0) / (roi.shape[1] / 2.0)

                    now = time.monotonic()
                    dt = max(now - self.last_control_time, 0.1)
                    de_dt = (error - self.prev_error) / dt
                    self.last_control_time = now
                    self.prev_error = error

                    if abs(error) < self.get_parameter('deadband').value:
                        error, de_dt = 0.0, 0.0

                    max_steer = self.get_parameter('max_steer').value
                    
                    # Erro Positivo = Curva Positiva (Direita)
                    raw_steer = (self.get_parameter('kp').value * error + self.get_parameter('kd').value * de_dt)
                    steer = clamp(raw_steer, -max_steer, max_steer)

                    base_speed = self.get_parameter('base_speed').value
                    min_speed = self.get_parameter('min_speed').value
                    fwd_range = self.get_parameter('pwm_forward_range').value
                    
                    penalty = (abs(steer) / max_steer) * (base_speed - min_speed)
                    fwd_speed = max(min_speed, base_speed - penalty) 

                    cmd_char = 'X'
                    cmd_val = 0

                    if abs(steer) < 0.15:
                        cmd_char = 'F'
                        cmd_val = int(fwd_speed * fwd_range)
                    elif steer > 0:
                        cmd_char = 'R'
                        turn_power = clamp(abs(steer) + min_speed, min_speed, 1.0)
                        cmd_val = int(turn_power * fwd_range)
                    else:
                        cmd_char = 'L'
                        turn_power = clamp(abs(steer) + min_speed, min_speed, 1.0)
                        cmd_val = int(turn_power * fwd_range)

                    self.send_secure_command(cmd_char, cmd_val)

                    self.get_logger().info(
                        f"[PD] err={error:+.3f}  steer={steer:+.3f}  --> CMD=[{cmd_char}:{cmd_val}]",
                        throttle_duration_sec=0.2)

                    cx_i, cy_i = int(cx), int(M["m01"] / M["m00"]) + roi_start
                    cnt_o = best.copy(); cnt_o[:, :, 1] += roi_start
                    cv2.drawContours(cv_image, [cnt_o], -1, (0, 255, 0), 2)
                    cv2.circle(cv_image, (cx_i, cy_i), 5, (255, 0, 0), -1)

        if not line_found:
            self.lost_frames += 1
            if self.lost_frames > self.get_parameter('lost_frame_limit').value:
                self.send_secure_command('R', 15)

        if self.frame_counter % self.get_parameter('debug_skip').value == 0:
            try:
                self.debug_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8"))
            except Exception:
                pass

    def _line_bounds(self):
        p = self.get_parameter
        return (np.array([p('line_h_lo').value, p('line_s_lo').value, p('line_v_lo').value]),
                np.array([p('line_h_hi').value, p('line_s_hi').value, p('line_v_hi').value]))

    def _red_bounds(self):
        p = self.get_parameter
        return (np.array([p('red_h_lo').value, p('red_s_lo').value, p('red_v_lo').value]),
                np.array([p('red_h_hi').value, p('red_s_hi').value, p('red_v_hi').value]))

    def harvest_routine(self):
        self.harvest_in_progress = True  # Bloqueia novos disparos do timer
        self.send_secure_command('X', 0)
        time.sleep(1.0)
        
        try:
            self.robot.reset_input_buffer()
        except:
            pass

        # --- FASE 1: DESCIDA (Mantendo o Watchdog acordado) ---
        self.get_logger().info("⚙️ Descendo Sonda...")
        end_time = time.monotonic() + 15.5
        while time.monotonic() < end_time:
            self.send_secure_command('D', 0)
            time.sleep(0.3)  # Alimenta o Watchdog do Arduino
            
        self.send_secure_command('X', 0)

        # --- FASE 2: COLETA DE DADOS (Mantendo o Watchdog acordado no estado Parado) ---
        self.get_logger().info("⏳ Coletando dados do solo (10s)...")
        end_time = time.monotonic() + 10.0
        while time.monotonic() < end_time:
            self.send_secure_command('X', 0) # Envia "Pare" a cada 0.3s só pra Pi não ser desconectada
            time.sleep(0.3)

        # --- FASE 3: SUBIDA (Mantendo o Watchdog acordado) ---
        self.get_logger().info("⚙️ Recolhendo Sonda...")
        end_time = time.monotonic() + 15.5
        while time.monotonic() < end_time:
            self.send_secure_command('U', 0)
            time.sleep(0.3)
            
        self.send_secure_command('X', 0)

        # --- FASE 4: AVANÇO DE LIMPEZA ---
        self.get_logger().info("🏎️ Avançando para limpar área de coleta...")
        end_time = time.monotonic() + 4.0
        while time.monotonic() < end_time:
            self.send_secure_command('F', 20)
            time.sleep(0.3)

        self.send_secure_command('X', 0)
        
        # Reseta estados para voltar ao seguidor de linha
        self.lost_frames       = 0
        self.prev_error        = 0.0          
        self.last_control_time = time.monotonic()
        self.last_line_time    = time.monotonic() 
        self.state             = "FOLLOWING"
        self.harvest_in_progress = False # Libera o timer para a próxima contagem de 30s 30s

    def auto_probe_callback(self):
        """Dispara a coleta automaticamente por tempo, se o robô estiver seguindo linha."""
        if self.state == "FOLLOWING" and not self.harvest_in_progress:
            self.get_logger().info("⏱️ Intervalo de 30s atingido! Iniciando coleta automática...")
            self.state = "HARVESTING"
            self.harvest_routine()
        else:
            self.get_logger().info("⚠️ 30s atingidos, mas o robô está ocupado ou em obstáculo. Pulando esta coleta.", 
                                   throttle_duration_sec=5.0)

def main(args=None):
    rclpy.init(args=args)
    node = AgriLineFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutdown requested — stopping motors.")
        node.send_secure_command('X', 0)
    finally:
        # Resolve o erro de Crash ao dar Ctrl+C
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()