-> Primeira etapa:
Conexão Direta Ethernet (Cabo RJ45)
Conecte o Cabo: Ligue o cabo de rede entre a Raspberry Pi e o seu Computador.

No seu Computador (Ubuntu):

Vá em Configurações (Settings) > Rede (Network).

Encontre a conexão Cabeada (Wired)

Vá na aba IPv4.

Mude o "Método" de Automático (DHCP) para Compartilhado com outros computadores (Shared to other computers).

Clique em Aplicar.

Desligue e ligue o botão da conexão cabeada para reiniciar a interface.

O que isso faz? O seu computador vai criar uma pequena rede privada e ele mesmo vai dar um IP para a Raspberry Pi. Isso elimina problemas de Wi-Fi da universidade e IPs que mudam sozinhos.

-> Segunda etapa:
Após 30s, Ping pelo nome (mDNS): ping ubuntu.local;
Descobrindo ip: arp -a;
ssh ubuntu@10.42.0.X  (o IP encontrado no arp)
