#!/usr/bin/env python3
# =============================================================
# analise.py — Análise estatística TCP vs R-UDP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime

LOG_DIR    = "/app/logs"
GRAFICOS   = os.path.join(LOG_DIR, "graficos")
os.makedirs(GRAFICOS, exist_ok=True)

CENARIOS   = ["A", "B", "C"]
DESC_CEN   = {
    "A": "Cenário A\n(0% perda / 10ms)",
    "B": "Cenário B\n(5% perda / 50ms)",
    "C": "Cenário C\n(10% perda / 100ms)"
}

COR_TCP  = "#2196F3"   # azul
COR_RUDP = "#F44336"   # vermelho

# ─────────────────────────────────────────────
# 1. Carrega e limpa os dados
# ─────────────────────────────────────────────

def carregar_dados():
    tcp_path  = os.path.join(LOG_DIR, "resultados_tcp.csv")
    rudp_path = os.path.join(LOG_DIR, "resultados_rudp.csv")

    tcp  = pd.read_csv(tcp_path)
    rudp = pd.read_csv(rudp_path)

    # Mantém só execuções bem-sucedidas e com throughput > 0
    tcp  = tcp[(tcp["throughput_mbps"].astype(float) > 0)]
    rudp = rudp[(rudp["throughput_mbps"].astype(float) > 0)]

    tcp["throughput_mbps"]  = tcp["throughput_mbps"].astype(float)
    tcp["duracao_s"]        = tcp["duracao_s"].astype(float)
    rudp["throughput_mbps"] = rudp["throughput_mbps"].astype(float)
    rudp["duracao_s"]       = rudp["duracao_s"].astype(float)

    # Limita a 15 execuções por cenário para equidade
    tcp  = tcp.groupby("cenario").head(15).reset_index(drop=True)
    rudp = rudp.groupby("cenario").head(15).reset_index(drop=True)

    return tcp, rudp


def estatisticas(df, coluna="throughput_mbps"):
    return df.groupby("cenario")[coluna].agg(
        media="mean", desvio="std", minimo="min", maximo="max", n="count"
    ).reindex(CENARIOS)


# ─────────────────────────────────────────────
# 2. Tabela de estatísticas no terminal
# ─────────────────────────────────────────────

def imprimir_tabela(tcp, rudp):
    print("\n" + "="*70)
    print("  ESTATÍSTICAS — THROUGHPUT (Mbps)")
    print("="*70)
    print(f"{'Cenário':<10} {'Protocolo':<10} {'Média':>10} {'Desvio':>10} "
          f"{'Mín':>10} {'Máx':>10} {'N':>5}")
    print("-"*70)

    for c in CENARIOS:
        for proto, df in [("TCP", tcp), ("R-UDP", rudp)]:
            sub = df[df["cenario"] == c]["throughput_mbps"]
            if len(sub) == 0:
                continue
            print(f"{c:<10} {proto:<10} {sub.mean():>10.4f} {sub.std():>10.4f} "
                  f"{sub.min():>10.4f} {sub.max():>10.4f} {len(sub):>5}")
        print("-"*70)

    print("\n  ESTATÍSTICAS — DURAÇÃO (s)")
    print("="*70)
    print(f"{'Cenário':<10} {'Protocolo':<10} {'Média':>10} {'Desvio':>10} "
          f"{'Mín':>10} {'Máx':>10}")
    print("-"*70)

    for c in CENARIOS:
        for proto, df in [("TCP", tcp), ("R-UDP", rudp)]:
            sub = df[df["cenario"] == c]["duracao_s"]
            if len(sub) == 0:
                continue
            print(f"{c:<10} {proto:<10} {sub.mean():>10.4f} {sub.std():>10.4f} "
                  f"{sub.min():>10.4f} {sub.max():>10.4f}")
        print("-"*70)


# ─────────────────────────────────────────────
# 3. Gráfico 1 — Throughput médio com barra de erro
# ─────────────────────────────────────────────

