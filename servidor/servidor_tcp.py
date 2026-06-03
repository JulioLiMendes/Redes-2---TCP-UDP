# =============================================================
# servidor_tcp.py — Servidor de transferência de arquivos TCP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import socket
import os
import sys
import time
import json
import hashlib
from datetime import datetime

sys.path.insert(0, '/app')
from config import HOST_SERVIDOR, PORTA_TCP, X_CUSTOM_AUTH, TAMANHO_CHUNK, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "servidor_tcp.log")


def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [TCP-SERVIDOR] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")


def validar_auth(header: dict) -> bool:
    """Verifica se o X-Custom-Auth recebido é válido."""
    recebido = header.get("X-Custom-Auth", "")
    if recebido == X_CUSTOM_AUTH:
        log(f"Autenticação OK: {recebido[:16]}...")
        return True
    log(f"FALHA NA AUTENTICAÇÃO! Recebido: {recebido[:16]}...")
    return False


def receber_arquivo(conn, addr):
    """Recebe um arquivo de um cliente TCP conectado."""
    try:
        # 1) Recebe o header JSON (tamanho fixo de 512 bytes)
        raw_header = conn.recv(512)
        header = json.loads(raw_header.decode().strip())

        if not validar_auth(header):
            conn.sendall(b"AUTH_FAIL")
            return

        nome_arquivo = header["filename"]
        tamanho_total = header["filesize"]
        cenario       = header.get("cenario", "?")

        log(f"Conexão de {addr} | Arquivo: {nome_arquivo} | Tamanho: {tamanho_total} bytes | Cenário: {cenario}")

        # Confirma que está pronto para receber
        conn.sendall(b"READY")

        # 2) Recebe os dados do arquivo
        destino = os.path.join(LOG_DIR, f"recebido_tcp_{nome_arquivo}")
        bytes_recebidos = 0
        inicio = time.perf_counter()

        with open(destino, "wb") as f:
            while bytes_recebidos < tamanho_total:
                chunk = conn.recv(TAMANHO_CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                bytes_recebidos += len(chunk)

        fim = time.perf_counter()

        # 3) Calcula métricas
        duracao   = fim - inicio
        throughput = (bytes_recebidos * 8) / (duracao * 1_000_000)  # Mbps

        log(f"Transferência concluída!")
        log(f"  Bytes recebidos : {bytes_recebidos}")
        log(f"  Duração         : {duracao:.4f}s")
        log(f"  Throughput      : {throughput:.4f} Mbps")

        # 4) Envia confirmação final ao cliente
        conn.sendall(b"OK")

    except Exception as e:
        log(f"ERRO ao receber arquivo: {e}")
    finally:
        conn.close()


def iniciar_servidor():
    log(f"Iniciando servidor TCP em {HOST_SERVIDOR}:{PORTA_TCP}")
    log(f"X-Custom-Auth configurado: {X_CUSTOM_AUTH[:16]}...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST_SERVIDOR, PORTA_TCP))
        s.listen(10)
        log("Aguardando conexões...")

        while True:
            conn, addr = s.accept()
            log(f"Nova conexão aceita de {addr}")
            receber_arquivo(conn, addr)


if __name__ == "__main__":
    iniciar_servidor()
