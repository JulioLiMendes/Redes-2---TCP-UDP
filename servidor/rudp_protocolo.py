# =============================================================
# rudp_protocolo.py — Definição do pacote R-UDP
# Autor: JULIO CESAR DE LIMA MENDES | Matrícula: 20249006910
# =============================================================
#
# Estrutura do pacote R-UDP (cabeçalho fixo de 32 bytes):
#
#  0        1        2        3        4
#  +--------+--------+--------+--------+
#  |         NUMERO DE SEQUENCIA        |  4 bytes (uint32)
#  +--------+--------+--------+--------+
#  |              CHECKSUM              |  4 bytes (uint32)
#  +--------+--------+--------+--------+
#  |    TIPO   (1B)  | FLAGS  (1B)      |  2 bytes
#  +--------+--------+--------+--------+
#  |         TAMANHO DO PAYLOAD         |  4 bytes (uint32)
#  +--------+--------+--------+--------+
#  |      X-Custom-Auth (64 bytes)      |  64 bytes (hex string)
#  +--------+--------+--------+--------+
#  |            PAYLOAD                 |  variável
#  +--------+--------+--------+--------+
#
# TIPOS de pacote:
#   0x01 = DATA   — bloco de dados do arquivo
#   0x02 = ACK    — confirmação de recebimento
#   0x03 = SYN    — início de sessão (handshake)
#   0x04 = FIN    — fim de transferência
#   0x05 = SYNACK — resposta ao SYN
#   0x06 = FINACK — resposta ao FIN
#
# FLAGS:
#   0x00 = normal
#   0x01 = último pacote (EOF)
# =============================================================

import struct
import zlib

# ---- Constantes de tipo ----
TIPO_DATA   = 0x01
TIPO_ACK    = 0x02
TIPO_SYN    = 0x03
TIPO_FIN    = 0x04
TIPO_SYNACK = 0x05
TIPO_FINACK = 0x06

FLAG_NORMAL = 0x00
FLAG_EOF    = 0x01

# Tamanho fixo do cabeçalho
TAMANHO_CABECALHO = 4 + 4 + 1 + 1 + 4 + 64  # = 78 bytes


def calcular_checksum(payload: bytes) -> int:
    """CRC32 do payload para validação de integridade."""
    return zlib.crc32(payload) & 0xFFFFFFFF


def montar_pacote(seq: int, tipo: int, payload: bytes,
                  auth: str, flag: int = FLAG_NORMAL) -> bytes:
    """
    Serializa um pacote R-UDP completo em bytes.
    Retorna: cabeçalho (78 bytes) + payload
    """
    checksum = calcular_checksum(payload)

    # Cabeçalho: seq(4) + checksum(4) + tipo(1) + flag(1) + tamanho(4) + auth(64)
    auth_bytes = auth.encode().ljust(64)[:64]   # garante exatamente 64 bytes
    cabecalho = struct.pack(
        "!IIBbI64s",
        seq,
        checksum,
        tipo,
        flag,
        len(payload),
        auth_bytes
    )
    return cabecalho + payload


def desmontar_pacote(dados: bytes):
    """
    Desserializa bytes em campos do pacote R-UDP.
    Retorna dict com todos os campos + flag de integridade ok/fail.
    """
    if len(dados) < TAMANHO_CABECALHO:
        return None

    seq, checksum, tipo, flag, tamanho_payload, auth_bytes = struct.unpack_from(
        "!IIBbI64s", dados, 0
    )

    payload = dados[TAMANHO_CABECALHO: TAMANHO_CABECALHO + tamanho_payload]

    # Valida checksum
    checksum_calculado = calcular_checksum(payload)
    integro = (checksum_calculado == checksum)

    return {
        "seq"      : seq,
        "checksum" : checksum,
        "tipo"     : tipo,
        "flag"     : flag,
        "tamanho"  : tamanho_payload,
        "auth"     : auth_bytes.decode().strip(),
        "payload"  : payload,
        "integro"  : integro
    }


def tipo_str(tipo: int) -> str:
    """Retorna o nome legível do tipo de pacote."""
    nomes = {
        TIPO_DATA  : "DATA",
        TIPO_ACK   : "ACK",
        TIPO_SYN   : "SYN",
        TIPO_FIN   : "FIN",
        TIPO_SYNACK: "SYNACK",
        TIPO_FINACK: "FINACK",
    }
    return nomes.get(tipo, f"DESCONHECIDO(0x{tipo:02x})")
