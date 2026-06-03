# Imagem base Ubuntu 22.04
FROM ubuntu:22.04

# Evita prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instala Python 3, ferramentas de rede e utilitários
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iproute2 \
    tcpdump \
    iputils-ping \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
RUN pip3 install pandas matplotlib

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia todo o código para dentro do container
COPY . /app/

# Permissão de execução nos scripts
RUN chmod +x /app/scripts/setup_tc.sh

# Porta padrão exposta (usada pelo servidor)
EXPOSE 5000

