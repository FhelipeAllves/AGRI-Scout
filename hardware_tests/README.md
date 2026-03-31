# Testes de Hardware - AGRI-Scout (Robô Real)

Bem-vindo ao conjunto de ferramentas de teste para o AGRI-Scout físico. 
Esses scripts foram desenhados para verificar isoladamente cada sensor, motor, e o sistema em que o ROS 2 está rodando (Raspberry Pi 4 B + Arduino), garantindo que tudo está pronto antes de subir a stack de navegação autônoma (`nav2`).

Como faz tempo que você não acessa a Raspberry Pi, este guia foi feito passo a passo, para te levar pela mão desde a conexão com a internet até a execução dos testes. Siga os passos cronologicamente.

---

## Passo 0: Acesso Básico e Internet na Raspberry Pi

Se você ligou a Raspberry Pi e não sabe se tem internet conectada:

### 1. Conectando a Raspberry à Internet (Wi-Fi)
Se estiver usando a Raspberry via monitor e teclado, você pode conectar no Wi-Fi usando a interface gráfica do sistema operacional (canto superior direito da tela).

Se estiver acessando via linha de comando (terminal, SSH ou TTY), use o gerenciador de redes `nmcli`:
```bash
# Listar as redes Wi-Fi disponíveis ao redor
nmcli dev wifi list

# Conectar na sua rede (substitua pelo nome da sua rede e a senha dela)
sudo nmcli dev wifi connect "NOME_DA_REDE" password "SUA_SENHA_DO_WIFI"
```

### 2. Testando a conexão
```bash
ping -c 4 google.com
```
*Se o comando responder com "64 bytes from...", você tem internet e pode seguir para o próximo passo! Se der erro de rede, repita o Passo 1.*

---

## Passo 1: Verificando e Preparando o Ambiente (ROS 2)

O cérebro do robô utiliza o **ROS 2 Jazzy**. Precisamos garantir que ele está instalado e que o workspace do projeto (pasta `agri_scout_ws`) está pronto para uso.

### 1. O ROS 2 está instalado?
Para saber se o ROS 2 está instalado, tente "ativar" o ambiente dele no terminal atual:
```bash
source /opt/ros/jazzy/setup.bash
```
* **Se não aparecer NADA na tela:** O comando deu certo, o ROS 2 está instalado!
* **Se der erro (ex: `No such file or directory`):** Significa que o ROS 2 não está instalado. Siga a [documentação oficial de instalação do ROS 2 Jazzy no Ubuntu](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) (baixe os pacotes "Desktop") antes de continuar.

### 2. O Workspace (`agri_scout_ws`) existe e está compilado?
Os códigos de navegação e pacotes do robô ficam na pasta base de trabalho em `~/agri_scout_ws`. 
Verifique se ele já foi compilado e está pronto para o uso listando a pasta de instalação:
```bash
ls ~/agri_scout_ws/install
```
* **Se a pasta existir:** Ótimo! Faça o setup do workspace:
  ```bash
  source ~/agri_scout_ws/install/setup.bash
  ```
* **Se NÃO existir ou der erro indicando que a pasta não foi achada:** Você precisa compilar o projeto inteiro. Execute os comandos abaixo:
  ```bash
  cd ~/agri_scout_ws
  colcon build --symlink-install
  source install/setup.bash
  ```

### 3. Instalando dependências dos testes Python
Os scripts de teste que você vai rodar dependem de algumas bibliotecas do Python, em especial a ferramenta `psutil` para ler dados da CPU e Memória da Raspberry.
Instale usando o gerenciador de pacotes do sistema (recomendado no Ubuntu 24.04+):
```bash
sudo apt update
sudo apt install python3-psutil
```

---

## Passo 2: Iniciando os Drivers de Hardware (A Base de Tudo)

⚠️ **MUITO IMPORTANTE:** Os scripts de teste interativos (Passo 3) **NÃO VÃO FUNCIONAR** se os sensores não estiverem ligados logicamente. O ROS 2 precisa estar "acordado" e traduzindo o sinal elétrico de cada cabo USB em mensagens que os nossos scripts entendam.

Para manter a organização, abra **novas abas do terminal** (usando o ícone do terminal na interface ou screen/tmux) para cada um dos drivers abaixo. 

Em **cada novo terminal/aba**, você **DEVE** sempre rodar estes dois comandos antes de mais nada:
```bash
source /opt/ros/jazzy/setup.bash
source ~/agri_scout_ws/install/setup.bash
```

