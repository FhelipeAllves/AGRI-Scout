#!/bin/bash

# Limpa a tela
clear

echo "======================================"
echo "    AGRI-SCOUT VITAL MONITOR"
echo " Pressione Ctrl+C para sair"
echo "======================================"

while true; do
    # Traz o cursor para o começo sem limpar a tela inteira (evita flickering)
    tput cup 4 0
    echo -e "\n\033[1;36m[  TEMPERATURA DA CPU  ]\033[0m"
    vcgencmd measure_temp

    echo -e "\n\033[1;33m[ VOLTAGEM DO NÚCLEO (V)]\033[0m"
    vcgencmd measure_volts core

    echo -e "\n\033[1;31m[ SAÚDE DA ENERGIA (UNDERVOLT) ]\033[0m"
    THROTTLED=$(vcgencmd get_throttled)
    echo "$THROTTLED"
    if [ "$THROTTLED" != "throttled=0x0" ]; then
        echo -e "\033[1;31m► ALERTA: Queda de energia registrada! \033[0m"
    else
        echo -e "\033[1;32m► Alimentação OK \033[0m"
    fi

    echo -e "\n\033[1;32m[ CONSUMO DE MEMÓRIA ]\033[0m"
    free -h | grep "Mem" | awk '{print "Usado: "$3" / Livre: "$7}'

    sleep 1
done
