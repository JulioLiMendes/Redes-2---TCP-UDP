#!/usr/bin/env python3
# =============================================================
# run_completo.py — Orquestra testes + captura tcpdump juntos
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
#
# Este script roda no container CLIENTE e:
#   1. Aplica o cenário de rede (tc)
#   2. Inicia o tcpdump em background no próprio cliente
#   3. Executa as transferências (TCP ou R-UDP)
#   4. Encerra o tcpdump e salva o .pcap
#   5. Repete para cada cenário
#
# Uso: python3 /app/scripts/run_completo.py [tcp|rudp|todos]
# =============================================================

import os
import sys
import time
import signal
import subprocess
from datetime import datetime

sys.path.insert(0, '/app')
from config import LOG_DIR, PORTA_TCP, PORTA_UDP

ARQUIVO_TESTE = "/app/logs/arquivo_teste.bin"
TAMANHO_MB    = 5
N_EXECUCOES   = 15
CENARIOS      = ["A", "B", "C"]
SETUP_TC      = "/app/scripts/setup_tc.sh"
CLIENTE_TCP   = "/app/cliente/cliente_tcp.py"
CLIENTE_RUDP  = "/app/cliente/cliente_rudp.py"
PCAP_DIR      = os.path.join(LOG_DIR, "pcap")
PAUSA_ENTRE   = 1.5

os.makedirs(PCAP_DIR, exist_ok=True)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ORQUESTRADOR] {msg}")


def gerar_arquivo_teste():
    tamanho = TAMANHO_MB * 1024 * 1024
    if os.path.exists(ARQUIVO_TESTE) and os.path.getsize(ARQUIVO_TESTE) == tamanho:
        log("Arquivo de teste já existe.")
        return
    log(f"Gerando arquivo de teste de {TAMANHO_MB}MB...")
    with open(ARQUIVO_TESTE, "wb") as f:
        f.write(os.urandom(tamanho))
    log("Arquivo de teste criado.")


def aplicar_cenario(cenario):
    log(f"Aplicando Cenário {cenario}...")
    subprocess.run(["bash", SETUP_TC, cenario], capture_output=True)
    time.sleep(1)


def iniciar_captura(protocolo, cenario):
    """Inicia o tcpdump em background e retorna o processo."""
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = os.path.join(PCAP_DIR, f"{protocolo}_cenario{cenario}_{ts}.pcap")

    if protocolo == "tcp":
        filtro = f"tcp port {PORTA_TCP}"
    elif protocolo == "rudp":
        filtro = f"udp port {PORTA_UDP}"
    else:
        filtro = f"port {PORTA_TCP} or port {PORTA_UDP}"

    log(f"Iniciando tcpdump | filtro: '{filtro}' | saída: {arquivo}")

    proc = subprocess.Popen(
        ["tcpdump", "-i", "eth0", "-w", arquivo, "-n", filtro],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.5)  # Dá tempo ao tcpdump inicializar
    return proc, arquivo


def encerrar_captura(proc, arquivo):
    """Encerra o tcpdump e confirma o arquivo gerado."""
    proc.send_signal(signal.SIGINT)
    proc.wait(timeout=5)
    time.sleep(0.3)

    if os.path.exists(arquivo):
        tamanho = os.path.getsize(arquivo)
        log(f"Captura encerrada: {os.path.basename(arquivo)} ({tamanho:,} bytes)")
    else:
        log(f"AVISO: Arquivo de captura não encontrado: {arquivo}")


def executar_tcp(cenario):
    log(f"=== TCP | Cenário {cenario} | {N_EXECUCOES} execuções ===")
    proc, arquivo = iniciar_captura("tcp", cenario)

    for i in range(1, N_EXECUCOES + 1):
        log(f"TCP execução {i}/{N_EXECUCOES}")
        subprocess.run(
            ["python3", CLIENTE_TCP, ARQUIVO_TESTE, cenario, str(i)]
        )
        time.sleep(PAUSA_ENTRE)

    encerrar_captura(proc, arquivo)


def executar_rudp(cenario):
    log(f"=== R-UDP | Cenário {cenario} | {N_EXECUCOES} execuções ===")
    proc, arquivo = iniciar_captura("rudp", cenario)

    for i in range(1, N_EXECUCOES + 1):
        log(f"R-UDP execução {i}/{N_EXECUCOES}")
        subprocess.run(
            ["python3", CLIENTE_RUDP, ARQUIVO_TESTE, cenario, str(i)]
        )
        time.sleep(PAUSA_ENTRE * 2)  # R-UDP precisa de mais intervalo

    encerrar_captura(proc, arquivo)


def main():
    modo = sys.argv[1].lower() if len(sys.argv) > 1 else "todos"

    if modo not in ["tcp", "rudp", "todos"]:
        print("Uso: python3 run_completo.py [tcp|rudp|todos]")
        print("  tcp   → apenas testes TCP com captura")
        print("  rudp  → apenas testes R-UDP com captura")
        print("  todos → TCP e R-UDP (certifique-se que ambos servidores estão ativos)")
        sys.exit(1)

    print("=" * 60)
    print(f"  TESTES COMPLETOS COM CAPTURA — Modo: {modo.upper()}")
    print(f"  {N_EXECUCOES} execuções x {len(CENARIOS)} cenários")
    print("=" * 60)

    gerar_arquivo_teste()

    for cenario in CENARIOS:
        aplicar_cenario(cenario)

        if modo in ["tcp", "todos"]:
            executar_tcp(cenario)

        if modo in ["rudp", "todos"]:
            executar_rudp(cenario)

    # Remove regras tc ao final
    subprocess.run(["bash", SETUP_TC, "reset"], capture_output=True)

    log("Convertendo capturas para CSV...")
    subprocess.run(["python3", "/app/scripts/pcap_para_csv.py"])

    print("\n" + "=" * 60)
    print("  CONCLUÍDO!")
    print(f"  .pcap em : {PCAP_DIR}")
    print(f"  CSVs em  : {LOG_DIR}/pcap_csv/")
    print(f"  Logs em  : {LOG_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