def grafico_throughput_medio(tcp, rudp):
    est_tcp  = estatisticas(tcp)
    est_rudp = estatisticas(rudp)

    x      = np.arange(len(CENARIOS))
    largura = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    barras_tcp = ax.bar(x - largura/2, est_tcp["media"], largura,
                        yerr=est_tcp["desvio"], capsize=6,
                        color=COR_TCP, alpha=0.85, label="TCP",
                        error_kw={"elinewidth": 2, "ecolor": "navy"})

    barras_rudp = ax.bar(x + largura/2, est_rudp["media"], largura,
                         yerr=est_rudp["desvio"], capsize=6,
                         color=COR_RUDP, alpha=0.85, label="R-UDP",
                         error_kw={"elinewidth": 2, "ecolor": "darkred"})

    # Anotações com valor nas barras
    for bar in barras_tcp:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.01,
                f"{h:.3f}", ha="center", va="bottom", fontsize=9, color="navy")

    for bar in barras_rudp:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.01,
                f"{h:.3f}", ha="center", va="bottom", fontsize=9, color="darkred")

    ax.set_xlabel("Cenário de Rede", fontsize=12)
    ax.set_ylabel("Throughput Médio (Mbps)", fontsize=12)
    ax.set_title("Throughput Médio: TCP vs R-UDP por Cenário\n(barras de erro = desvio padrão)",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([DESC_CEN[c] for c in CENARIOS], fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    caminho = os.path.join(GRAFICOS, "01_throughput_medio.png")
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"[OK] Salvo: {caminho}")


# ─────────────────────────────────────────────
# 4. Gráfico 2 — Boxplot throughput
# ─────────────────────────────────────────────

def grafico_boxplot_throughput(tcp, rudp):
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=False)
    fig.suptitle("Distribuição do Throughput: TCP vs R-UDP por Cenário",
                 fontsize=13, fontweight="bold")

    for i, cenario in enumerate(CENARIOS):
        ax   = axes[i]
        d_tcp  = tcp[tcp["cenario"] == cenario]["throughput_mbps"].values
        d_rudp = rudp[rudp["cenario"] == cenario]["throughput_mbps"].values

        bp = ax.boxplot(
            [d_tcp, d_rudp],
            labels=["TCP", "R-UDP"],
            patch_artist=True,
            medianprops={"color": "black", "linewidth": 2},
            whiskerprops={"linewidth": 1.5},
            capprops={"linewidth": 1.5}
        )

        bp["boxes"][0].set_facecolor(COR_TCP)
        bp["boxes"][0].set_alpha(0.7)
        bp["boxes"][1].set_facecolor(COR_RUDP)
        bp["boxes"][1].set_alpha(0.7)

        ax.set_title(DESC_CEN[cenario], fontsize=10)
        ax.set_ylabel("Throughput (Mbps)" if i == 0 else "")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    caminho = os.path.join(GRAFICOS, "02_boxplot_throughput.png")
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"[OK] Salvo: {caminho}")


# ─────────────────────────────────────────────
# 5. Gráfico 3 — Duração média por cenário
# ─────────────────────────────────────────────

def grafico_duracao_media(tcp, rudp):
    est_tcp  = estatisticas(tcp,  "duracao_s")
    est_rudp = estatisticas(rudp, "duracao_s")

    x       = np.arange(len(CENARIOS))
    largura = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(x - largura/2, est_tcp["media"],  largura,
           yerr=est_tcp["desvio"],  capsize=6,
           color=COR_TCP,  alpha=0.85, label="TCP",
           error_kw={"elinewidth": 2})

    ax.bar(x + largura/2, est_rudp["media"], largura,
           yerr=est_rudp["desvio"], capsize=6,
           color=COR_RUDP, alpha=0.85, label="R-UDP",
           error_kw={"elinewidth": 2})

    ax.set_xlabel("Cenário de Rede", fontsize=12)
    ax.set_ylabel("Duração Média (s)", fontsize=12)
    ax.set_title("Duração Média da Transferência: TCP vs R-UDP\n(barras de erro = desvio padrão)",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([DESC_CEN[c] for c in CENARIOS], fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    caminho = os.path.join(GRAFICOS, "03_duracao_media.png")
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"[OK] Salvo: {caminho}")


# ─────────────────────────────────────────────
# 6. Gráfico 4 — Throughput por execução (linha)
# ─────────────────────────────────────────────

def grafico_throughput_por_execucao(tcp, rudp):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
    fig.suptitle("Throughput por Execução: TCP vs R-UDP",
                 fontsize=13, fontweight="bold")

    for i, cenario in enumerate(CENARIOS):
        ax     = axes[i]
        d_tcp  = tcp[tcp["cenario"] == cenario].reset_index(drop=True)
        d_rudp = rudp[rudp["cenario"] == cenario].reset_index(drop=True)

        ax.plot(range(1, len(d_tcp) + 1),  d_tcp["throughput_mbps"],
                "o-", color=COR_TCP,  label="TCP",   linewidth=2, markersize=5)
        ax.plot(range(1, len(d_rudp) + 1), d_rudp["throughput_mbps"],
                "s-", color=COR_RUDP, label="R-UDP", linewidth=2, markersize=5)

        # Linha de média
        ax.axhline(d_tcp["throughput_mbps"].mean(),  color=COR_TCP,
                   linestyle="--", alpha=0.6, linewidth=1.5)
        ax.axhline(d_rudp["throughput_mbps"].mean(), color=COR_RUDP,
                   linestyle="--", alpha=0.6, linewidth=1.5)

        ax.set_title(DESC_CEN[cenario], fontsize=10)
        ax.set_xlabel("Execução nº")
        ax.set_ylabel("Throughput (Mbps)" if i == 0 else "")
        ax.legend(fontsize=9)
        ax.grid(linestyle="--", alpha=0.4)
        ax.set_ylim(bottom=0)

    plt.tight_layout()
    caminho = os.path.join(GRAFICOS, "04_throughput_execucoes.png")
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"[OK] Salvo: {caminho}")


