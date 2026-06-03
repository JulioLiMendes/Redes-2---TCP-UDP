#!/bin/bash
# =============================================================
# setup_tc.sh — Simulação de condições adversas de rede
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# Uso: ./setup_tc.sh [A|B|C|reset]
# =============================================================

INTERFACE="eth0"

limpar_regras() {
    echo "[TC] Removendo regras anteriores em $INTERFACE..."
    tc qdisc del dev $INTERFACE root 2>/dev/null || true
    echo "[TC] Interface limpa."
}

aplicar_cenario() {
    local CENARIO=$1
    local PERDA=$2
    local DELAY=$3

    echo "=========================================="
    echo " Aplicando Cenário $CENARIO"
    echo " Perda de pacotes : $PERDA%"
    echo " Latência (delay) : ${DELAY}ms"
    echo "=========================================="

    # Remove regras antigas antes de aplicar novas
    limpar_regras

    # Aplica nova disciplina de fila com netem
    tc qdisc add dev $INTERFACE root netem \
        delay ${DELAY}ms \
        loss ${PERDA}%

    echo "[TC] Cenário $CENARIO aplicado com sucesso!"
    echo ""
    echo "[TC] Configuração atual:"
    tc qdisc show dev $INTERFACE
}

# ---- Leitura do argumento ----
CENARIO=${1^^}  # Converte para maiúsculo

case $CENARIO in
    A)
        # Cenário A: Rede ideal
        aplicar_cenario "A" 0 10
        ;;
    B)
        # Cenário B: Rede degradada
        aplicar_cenario "B" 5 50
        ;;
    C)
        # Cenário C: Rede com alta perda
        aplicar_cenario "C" 10 100
        ;;
    RESET)
        limpar_regras
        echo "[TC] Interface restaurada ao estado normal."
        ;;
    *)
        echo "Uso: $0 [A|B|C|reset]"
        echo ""
        echo "  A     → 0% perda / 10ms delay  (rede ideal)"
        echo "  B     → 5% perda / 50ms delay  (rede degradada)"
        echo "  C     → 10% perda / 100ms delay (rede com alta perda)"
        echo "  reset → Remove todas as regras de tráfego"
        exit 1
        ;;
esac