### Terminal A (Arduino - Motores, Encoders, Ultrassom)
Certifique-se de que o Arduino está conectado via cabo USB e inicie o agente micro-ROS (se for micro-ROS) ou rosserial. Normalmente a porta é a `ttyUSB0`.
```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0
# Dica: Se falhar dizendo que a porta não existe, desconecte e conecte o Arduino 
# e rode 'dmesg | grep tty' para ver o nome correto (ex: ttyACM0).
```

### Terminal B (LiDAR - Sensor de varredura a laser)
Inicializa o pacote oficial da Lidar. Ajuste o nome do launch (.py) caso você utilize um modelo diferente.
```bash
ros2 launch rplidar_ros rplidar_a2m12_launch.py
```

### Terminal C (Câmera RealSense - Visão Computacional)
Inicializa o pacote que traduz a imagem USB em imagem ROS.
```bash
ros2 launch realsense2_camera rs_launch.py
```

**🤔 Como ter certeza que deu certo?** 
Abra um terminal qualquer, faça o `source` mágico (`source /opt/ros/jazzy/setup.bash`) e rode:
```bash
ros2 topic list
```
Você deverá ver uma lista grande de palavras como `/scan`, `/odom`, `/camera/color/image_raw`. Se eles apareceram, parabéns! Os sensores estão conversando corretamente.

---

## Passo 3: Executando os Testes de Hardware Práticos

Finalmente, com a base do sistema publicando dados nas veias do robô, vamos rodar seus scripts de teste. 
Volte para a raiz desse README:
```bash
cd ~/AGRI-Scout/hardware_tests/
```

Dê permissão de execução a todos os scripts (só precisa fazer uma única vez na vida):
```bash
chmod +x *.py
```

E os execute um a um na ordem sugerida:

### 1. Monitor do Sistema (Coração da Operação)
```bash
./system_monitor.py
```
* **🔍 O que verificar:** Se o uso de CPU está aceitável (abaixo de 80%), a Temperatura não está ultrapassando os 75-80°C (evitando danos ao chip) e a Memória RAM não está enforcada (100% de uso).

### 2. LiDAR e Câmera (Sensores de Alto Débito)
Estes são os sensores que emitem a maior carga de dados pelo cabo USB.
```bash
./test_lidar.py
./test_camera.py
```
* **🔍 O que verificar:** A frequência (Hz) de publicação está rápida e consistente? O LiDAR tem pontos na nuvem de scan? A Câmera abre e retorna pelo menos o formato dos quadros (ex: 640x480)?

### 3. IMU e GPS (Sensores de Posicionamento Espacial)
```bash
./test_imu_gps.py
```
* **🔍 O que verificar:** A orientação X, Y, Z da IMU não fica girando loucamente quando o robô está perfeitamente parado no chão. O GPS consegue sinal de satélite (Fix Status válido) em um ambiente externo.

### 4. Sensores Ultrassônicos (Parachoque frontal e laterais)
```bash
./test_ultrasound.py
```
* **🔍 O que verificar:** Coloque a sua mão na frente de cada um dos sensores e observe no terminal se a distância que aparece vai cair corretamente e vai acompanhar a distância real da sua mão. 

### 5. Motores (Odometria e Acionamento) ✨ ALTO RISCO ✨
⚠️ **RECOMENDADO:** Erga as rodas do robô e coloque ele sobre um banco/cerâmica firme na sua primeira tentativa para evitar que o robô de fato dispare e atropele alguém.
```bash
./test_motors.py
```
* **🔍 O que verificar:** 
  1. Ao pressionar `W`, ambas as esteiras/rodas vão para frente?
  2. O valor de odometria cresce de forma condizente?
  3. Pressione `A` (girar esquerda) e `D` (girar direita) - ele gira para o lado correto? 
  4. Pressione e segure `ESPAÇO` para garantir o freio instantâneo do drive.

---
**🛠️ Dica de Ouro / Troubleshooting Geral:** 
Se ao subir qualquer dos testes do **Passo 3** você ler algo como *"Aguardando dados...*" permanentemente no terminal (por mais de 10 segundos) e nada mais acontecer: **O seu driver tombou.**
Isso significa que o Passo 2 de alguma forma falhou. Volte ao terminal daquele driver, aperte `Ctrl+C` para matar o processo, cheque as conexões dos cabos na porta USB e inicie ele novamente. 
