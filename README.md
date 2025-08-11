# airflow-projeto

Este projeto utiliza o Apache Airflow para orquestrar um pipeline de monitoramento e registro de dados de uma turbina eólica. O fluxo automatiza desde a detecção de novos arquivos de sensores até o armazenamento dos dados em banco de dados e envio de alertas por e-mail.

---

## Principais Funcionalidades

- **Monitoramento de Arquivos:** Detecta automaticamente a chegada de novos arquivos de dados de sensores em um diretório específico.
- **Processamento dos Dados:** Lê e extrai informações relevantes dos arquivos JSON gerados pelos sensores.
- **Armazenamento em Banco de Dados:** Cria e insere os dados em uma tabela PostgreSQL, garantindo persistência e histórico dos registros.
- **Avaliação de Temperatura:** Analisa a temperatura registrada e envia alertas por e-mail caso esteja acima do limite definido.
- **Notificações:** Envia e-mails informativos ou de alerta conforme o resultado da avaliação dos dados.

---

## Estrutura do Projeto

- `dags/`: Contém o código principal da DAG responsável pelo pipeline de dados da turbina eólica.
- `data/`: Diretório onde os arquivos de dados dos sensores são gerados e monitorados pelo Airflow. Certifique-se de que o caminho configurado na variável `path_file` aponte para esta pasta.
- `winturbinegenerator.ipynb`: Notebook que gera os arquivos de dados simulando os sensores da turbina.
- `README.md`: Este arquivo de documentação.

---

## Como rodar o projeto com Docker

Para executar o Airflow via Docker, é necessário criar um arquivo `.env` na raiz do projeto. Esse arquivo define variáveis de ambiente essenciais para a configuração dos containers.

**Exemplo de arquivo `.env`:**
```
AIRFLOW_UID=50000
AIRFLOW_IMAGE_NAME=apache/airflow:2.5.1
```
Esses valores garantem que o Airflow tenha permissões corretas para criar arquivos e diretórios nos volumes do Docker.

### Passo a passo para subir o Airflow com Docker:

1. **Clone o repositório e acesse a pasta do projeto:**
   ```
   git clone <url-do-repositorio>
   cd <nome-da-pasta>
   ```

2. **Crie o arquivo `.env` conforme o exemplo acima.**

3. **Suba os containers do Airflow:**
   ```
   docker compose up airflow-init
   docker compose up
   ```

4. **Acesse a interface web do Airflow:**
   - Normalmente disponível em [http://localhost:8080](http://localhost:8080)
   - Usuário e senha padrão: `airflow` / `airflow` (pode ser alterado no docker-compose ou via variáveis de ambiente)

5. **Para parar os containers:**
   ```
   docker compose down
   ```

6. **Para remover volumes e dados persistentes:**
   ```
   docker compose down --volumes --remove-orphans
   ```

**Observação:**  
Certifique-se de ter o Docker e o Docker Compose instalados em sua máquina.

---

## Configuração SMTP

As configurações de SMTP para envio de e-mails pelo Airflow estão definidas no arquivo de configuração do Docker utilizado no projeto.  
Isso garante que o Airflow consiga enviar notificações e alertas automaticamente, sem necessidade de configuração manual no `airflow.cfg` local.

Certifique-se de que as variáveis de ambiente relacionadas ao SMTP estejam corretamente configuradas no arquivo Docker antes de iniciar os serviços.

---

## Configuração de Conexões e Variáveis via Interface do Airflow

- **Conexão com o banco de dados PostgreSQL:**  
  A conexão foi criada pela interface web do Airflow.  
  Para criar ou editar uma conexão:
  1. Acesse o menu **Admin > Connections**.
  2. Clique em **+ Add a new record**.
  3. Escolha o tipo `Postgres`, preencha os campos necessários (host, schema, login, senha, porta) e salve.
  4. Use o mesmo `Conn Id` configurado na DAG (ex: `postgres`).

- **Variável do caminho do arquivo (`path_file`):**  
  A variável foi criada pela interface web do Airflow.  
  Para criar ou editar uma variável:
  1. Acesse o menu **Admin > Variables**.
  2. Clique em **+ Add a new record**.
  3. Defina o nome como `path_file` e o valor como o caminho completo para a pasta ou arquivo monitorado (ex: `/opt/airflow/data/arquivo.json`).
  4. Salve a variável.

Essas configurações permitem que o pipeline funcione corretamente, sem necessidade de alterar o código para diferentes ambientes.

---

## Observações Importantes

- Configure corretamente as conexões do Airflow, especialmente para o PostgreSQL e SMTP (para envio de e-mails).
- Os arquivos de dados devem ser gerados e salvos na pasta `data/`, conforme definido na variável `path_file` do Airflow.
- O projeto pode ser facilmente adaptado para outros tipos de sensores ou bancos de dados.
