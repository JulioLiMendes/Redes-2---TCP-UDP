# =============================================================
# protocolo_rudp.py — Definição dos pacotes do protocolo R-UDP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================
#
# Estrutura do pacote R-UDP (binário com struct):
#
#  0        1        2        3        4        5        6        7   (bytes)
#  +--------+--------+--------+--------+--------+--------+--------+--------+
#  |  TIPO  |  SEQ_NUM (4 bytes)       |  CHECKSUM (4 bytes)               |
#  +--------+--------+--------+--------+--------+--------+--------+--------+
#  |  PAYLOAD_LEN (4 bytes)  |  AUTH_LEN (1 byte) | AUTH (64 bytes fixo)  |
#  +--------+--------+--------+--------+--------+--------+--------+--------+
#  |  DADOS (variável, até TAMANHO_CHUNK bytes)                            |
#  +--------+--------+--------+--------+--------+--------+--------+--------+
#
# Tamanho do cabeçalho fixo: 1 + 4 + 4 + 4 + 1 + 64 = 78 bytes
# =============================================================

import struct
import zlib

# ---- Tipos de pacote ----
TIPO_DATA  = 0x01   # Pacote de dados
TIPO_ACK   = 0x02   # Confirmação
TIPO_NACK  = 0x03   # Confirmação negativa (erro de checksum)
TIPO_SYN   = 0x04   # Início de sessão
TIPO_FIN   = 0x05   # Fim de transferência
TIPO_SYNACK= 0x06   # Resposta ao SYN

# Tamanhos fixos
TAMANHO_CABECALHO = 78   # bytes
AUTH_SIZE         = 64   # SHA-256 em hex = 64 caracteres


def calcular_checksum(dados: bytes) -> int:
    """Calcula CRC32 dos dados como checksum de integridade."""
    return zlib.crc32(dados) & 0xFFFFFFFF


def montar_pacote(tipo: int, seq_num: int, auth: str, payload: bytes = b"") -> bytes:
    """
    Monta um pacote R-UDP completo.
    Retorna bytes prontos para envio via socket UDP.
    """
    # Checksum calculado sobre o payload
    checksum    = calcular_checksum(payload)
    payload_len = len(payload)

    # Auth padded/truncated para exatamente AUTH_SIZE bytes
    auth_bytes  = auth.encode()[:AUTH_SIZE].ljust(AUTH_SIZE, b'\x00')

    # Cabeçalho: tipo(1) + seq(4) + checksum(4) + payload_len(4) + auth_len(1) + auth(64)
    cabecalho = struct.pack(
        "!B I I I B",
        tipo,
        seq_num,
        checksum,
        payload_len,
        AUTH_SIZE
    ) + auth_bytes

    return cabecalho + payload


def desmontar_pacote(raw: bytes) -> dict:
    """
    Desmonta um pacote R-UDP recebido.
    Retorna um dicionário com os campos do pacote.
    """
    if len(raw) < TAMANHO_CABECALHO:
        raise ValueError(f"Pacote muito curto: {len(raw)} bytes (mín: {TAMANHO_CABECALHO})")

    # Desempacota o cabeçalho fixo
    tipo, seq_num, checksum_recebido, payload_len, auth_len = struct.unpack(
        "!B I I I B", raw[:14]
    )

    # Lê o campo de autenticação
    auth_raw = raw[14:14 + AUTH_SIZE]
    auth     = auth_raw.rstrip(b'\x00').decode(errors='ignore')

    # Lê o payload
    payload_inicio = TAMANHO_CABECALHO
    payload        = raw[payload_inicio:payload_inicio + payload_len]

    # Valida integridade
    checksum_calculado = calcular_checksum(payload)
    integro = (checksum_calculado == checksum_recebido)

    return {
        "tipo"       : tipo,
        "seq_num"    : seq_num,
        "checksum"   : checksum_recebido,
        "integro"    : integro,
        "auth"       : auth,
        "payload_len": payload_len,
        "payload"    : payload
    }


def montar_ack(seq_num: int, auth: str) -> bytes:
    """Monta um pacote ACK."""
    return montar_pacote(TIPO_ACK, seq_num, auth)


def montar_nack(seq_num: int, auth: str) -> bytes:
    """Monta um pacote NACK (erro de integridade)."""
    return montar_pacote(TIPO_NACK, seq_num, auth)


def montar_syn(auth: str, metadata: bytes) -> bytes:
    """Monta pacote SYN com metadados do arquivo."""
    return montar_pacote(TIPO_SYN, 0, auth, metadata)


def montar_synack(auth: str) -> bytes:
    """Monta pacote SYN-ACK."""
    return montar_pacote(TIPO_SYNACK, 0, auth)


def montar_fin(seq_num: int, auth: str) -> bytes:
    """Monta pacote FIN (fim da transferência)."""
    return montar_pacote(TIPO_FIN, seq_num, auth)


def nome_tipo(tipo: int) -> str:
    nomes = {
        TIPO_DATA  : "DATA",
        TIPO_ACK   : "ACK",
        TIPO_NACK  : "NACK",
        TIPO_SYN   : "SYN",
        TIPO_FIN   : "FIN",
        TIPO_SYNACK: "SYN-ACK",
    }
    return nomes.get(tipo, f"DESCONHECIDO(0x{tipo:02X})")
