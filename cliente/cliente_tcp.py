import socket
import os
import sys
import time
import json
import csv
from datetime import datetime

sys.path.insert(0, '/app')
from config import HOST_SERVIDOR, PORTA_TCP, X_CUSTOM_AUTH, TAMANHO_CHUNK, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE     = os.path.join(LOG_DIR, "cliente_tcp.log")
CSV_RESULTADOS = os.path.join(LOG_DIR, "resultados_tcp.csv")


def log(msg):
    linha = f"[{datetime.now().strftime('%H:%M:%S.%f')}] [TCP-CLIENTE] {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")


def salvar_csv(cenario, execucao, duracao, throughput, bytes_enviados, sucesso):
    """Salva o resultado desta execução no CSV de resultados."""
    arquivo_novo = not os.path.exists(CSV_RESULTADOS)

    with open(CSV_RESULTADOS, "a", newline="") as f:
        writer = csv.writer(f)
        if arquivo_novo:
            writer.writerow([
                "timestamp", "protocolo", "cenario", "execucao",
                "duracao_s", "throughput_mbps", "bytes_enviados", "sucesso"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            "TCP",
            cenario,
            execucao,
            f"{duracao:.6f}",
            f"{throughput:.6f}",
            bytes_enviados,
            sucesso
        ])
    log(f"Resultado salvo em {CSV_RESULTADOS}")


def enviar_arquivo(caminho_arquivo: str, cenario: str, execucao: int = 1):
    """Envia um arquivo ao servidor TCP e registra as métricas."""

    if not os.path.exists(caminho_arquivo):
        log(f"ERRO: Arquivo '{caminho_arquivo}' não encontrado.")
        sys.exit(1)

    nome_arquivo  = os.path.basename(caminho_arquivo)
    tamanho_total = os.path.getsize(caminho_arquivo)

    log(f"=== Execução {execucao} | Cenário {cenario} ===")
    log(f"Arquivo : {nome_arquivo} ({tamanho_total} bytes)")
    log(f"Destino : {HOST_SERVIDOR}:{PORTA_TCP}")

    sucesso = False
    duracao = 0.0
    throughput = 0.0

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST_SERVIDOR, PORTA_TCP))
            log("Conexão estabelecida.")
            header = {
                "X-Custom-Auth": X_CUSTOM_AUTH,
                "filename"      : nome_arquivo,
                "filesize"      : tamanho_total,
                "cenario"       : cenario,
                "execucao"      : execucao,
                "protocolo"     : "TCP"
            }
            raw_header = json.dumps(header).ljust(512).encode()
            s.sendall(raw_header)

            resposta = s.recv(16).decode().strip()
            if resposta != "READY":
                log(f"Servidor recusou conexão: {resposta}")
                return

            log("Servidor pronto. Iniciando envio...")

            bytes_enviados = 0
            inicio = time.perf_counter()

            with open(caminho_arquivo, "rb") as f:
                while True:
                    chunk = f.read(TAMANHO_CHUNK)
                    if not chunk:
                        break
                    s.sendall(chunk)
                    bytes_enviados += len(chunk)

            fim = time.perf_counter()

            confirmacao = s.recv(16).decode().strip()
            sucesso = (confirmacao == "OK")

            duracao    = fim - inicio
            throughput = (bytes_enviados * 8) / (duracao * 1_000_000) 

            log(f"Transferência {'CONCLUÍDA' if sucesso else 'COM ERRO'}!")
            log(f"  Bytes enviados  : {bytes_enviados}")
            log(f"  Duração         : {duracao:.4f}s")
            log(f"  Throughput      : {throughput:.4f} Mbps")

    except ConnectionRefusedError:
        log("ERRO: Servidor não está rodando. Inicie o servidor_tcp.py primeiro.")
    except Exception as e:
        log(f"ERRO inesperado: {e}")
    finally:
        salvar_csv(cenario, execucao, duracao, throughput,
                   tamanho_total, sucesso)

    return duracao, throughput

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 cliente_tcp.py <arquivo> <cenario> [execucao]")
        print("  Ex: python3 cliente_tcp.py /app/teste.bin A 1")
        sys.exit(1)

    arquivo  = sys.argv[1]
    cenario  = sys.argv[2].upper()
    execucao = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    enviar_arquivo(arquivo, cenario, execucao)
