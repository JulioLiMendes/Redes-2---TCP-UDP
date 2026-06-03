# Análise de Desempenho e Confiabilidade em Camadas de Transporte: TCP vs R-UDP

**Disciplina:** Redes de Computadores II  
**Instituição:** Universidade Federal do Piauí — Campus Senador Helvídio Nunes de Barros  
**Curso:** Bacharelado em Sistemas de Informação  
**Aluno:** Julio Cesar de Lima Mendes  
**Matrícula:** 20249006910  
**X-Custom-Auth (SHA-256):** `2f93fca4ad0be3570264caaf2010c07833a9889bd61b857b9681fd465d2fcf15`

---

## Sobre o Projeto

Este projeto implementa e compara dois sistemas de transferência de arquivos:

- **TCP** — Transferência via sockets TCP nativos do Python
- **R-UDP** — Transferência via UDP com camada de confiabilidade implementada manualmente (Stop-and-Wait)

Os testes são executados em três cenários de rede simulados com `tc/netem` em containers Docker, com captura de tráfego via `tcpdump` e análise estatística com Pandas e Matplotlib.

---

## Estrutura do Repositório

```
redes2/
├── Dockerfile               
├── docker-compose.yml         
├── config.py                   
├── protocolo_rudp.py           
│
├── cliente/
│   ├── cliente_tcp.py         
│   └── cliente_rudp.py    
│
├── servidor/
│   ├── servidor_tcp.py      
│   └── servidor_rudp.py  
│
├── scripts/
│   ├── setup_tc.sh     
│   ├── run_testes_tcp.py      
│   ├── run_testes_rudp.py   
│   ├── run_completo.py      
│   └── pcap_para_csv.py      
│
├── analise/
│   └── gerar_graficos.py     
│
├── logs/
│   ├── resultados_tcp.csv    
│   ├── resultados_rudp_limpo.csv 
│   └── graficos/         
│
└── wireshark - prints/       
```

---

## Protocolo R-UDP

O cabeçalho personalizado possui **78 bytes fixos**:

| Campo | Tamanho | Descrição |
|---|---|---|
| Tipo | 1 byte | DATA / ACK / NACK / SYN / FIN |
| Seq Num | 4 bytes | Número de sequência |
| Checksum | 4 bytes | CRC32 do payload |
| Payload Len | 4 bytes | Tamanho do payload |
| Auth Len | 1 byte | Tamanho do campo de autenticação |
| X-Custom-Auth | 64 bytes | SHA-256 (matrícula + nome) |

**Fluxo Stop-and-Wait:**
```
CLIENTE                    SERVIDOR
   |--- SYN (metadados) --->|
   |<-- SYN-ACK ------------|
   |--- DATA seq=1 -------->|
   |<-- ACK seq=1 ----------|
   |--- DATA seq=2 -------->|   ← aguarda ACK antes do próximo
   |<-- ACK seq=2 ----------|
   |--- FIN seq=N -------->|
   |<-- ACK seq=N ----------|
```

---

## Cenários de Rede

| Cenário | Perda | Delay | Descrição |
|---|---|---|---|
| A | 0% | 10ms | Rede ideal |
| B | 5% | 50ms | Rede degradada |
| C | 10% | 100ms | Alta perda e latência |

---

## Resultados

| Cenário | TCP (Mbps) | R-UDP (Mbps) | Fator |
|---|---|---|---|
| A | 81,4773 | 1,3021 | ~62x |
| B | 1,3616 | 0,0679 | ~20x |
| C | 0,4007 | 0,0025 | ~160x |

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) com WSL 2 habilitado
- Windows 10/11

---

## Como Executar

### 1. Subir os containers

```powershell
docker-compose up -d --build
```

### 2. Iniciar os servidores (dois terminais separados)

```powershell
# Terminal 1 — Servidor TCP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_tcp.py
```

```powershell
# Terminal 2 — Servidor R-UDP
docker exec -it redes2_servidor bash
python3 /app/servidor/servidor_rudp.py
```

### 3. Executar os testes completos com captura

```powershell
# Terminal 3 — Cliente
docker exec -it redes2_cliente bash
python3 /app/scripts/run_completo.py todos
```

Isso executa automaticamente 15 transferências por protocolo por cenário (90 no total), aplicando os cenários A, B e C com `tc/netem` e capturando o tráfego com `tcpdump`.

### 4. Gerar os gráficos

```powershell
docker exec -it redes2_cliente bash
python3 /app/analise/gerar_graficos.py
```

### 5. Copiar resultados para o Windows

```powershell
docker cp redes2_cliente:/app/logs "C:\caminho\destino\logs"
```

---

## Aplicar Cenário Manualmente

```bash
# Dentro do container cliente
bash /app/scripts/setup_tc.sh A      
bash /app/scripts/setup_tc.sh B   
bash /app/scripts/setup_tc.sh C 
bash /app/scripts/setup_tc.sh reset 
```

---

## Referências

- KUROSE, J. F.; ROSS, K. W. *Redes de Computadores e a Internet*. 8. ed. Pearson, 2021.
- TANENBAUM, A. S.; WETHERALL, D. *Redes de Computadores*. 5. ed. Pearson, 2011.
- POSTEL, J. *Transmission Control Protocol*. RFC 793, IETF, 1981.
- POSTEL, J. *User Datagram Protocol*. RFC 768, IETF, 1980.
- Docker Documentation. https://docs.docker.com
- tc-netem: Network Emulator. https://man7.org/linux/man-pages/man8/tc-netem.8.html
