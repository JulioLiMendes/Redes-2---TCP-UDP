#!/usr/bin/env python3
# =============================================================
# pcap_para_csv.py — Converte capturas .pcap em CSV analisável
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# Uso: python3 pcap_para_csv.py
# =============================================================

import os
import sys
import subprocess
import csv
import struct
import re
from datetime import datetime

LOG_DIR  = "/app/logs"
PCAP_DIR = os.path.join(LOG_DIR, "pcap")
CSV_DIR  = os.path.join(LOG_DIR, "pcap_csv")

os.makedirs(CSV_DIR, exist_ok=True)

PORTA_TCP = 5000
PORTA_UDP = 5001


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def tcpdump_disponivel():
    """Verifica se tcpdump está instalado."""
    r = subprocess.run(["which", "tcpdump"], capture_output=True)
    return r.returncode == 0


def converter_pcap_com_tcpdump(pcap_path: str, csv_path: str):
    """
    Usa tcpdump -r para ler o .pcap e extrai campos relevantes.
    Salva em CSV com: timestamp, protocolo, src_ip, dst_ip,
                      src_port, dst_port, tamanho_bytes, flags, info
    """
    log(f"Convertendo: {os.path.basename(pcap_path)}")

    cmd = [
        "tcpdump", "-r", pcap_path,
        "-n",          # Não resolve hostnames
        "-tt",         # Timestamp em Unix epoch
        "-q",          # Saída resumida
        "-v"           # Verboso (inclui tamanho)
    ]

    resultado = subprocess.run(cmd, capture_output=True, text=True)
    linhas    = resultado.stdout.strip().split("\n")

    registros = []
    for linha in linhas:
        if not linha.strip():
            continue
        r = parsear_linha_tcpdump(linha)
        if r:
            registros.append(r)

    if not registros:
        log(f"  Nenhum pacote encontrado em {pcap_path}")
        return 0

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp_unix", "protocolo", "src_ip", "src_port",
            "dst_ip", "dst_port", "tamanho_bytes", "flags", "info_extra"
        ])
        writer.writeheader()
        writer.writerows(registros)

    log(f"  {len(registros)} pacotes salvos em {csv_path}")
    return len(registros)


def parsear_linha_tcpdump(linha: str) -> dict:
    """
    Extrai campos de uma linha de saída do tcpdump.
    Exemplo TCP:
      1748000000.123456 IP 172.20.0.20.12345 > 172.20.0.10.5000: Flags [P.], length 4174
    Exemplo UDP:
      1748000000.123456 IP 172.20.0.20.54321 > 172.20.0.10.5001: UDP, length 4174
    """
    try:
        partes = linha.split()
        if len(partes) < 5:
            return None

        timestamp = partes[0]

        # Detecta protocolo pela porta
        protocolo = "OUTRO"
        src_raw   = ""
        dst_raw   = ""

        for i, p in enumerate(partes):
            if p == "IP" and i + 3 < len(partes):
                src_raw = partes[i + 1]
                dst_raw = partes[i + 3].rstrip(":")
                break

        if not src_raw:
            return None

        src_parts = src_raw.rsplit(".", 1)
        dst_parts = dst_raw.rsplit(".", 1)

        src_ip   = src_parts[0] if len(src_parts) == 2 else src_raw
        src_port = src_parts[1] if len(src_parts) == 2 else "0"
        dst_ip   = dst_parts[0] if len(dst_parts) == 2 else dst_raw
        dst_port = dst_parts[1] if len(dst_parts) == 2 else "0"

        # Classifica por porta
        if str(PORTA_TCP) in [src_port, dst_port]:
            protocolo = "TCP"
        elif str(PORTA_UDP) in [src_port, dst_port]:
            protocolo = "UDP_RUDP"

        # Extrai tamanho
        tamanho = 0
        for i, p in enumerate(partes):
            if p == "length" and i + 1 < len(partes):
                try:
                    tamanho = int(partes[i + 1].rstrip(","))
                except ValueError:
                    pass
                break

        # Extrai flags TCP
        flags = ""
        m = re.search(r"Flags \[([^\]]+)\]", linha)
        if m:
            flags = m.group(1)

        return {
            "timestamp_unix": timestamp,
            "protocolo"     : protocolo,
            "src_ip"        : src_ip,
            "src_port"      : src_port,
            "dst_ip"        : dst_ip,
            "dst_port"      : dst_port,
            "tamanho_bytes" : tamanho,
            "flags"         : flags,
            "info_extra"    : linha[linha.find(dst_raw) + len(dst_raw):].strip()
        }

    except Exception:
        return None


def gerar_resumo_pcap(csv_path: str, pcap_nome: str):
    """Lê o CSV gerado e imprime estatísticas básicas."""
    if not os.path.exists(csv_path):
        return

    pacotes        = []
    total_bytes    = 0
    primeiro_ts    = None
    ultimo_ts      = None

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pacotes.append(row)
            total_bytes += int(row["tamanho_bytes"])
            ts = float(row["timestamp_unix"])
            if primeiro_ts is None or ts < primeiro_ts:
                primeiro_ts = ts
            if ultimo_ts is None or ts > ultimo_ts:
                ultimo_ts = ts

    if not pacotes:
        return

    duracao    = (ultimo_ts - primeiro_ts) if ultimo_ts and primeiro_ts else 0
    throughput = (total_bytes * 8) / (duracao * 1_000_000) if duracao > 0 else 0

    print(f"\n  --- Resumo: {pcap_nome} ---")
    print(f"  Total de pacotes : {len(pacotes)}")
    print(f"  Total de bytes   : {total_bytes:,}")
    print(f"  Duração captura  : {duracao:.4f}s")
    print(f"  Throughput médio : {throughput:.4f} Mbps")


def processar_todos():
    """Converte todos os .pcap da pasta pcap/ para CSV."""
    if not tcpdump_disponivel():
        log("ERRO: tcpdump não encontrado. Execute dentro do container!")
        sys.exit(1)

    arquivos_pcap = [
        f for f in os.listdir(PCAP_DIR)
        if f.endswith(".pcap")
    ]

    if not arquivos_pcap:
        log(f"Nenhum arquivo .pcap encontrado em {PCAP_DIR}")
        log("Execute os testes primeiro e use captura_tcpdump.sh para capturar.")
        return

    log(f"Encontrados {len(arquivos_pcap)} arquivo(s) .pcap")
    log(f"Saída dos CSVs em: {CSV_DIR}")

    total_convertidos = 0
    for nome_pcap in sorted(arquivos_pcap):
        pcap_path = os.path.join(PCAP_DIR, nome_pcap)
        csv_nome  = nome_pcap.replace(".pcap", ".csv")
        csv_path  = os.path.join(CSV_DIR, csv_nome)

        n = converter_pcap_com_tcpdump(pcap_path, csv_path)
        if n > 0:
            gerar_resumo_pcap(csv_path, nome_pcap)
            total_convertidos += 1

    print(f"\n{'='*50}")
    print(f"  {total_convertidos} arquivo(s) convertido(s) com sucesso!")
    print(f"  CSVs disponíveis em: {CSV_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    processar_todos()
