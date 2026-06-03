# =============================================================
# config.py — Configurações globais do projeto
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================

import hashlib

# ---- Identificação do aluno ----
MATRICULA = "20249006910"
NOME      = "JULIO CESAR DE LIMA MENDES"

# Hash SHA-256 usado no cabeçalho X-Custom-Auth
X_CUSTOM_AUTH = hashlib.sha256(
    (MATRICULA + NOME).encode()
).hexdigest()

# ---- Rede ----
HOST_SERVIDOR = "172.20.0.10"   # IP do container servidor
PORTA_TCP     = 5000
PORTA_UDP     = 5001

# ---- Transferência ----
TAMANHO_CHUNK  = 4096           # Bytes por pacote de dados
TIMEOUT_RUDP   = 2.0            # Segundos para retransmissão (R-UDP)
MAX_TENTATIVAS = 10             # Máximo de retransmissões por pacote

# ---- Logs ----
LOG_DIR = "/app/logs"
