
import os
import sys
import time
import subprocess

sys.path.insert(0, '/app')
from config import LOG_DIR

ARQUIVO_TESTE = "/app/logs/arquivo_teste.bin"
TAMANHO_MB    = 5
N_EXECUCOES   = 15
CENARIOS      = ["A", "B", "C"]
SETUP_TC      = "/app/scripts/setup_tc.sh"
CLIENTE_RUDP  = "/app/cliente/cliente_rudp.py"
PAUSA_ENTRE   = 2.0


def gerar_arquivo_teste():
    tamanho = TAMANHO_MB * 1024 * 1024
    if os.path.exists(ARQUIVO_TESTE) and os.path.getsize(ARQUIVO_TESTE) == tamanho:
        print("[INFO] Arquivo de teste ja existe.")
        return
    print(f"[INFO] Gerando arquivo de teste de {TAMANHO_MB}MB...")
    with open(ARQUIVO_TESTE, "wb") as f:
        f.write(os.urandom(tamanho))
    print(f"[INFO] Arquivo criado: {ARQUIVO_TESTE}")


def aplicar_cenario(cenario):
    print(f"\n{'='*50}\n  Aplicando Cenario {cenario}...\n{'='*50}")
    r = subprocess.run(["bash", SETUP_TC, cenario], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(f"[ERRO tc] {r.stderr}")
    time.sleep(1)


def executar_transferencias(cenario):
    for i in range(1, N_EXECUCOES + 1):
        print(f"\n[R-UDP] Cenario {cenario} | Execucao {i}/{N_EXECUCOES}")
        subprocess.run(
            ["python3", CLIENTE_RUDP, ARQUIVO_TESTE, cenario, str(i)]
        )
        time.sleep(PAUSA_ENTRE)


def main():
    print("=" * 60)
    print("  TESTES AUTOMATICOS - R-UDP")
    print(f"  {N_EXECUCOES} execucoes x {len(CENARIOS)} cenarios")
    print("  ATENCAO: Inicie o servidor_rudp.py antes!")
    print("=" * 60)

    os.makedirs(LOG_DIR, exist_ok=True)
    gerar_arquivo_teste()

    for cenario in CENARIOS:
        aplicar_cenario(cenario)
        executar_transferencias(cenario)

    subprocess.run(["bash", SETUP_TC, "reset"], capture_output=True)

    print("\n" + "=" * 60)
    print("  TESTES R-UDP CONCLUIDOS!")
    print(f"  Resultados em: {LOG_DIR}/resultados_rudp.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()
