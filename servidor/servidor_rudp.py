# =============================================================
# servidor_rudp.py — Servidor R-UDP (Stop-and-Wait)
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket
import os
import sys
import time
import json
import csv
from datetime import datetime

sys.path.insert(0, '/app')
from config import HOST_SERVIDOR, PORTA_UDP, X_CUSTOM_AUTH, TAMANHO_CHUNK, LOG_DIR
from protocolo_rudp import (
    desmontar_pacote, montar_ack, montar_nack, montar_synack,
    TIPO_DATA, TIPO_SYN, TIPO_FIN,
    TAMANHO_CABECALHO, nome_tipo
)

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE       = os.path.join(LOG_DIR, "servidor_rudp.log")
CSV_RESULTADOS = os.path.join(LOG_DIR, "resultados_rudp.csv")

BUFFER_SIZE = TAMANHO_CHUNK + TAMANHO_CABECALHO + 64


def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [RUDP-SERVIDOR] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")


def validar_auth(auth: str) -> bool:
    ok = (auth.strip('\x00') == X_CUSTOM_AUTH)
    if not ok:
        log(f"FALHA AUTH: recebido '{auth[:16]}...'")
    return ok


def salvar_csv(cenario, duracao, throughput, bytes_recebidos,
               total_pacotes, retransmissoes, sucesso):
    novo = not os.path.exists(CSV_RESULTADOS)
    with open(CSV_RESULTADOS, "a", newline="") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["timestamp", "protocolo", "cenario", "duracao_s",
                         "throughput_mbps", "bytes_recebidos",
                         "total_pacotes", "retransmissoes", "sucesso"])
        w.writerow([
            datetime.now().isoformat(), "R-UDP", cenario,
            f"{duracao:.6f}", f"{throughput:.6f}",
            bytes_recebidos, total_pacotes, retransmissoes, sucesso
        ])


def receber_arquivo(sock, addr_cliente, header_meta):
    nome_arquivo   = header_meta["filename"]
    tamanho_total  = header_meta["filesize"]
    cenario        = header_meta.get("cenario", "?")

    log(f"Início da transferência R-UDP")
    log(f"  Arquivo  : {nome_arquivo} ({tamanho_total} bytes)")
    log(f"  Cenário  : {cenario}")
    log(f"  Cliente  : {addr_cliente}")

    destino         = os.path.join(LOG_DIR, f"recebido_rudp_{nome_arquivo}")
    seq_esperado    = 1
    bytes_recebidos = 0
    total_pacotes   = 0
    retransmissoes  = 0
    sucesso         = False
    inicio          = time.perf_counter()

    with open(destino, "wb") as f_out:
        while True:
            try:
                raw, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                log("Timeout aguardando pacote — encerrando sessão.")
                break

            total_pacotes += 1

            try:
                pkt = desmontar_pacote(raw)
            except Exception as e:
                log(f"Erro ao desmontar pacote: {e}")
                continue

            tipo    = pkt["tipo"]
            seq_num = pkt["seq_num"]

            log(f"  <- [{nome_tipo(tipo)}] seq={seq_num} | "
                f"{'OK' if pkt['integro'] else 'CORROMPIDO'} | "
                f"{pkt['payload_len']} bytes")

            # FIN — fim da transferência
            if tipo == TIPO_FIN:
                ack = montar_ack(seq_num, X_CUSTOM_AUTH)
                sock.sendto(ack, addr)
                log(f"  -> [ACK] seq={seq_num} (FIN confirmado)")
                sucesso = True
                break

            # DATA
            if tipo == TIPO_DATA:
                if not validar_auth(pkt["auth"]):
                    continue

                # Checksum inválido — envia NACK
                if not pkt["integro"]:
                    nack = montar_nack(seq_num, X_CUSTOM_AUTH)
                    sock.sendto(nack, addr)
                    log(f"  -> [NACK] seq={seq_num} (checksum inválido)")
                    retransmissoes += 1
                    continue

                # Pacote duplicado — reconfirma ACK
                if seq_num < seq_esperado:
                    ack = montar_ack(seq_num, X_CUSTOM_AUTH)
                    sock.sendto(ack, addr)
                    log(f"  -> [ACK] seq={seq_num} (duplicado, ignorado)")
                    retransmissoes += 1
                    continue

                # Fora de ordem (não esperado no Stop-and-Wait)
                if seq_num != seq_esperado:
                    log(f"  ! Fora de ordem: esperado {seq_esperado}, recebido {seq_num}")
                    continue

                # Pacote correto — grava e confirma
                f_out.write(pkt["payload"])
                bytes_recebidos += pkt["payload_len"]
                seq_esperado    += 1

                ack = montar_ack(seq_num, X_CUSTOM_AUTH)
                sock.sendto(ack, addr)
                log(f"  -> [ACK] seq={seq_num} | "
                    f"{bytes_recebidos}/{tamanho_total} bytes recebidos")

    fim        = time.perf_counter()
    duracao    = fim - inicio
    throughput = (bytes_recebidos * 8) / (duracao * 1_000_000) if duracao > 0 else 0

    log(f"Transferência {'CONCLUÍDA' if sucesso else 'INCOMPLETA'}!")
    log(f"  Bytes recebidos : {bytes_recebidos}")
    log(f"  Duração         : {duracao:.4f}s")
    log(f"  Throughput      : {throughput:.4f} Mbps")
    log(f"  Total pacotes   : {total_pacotes}")
    log(f"  Retransmissões  : {retransmissoes}")

    salvar_csv(cenario, duracao, throughput, bytes_recebidos,
               total_pacotes, retransmissoes, sucesso)


def iniciar_servidor():
    log(f"Iniciando servidor R-UDP em {HOST_SERVIDOR}:{PORTA_UDP}")
    log(f"X-Custom-Auth: {X_CUSTOM_AUTH[:16]}...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST_SERVIDOR, PORTA_UDP))
        sock.settimeout(60)
        log("Aguardando SYN do cliente...")

        while True:
            try:
                raw, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                log("Aguardando nova sessão...")
                continue

            try:
                pkt = desmontar_pacote(raw)
            except Exception as e:
                log(f"Erro ao desmontar pacote inicial: {e}")
                continue

            if pkt["tipo"] == TIPO_SYN:
                if not validar_auth(pkt["auth"]):
                    continue

                try:
                    meta = json.loads(pkt["payload"].decode())
                except Exception:
                    log("Erro ao ler metadados do SYN.")
                    continue

                log(f"SYN recebido de {addr} | meta: {meta}")

                synack = montar_synack(X_CUSTOM_AUTH)
                sock.sendto(synack, addr)
                log(f"  -> [SYN-ACK] enviado para {addr}")

                sock.settimeout(10)
                receber_arquivo(sock, addr, meta)
                sock.settimeout(60)
                log("Aguardando nova sessão...\n")


if __name__ == "__main__":
    iniciar_servidor()
