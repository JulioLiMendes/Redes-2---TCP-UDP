import struct
import zlib

TIPO_DATA  = 0x01   
TIPO_ACK   = 0x02   
TIPO_NACK  = 0x03 
TIPO_SYN   = 0x04  
TIPO_FIN   = 0x05   
TIPO_SYNACK= 0x06 

TAMANHO_CABECALHO = 78   
AUTH_SIZE         = 64   


def calcular_checksum(dados: bytes) -> int:
    """Calcula CRC32 dos dados como checksum de integridade."""
    return zlib.crc32(dados) & 0xFFFFFFFF


def montar_pacote(tipo: int, seq_num: int, auth: str, payload: bytes = b"") -> bytes:
    """
    Monta um pacote R-UDP completo.
    Retorna bytes prontos para envio via socket UDP.
    """
    checksum    = calcular_checksum(payload)
    payload_len = len(payload)

    auth_bytes  = auth.encode()[:AUTH_SIZE].ljust(AUTH_SIZE, b'\x00')

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

    tipo, seq_num, checksum_recebido, payload_len, auth_len = struct.unpack(
        "!B I I I B", raw[:14]
    )

    auth_raw = raw[14:14 + AUTH_SIZE]
    auth     = auth_raw.rstrip(b'\x00').decode(errors='ignore')

    payload_inicio = TAMANHO_CABECALHO
    payload        = raw[payload_inicio:payload_inicio + payload_len]

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