# ─────────────────────────────────────────────
# 7. Gráfico 5 — Degradação por cenário (linha)
# ─────────────────────────────────────────────

def grafico_degradacao(tcp, rudp):
    medias_tcp  = [tcp[tcp["cenario"]  == c]["throughput_mbps"].mean() for c in CENARIOS]
    medias_rudp = [rudp[rudp["cenario"] == c]["throughput_mbps"].mean() for c in CENARIOS]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(CENARIOS, medias_tcp,  "o-", color=COR_TCP,  label="TCP",
            linewidth=2.5, markersize=9)
    ax.plot(CENARIOS, medias_rudp, "s-", color=COR_RUDP, label="R-UDP",
            linewidth=2.5, markersize=9)

    for i, (c, v) in enumerate(zip(CENARIOS, medias_tcp)):
        ax.annotate(f"{v:.3f}", (c, v), textcoords="offset points",
                    xytext=(0, 10), ha="center", color="navy", fontsize=9)
    for i, (c, v) in enumerate(zip(CENARIOS, medias_rudp)):
        ax.annotate(f"{v:.3f}", (c, v), textcoords="offset points",
                    xytext=(0, -16), ha="center", color="darkred", fontsize=9)

    ax.set_xlabel("Cenário de Rede", fontsize=12)
    ax.set_ylabel("Throughput Médio (Mbps)", fontsize=12)
    ax.set_title("Degradação do Throughput conforme piora da rede",
                 fontsize=13, fontweight="bold")
    ax.set_xticklabels([DESC_CEN[c] for c in CENARIOS], fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(linestyle="--", alpha=0.4)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    caminho = os.path.join(GRAFICOS, "05_degradacao_cenarios.png")
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"[OK] Salvo: {caminho}")


# ─────────────────────────────────────────────
# 8. Execução principal
# ─────────────────────────────────────────────

def main():
    print("="*60)
    print("  ANÁLISE ESTATÍSTICA — TCP vs R-UDP")
    print("  JULIO CESAR DE LIMA MENDES | 20249006910")
    print("="*60)

    tcp, rudp = carregar_dados()

    print(f"\nDados carregados:")
    print(f"  TCP  : {len(tcp)} execuções válidas")
    print(f"  R-UDP: {len(rudp)} execuções válidas")

    imprimir_tabela(tcp, rudp)

    print(f"\nGerando gráficos em {GRAFICOS}/ ...")
    grafico_throughput_medio(tcp, rudp)
    grafico_boxplot_throughput(tcp, rudp)
    grafico_duracao_media(tcp, rudp)
    grafico_throughput_por_execucao(tcp, rudp)
    grafico_degradacao(tcp, rudp)

    print("\n" + "="*60)
    print("  5 gráficos gerados com sucesso!")
    print(f"  Pasta: {GRAFICOS}/")
    print("="*60)


if __name__ == "__main__":
    main()
