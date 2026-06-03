import socket
import os
import sys
import time
import json
import csv
from datetime import datetime

sys.path.insert(0, '/app')
from config import (HOST_SERVIDOR, PORTA_UDP, X_CUSTOM_AUTH,
                    TAMANHO_CHUNK, TIMEOUT_RUDP, MAX_TENTATIVAS, LOG_DIR)
from protocolo_rudp import (
    montar_pacote, montar_syn, montar_fin, desmontar_pacote,
    TIPO_ACK, TIPO_NACK, TIPO_SYNACK, TIPO_DATA,
    TAMANHO_CABECALHO, nome_tipo
)

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE       = os.path.join(LOG_DIR, "cliente_rudp.log")
CSV_RESULTADOS = os.path.join(LOG_DIR, "resultados_rudp.csv")
BUFFER_SIZE    = TAMANHO_CHUNK + TAMANHO_CABECALHO + 64


def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [RUDP-CLIENTE] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")


def salvar_csv(cenario, execucao, duracao, throughput,
               bytes_enviados, retransmissoes, sucesso):
    novo = not os.path.exists(CSV_RESULTADOS)
    with open(CSV_RESULTADOS, "a", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["timestamp", "protocolo", "cenario", "execucao",
                         "duracao_s", "throughput_mbps", "bytes_enviados",
                         "retransmissoes", "sucesso"])
        w.writerow([
            datetime.now().isoformat(), "R-UDP", cenario, execucao,
            f"{duracao:.6f}", f"{throughput:.6f}",
            bytes_enviados, retransmissoes, sucesso
        ])
    log(f"Resultado salvo em {CSV_RESULTADOS}")


def enviar_com_retry(sock, pacote, tipo_esperado, seq_num, addr_servidor):
    """
    Stop-and-Wait: envia um pacote e aguarda ACK.
    Retransmite até MAX_TENTATIVAS em caso de timeout ou NACK.
    Retorna (True, n_retransmissoes) ou (False, n_retransmissoes).
    """
    retrans = 0
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        sock.sendto(pacote, addr_servidor)
        if tentativa == 1:
            log(f"  -> Enviado seq={seq_num}")
        else:
            log(f"  -> Retransmissão seq={seq_num} | tentativa {tentativa}/{MAX_TENTATIVAS}")
            retrans += 1

        try:
            raw, _ = sock.recvfrom(BUFFER_SIZE)
            resp   = desmontar_pacote(raw)
            tipo_r = resp["tipo"]
            seq_r  = resp["seq_num"]

            log(f"  <- [{nome_tipo(tipo_r)}] seq={seq_r}")

            if tipo_r == tipo_esperado and seq_r == seq_num:
                return True, retrans

            if tipo_r == TIPO_NACK and seq_r == seq_num:
                log(f"  ! NACK recebido — retransmitindo seq={seq_num}")
                continue

            log(f"  ! Resposta inesperada: {nome_tipo(tipo_r)} seq={seq_r}")

        except socket.timeout:
            log(f"  ! Timeout seq={seq_num} (tentativa {tentativa})")

    log(f"  !! FALHA: seq={seq_num} não confirmado após {MAX_TENTATIVAS} tentativas")
    return False, retrans


def enviar_arquivo(caminho_arquivo: str, cenario: str, execucao: int = 1):
    if not os.path.exists(caminho_arquivo):
        log(f"ERRO: Arquivo '{caminho_arquivo}' não encontrado.")
        sys.exit(1)

    nome_arquivo  = os.path.basename(caminho_arquivo)
    tamanho_total = os.path.getsize(caminho_arquivo)
    addr_servidor = (HOST_SERVIDOR, PORTA_UDP)

    log(f"=== Execução {execucao} | Cenário {cenario} ===")
    log(f"Arquivo  : {nome_arquivo} ({tamanho_total} bytes)")
    log(f"Destino  : {HOST_SERVIDOR}:{PORTA_UDP}")
    log(f"Timeout  : {TIMEOUT_RUDP}s | Max tentativas: {MAX_TENTATIVAS}")

    sucesso        = False
    duracao        = 0.0
    throughput     = 0.0
    retransmissoes = 0

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(TIMEOUT_RUDP)

        # ── 1) Handshake SYN ──────────────────────────────────
        meta = json.dumps({
            "filename" : nome_arquivo,
            "filesize" : tamanho_total,
            "cenario"  : cenario,
            "execucao" : execucao,
            "protocolo": "R-UDP"
        }).encode()

        syn       = montar_syn(X_CUSTOM_AUTH, meta)
        synack_ok = False

        log("Enviando SYN...")
        for t in range(1, MAX_TENTATIVAS + 1):
            sock.sendto(syn, addr_servidor)
            try:
                raw, _ = sock.recvfrom(BUFFER_SIZE)
                resp   = desmontar_pacote(raw)
                if resp["tipo"] == TIPO_SYNACK:
                    log("SYN-ACK recebido! Iniciando transferência.")
                    synack_ok = True
                    break
            except socket.timeout:
                log(f"Timeout aguardando SYN-ACK (tentativa {t}/{MAX_TENTATIVAS})")

        if not synack_ok:
            log("ERRO: Servidor não respondeu ao SYN. Abortando.")
            salvar_csv(cenario, execucao, 0, 0, 0, 0, False)
            return

        seq_num        = 1
        bytes_enviados = 0
        inicio         = time.perf_counter()

        with open(caminho_arquivo, "rb") as f:
            while True:
                chunk = f.read(TAMANHO_CHUNK)
                if not chunk:
                    break

                pacote     = montar_pacote(TIPO_DATA, seq_num, X_CUSTOM_AUTH, chunk)
                ok, retrans = enviar_com_retry(sock, pacote, TIPO_ACK,
                                               seq_num, addr_servidor)
                retransmissoes += retrans

                if not ok:
                    log(f"ERRO: Pacote seq={seq_num} não confirmado. Abortando.")
                    salvar_csv(cenario, execucao, 0, 0, bytes_enviados,
                               retransmissoes, False)
                    return

                bytes_enviados += len(chunk)
                seq_num        += 1

        fim = time.perf_counter()

        log("Enviando FIN...")
        fin          = montar_fin(seq_num, X_CUSTOM_AUTH)
        fin_ok, rtr  = enviar_com_retry(sock, fin, TIPO_ACK, seq_num, addr_servidor)
        retransmissoes += rtr

        sucesso    = fin_ok
        duracao    = fim - inicio
        throughput = (bytes_enviados * 8) / (duracao * 1_000_000) if duracao > 0 else 0

        log(f"Transferência {'CONCLUÍDA' if sucesso else 'INCOMPLETA'}!")
        log(f"  Bytes enviados   : {bytes_enviados}")
        log(f"  Duração          : {duracao:.4f}s")
        log(f"  Throughput       : {throughput:.4f} Mbps")
        log(f"  Retransmissões   : {retransmissoes}")
        log(f"  Seq final        : {seq_num}")

    salvar_csv(cenario, execucao, duracao, throughput,
               bytes_enviados, retransmissoes, sucesso)

    return duracao, throughput


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 cliente_rudp.py <arquivo> <cenario> [execucao]")
        print("  Ex: python3 cliente_rudp.py /app/logs/teste.bin A 1")
        sys.exit(1)

    arquivo  = sys.argv[1]
    cenario  = sys.argv[2].upper()
    execucao = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    enviar_arquivo(arquivo, cenario, execucao)
