import os
import sys
import time
import subprocess

sys.path.insert(0, '/app')
from config import LOG_DIR

ARQUIVO_TESTE   = "/app/logs/arquivo_teste.bin"
TAMANHO_MB      = 5      
N_EXECUCOES     = 15     
CENARIOS        = ["A", "B", "C"]
SETUP_TC        = "/app/scripts/setup_tc.sh"
CLIENTE_TCP     = "/app/cliente/cliente_tcp.py"
PAUSA_ENTRE     = 1.0      


def gerar_arquivo_teste():
    """Gera um arquivo binário aleatório para os testes."""
    tamanho = TAMANHO_MB * 1024 * 1024
    if os.path.exists(ARQUIVO_TESTE):
        if os.path.getsize(ARQUIVO_TESTE) == tamanho:
            print(f"[INFO] Arquivo de teste já existe: {ARQUIVO_TESTE}")
            return
    print(f"[INFO] Gerando arquivo de teste de {TAMANHO_MB}MB...")
    with open(ARQUIVO_TESTE, "wb") as f:
        f.write(os.urandom(tamanho))
    print(f"[INFO] Arquivo criado: {ARQUIVO_TESTE}")


def aplicar_cenario(cenario):
    """Aplica o cenário de rede via tc."""
    print(f"\n{'='*50}")
    print(f"  Aplicando Cenário {cenario}...")
    print(f"{'='*50}")
    resultado = subprocess.run(
        ["bash", SETUP_TC, cenario],
        capture_output=True, text=True
    )
    print(resultado.stdout)
    if resultado.returncode != 0:
        print(f"[ERRO tc] {resultado.stderr}")
    time.sleep(1) 


def executar_transferencias(cenario):
    """Executa N transferências TCP para o cenário dado."""
    for i in range(1, N_EXECUCOES + 1):
        print(f"\n[TCP] Cenário {cenario} | Execução {i}/{N_EXECUCOES}")
        resultado = subprocess.run(
            ["python3", CLIENTE_TCP, ARQUIVO_TESTE, cenario, str(i)],
            capture_output=False
        )
        time.sleep(PAUSA_ENTRE)


def main():
    print("=" * 60)
    print("  TESTES AUTOMÁTICOS — TCP")
    print(f"  {N_EXECUCOES} execuções × {len(CENARIOS)} cenários = "
          f"{N_EXECUCOES * len(CENARIOS)} transferências")
    print("=" * 60)

    os.makedirs(LOG_DIR, exist_ok=True)
    gerar_arquivo_teste()

    for cenario in CENARIOS:
        aplicar_cenario(cenario)
        executar_transferencias(cenario)

    subprocess.run(["bash", SETUP_TC, "reset"], capture_output=True)

    print("\n" + "=" * 60)
    print("  TESTES TCP CONCLUÍDOS!")
    print(f"  Resultados em: {LOG_DIR}/resultados_tcp.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()
