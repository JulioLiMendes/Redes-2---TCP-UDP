import hashlib

MATRICULA = "20249006910"
NOME      = "JULIO CESAR DE LIMA MENDES"

X_CUSTOM_AUTH = hashlib.sha256(
    (MATRICULA + NOME).encode()
).hexdigest()

HOST_SERVIDOR = "172.20.0.10"  
PORTA_TCP     = 5000
PORTA_UDP     = 5001

TAMANHO_CHUNK  = 4096        
TIMEOUT_RUDP   = 2.0      
MAX_TENTATIVAS = 10         

LOG_DIR = "/app/logs"
