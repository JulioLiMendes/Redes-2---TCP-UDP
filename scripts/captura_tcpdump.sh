INTERFACE="eth0"
LOG_DIR="/app/logs"
PCAP_DIR="$LOG_DIR/pcap"
mkdir -p "$PCAP_DIR"

PORTA_TCP=5000
PORTA_UDP=5001

PROTOCOLO=${1:-"todos"}
CENARIO=${2:-"X"}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

capturar() {
    local FILTRO="$1"
    local ARQUIVO="$2"
    local DESCRICAO="$3"

    echo "=========================================="
    echo "  Iniciando captura: $DESCRICAO"
    echo "  Filtro : $FILTRO"
    echo "  Saída  : $ARQUIVO"
    echo "  Pressione Ctrl+C para encerrar"
    echo "=========================================="

    tcpdump -i "$INTERFACE" \
            -w "$ARQUIVO" \
            -n \
            "$FILTRO"

    echo ""
    echo "[OK] Captura encerrada: $ARQUIVO"
    echo "[INFO] Tamanho: $(du -sh "$ARQUIVO" | cut -f1)"
}

case "${PROTOCOLO,,}" in
    tcp)
        ARQUIVO="$PCAP_DIR/tcp_cenario${CENARIO}_${TIMESTAMP}.pcap"
        capturar "tcp port $PORTA_TCP" "$ARQUIVO" \
                 "TCP | Cenário $CENARIO | Porta $PORTA_TCP"
        ;;

    rudp)
        ARQUIVO="$PCAP_DIR/rudp_cenario${CENARIO}_${TIMESTAMP}.pcap"
        capturar "udp port $PORTA_UDP" "$ARQUIVO" \
                 "R-UDP | Cenário $CENARIO | Porta $PORTA_UDP"
        ;;

    todos)
        ARQUIVO="$PCAP_DIR/todos_cenario${CENARIO}_${TIMESTAMP}.pcap"
        capturar "port $PORTA_TCP or port $PORTA_UDP" "$ARQUIVO" \
                 "TCP + R-UDP | Cenário $CENARIO"
        ;;

    *)
        echo "Uso: $0 [tcp|rudp|todos] [cenario]"
        echo "  tcp   → captura apenas tráfego TCP (porta $PORTA_TCP)"
        echo "  rudp  → captura apenas tráfego UDP (porta $PORTA_UDP)"
        echo "  todos → captura ambos"
        echo ""
        echo "Exemplos:"
        echo "  $0 tcp A      → TCP no Cenário A"
        echo "  $0 rudp B     → R-UDP no Cenário B"
        echo "  $0 todos C    → Tudo no Cenário C"
        exit 1
        ;;
esac
