# Redes de Computadores II — TCP vs R-UDP
**Aluno:** JULIO CESAR DE LIMA MENDES  
**Matrícula:** 20249006910  
**X-Custom-Auth (SHA-256):** `2f93fca4ad0be3570264caaf2010c07833a9889bd61b857b9681fd465d2fcf15`

---

## Estrutura do Projeto

```
redes2/
├── Dockerfile
├── docker-compose.yml
├── config.py
├── scripts/
│   └── setup_tc.sh
├── servidor/
│   ├── servidor_tcp.py     (Etapa 2)
│   └── servidor_rudp.py    (Etapa 3)
├── cliente/
│   ├── cliente_tcp.py      (Etapa 2)
│   └── cliente_rudp.py     (Etapa 3)
├── logs/                   (gerado automaticamente)
└── analise/
    └── analise.py          (Etapa 5)
```

---

## Pré-requisitos (Windows)

1. Instalar o **Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. Habilitar **WSL 2** quando solicitado pelo Docker Desktop
3. Instalar o **Git**: https://git-scm.com/

---

## Como usar (Etapa 1)

### 1. Subir os containers
Abra o **PowerShell** ou **Terminal** na pasta do projeto:

```bash
docker-compose up -d --build
```

### 2. Verificar se os containers estão rodando
```bash
docker ps
```
Você deve ver `redes2_servidor` e `redes2_cliente` com status `Up`.

### 3. Testar conectividade entre os containers
```bash
# Entrar no container cliente
docker exec -it redes2_cliente bash

# Dentro do container, pingar o servidor
ping 172.20.0.10
```

### 4. Aplicar um cenário de rede (dentro do container)
```bash
# Entrar no container cliente
docker exec -it redes2_cliente bash

# Aplicar Cenário A (rede ideal)
bash /app/scripts/setup_tc.sh A

# Aplicar Cenário B (rede degradada)
bash /app/scripts/setup_tc.sh B

# Aplicar Cenário C (alta perda)
bash /app/scripts/setup_tc.sh C

# Remover regras
bash /app/scripts/setup_tc.sh reset
```

### 5. Verificar o delay aplicado
```bash
ping -c 5 172.20.0.10
```

### 6. Derrubar os containers
```bash
docker-compose down
```

---

## Cenários de Rede

| Cenário | Perda de Pacotes | Delay  | Descrição        |
|---------|-----------------|--------|------------------|
| A       | 0%              | 10ms   | Rede ideal       |
| B       | 5%              | 50ms   | Rede degradada   |
| C       | 10%             | 100ms  | Alta perda       |
