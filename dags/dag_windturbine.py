from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator 
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import json
import os

"""
DAG WindTurbine: Orquestração de pipeline para monitoramento e registro de dados de turbina eólica.

Este código define uma DAG para automatizar o processamento de dados de sensores de turbinas eólicas. 
O pipeline realiza as seguintes etapas:
1. Aguarda a chegada de um arquivo de dados de sensores em um diretório monitorado. (O arquivo é gerado pelo notebook generator 
winturbinegenerator.ipynb)
2. Processa o arquivo, extrai os dados e os envia para o XCom para uso em tarefas subsequentes.
3. Insere os dados extraídos em uma tabela PostgreSQL, criando a tabela caso não exista.
4. Avalia a temperatura registrada e envia um e-mail de alerta se estiver acima do limite estabelecido, ou um e-mail informativo 
se estiver normal.

**Parâmetros e argumentos principais:**
- `default_args`: Define configurações padrão para as tasks, como e-mail de notificação, tentativas de retry e intervalo entre 
tentativas.
- `schedule_interval`: Configurado para rodar a cada minuto (`'* * * * *'`), garantindo monitoramento contínuo.
- `start_date`: Data de início da DAG.
- `catchup`: Desabilitado para evitar execuções retroativas.
- `tags`, `doc_md`: Usados para organização e documentação da DAG.

**Uso de Task Groups:**
Os Task Groups (`group_check_temp` e `group_database`) são utilizados para organizar visualmente e logicamente as tarefas 
relacionadas, facilitando o entendimento do fluxo e a manutenção do pipeline.  
- `group_check_temp`: Agrupa as tarefas de avaliação de temperatura e envio de e-mails.
- `group_database`: Agrupa as tarefas de criação de tabela e inserção de dados no banco.
"""

default_args = {
        'depends_on_past' : False,
        'email' : ['seu.email@gmail.com'],
        'email_on_failure': True,
        'email_on_retry': False,
        'retries' : 3,
        'retry_delay' : timedelta(seconds=10)
        }

dag = DAG('windturbine', description='Dados da Turbina',
          schedule_interval='* * * * *', 
          start_date=datetime(2025,8,10),
          catchup=False,
          default_args=default_args,
          default_view='graph',
          doc_md="## Dag para registrar dados de turbina eólica", #pode ser usado para documentar a DAG e tasks
          tags=['windturbine'],
          )

group_check_temp = TaskGroup("group_check_temp", dag=dag)
group_database = TaskGroup('group_database', dag=dag)

file_sensor_task = FileSensor(
        task_id = 'file_sensor_task',
        filepath = Variable.get('path_file'),
        fs_conn_id = 'fs_default',
        poke_interval = 10,
        dag = dag)

def process_file(**kwarg):
    with open(Variable.get('path_file')) as f:
        data = json.load(f)
        kwarg['ti'].xcom_push(key='idtemp', value=data['idtemp'])
        kwarg['ti'].xcom_push(key='powerfactor', value=data['powerfactor'])
        kwarg['ti'].xcom_push(key='hydraulicpressure', value=data['hydraulicpressure'])
        kwarg['ti'].xcom_push(key='temperature', value=data['temperature'])
        kwarg['ti'].xcom_push(key='timestamp', value=data['timestamp'])
    os.remove(Variable.get('path_file'))

get_data = PythonOperator(
            task_id = 'get_data',
            python_callable= process_file,
            provide_context = True,
            dag=dag)

create_table = PostgresOperator(task_id="create_table",
                                postgres_conn_id='postgres',
                                sql='''CREATE TABLE IF NOT EXISTS sensors (
                                        idtemp VARCHAR, 
                                        powerfactor VARCHAR,
                                        hydraulicpressure VARCHAR, 
                                        temperature VARCHAR,
                                        timestamp VARCHAR
                                    );''',
                                task_group=group_database,
                                dag=dag)

insert_data = PostgresOperator(task_id='insert_data',
                               postgres_conn_id='postgres',
                               parameters=(
                                '{{ ti.xcom_pull(task_ids="get_data",key="idtemp") }}',     
                                '{{ ti.xcom_pull(task_ids="get_data",key="powerfactor") }}',     
                                '{{ ti.xcom_pull(task_ids="get_data",key="hydraulicpressure") }}',     
                                '{{ ti.xcom_pull(task_ids="get_data",key="temperature") }}',     
                                '{{ ti.xcom_pull(task_ids="get_data",key="timestamp") }}'                                                                               
                                ),#expressões Jinja para puxar os valores do XCom
                                sql = '''INSERT INTO sensors (idtemp, powerfactor,
                                hydraulicpressure, temperature, timestamp)
                                VALUES (%s, %s, %s, %s, %s);''',
                                task_group = group_database,
                                dag=dag
                               )

send_email_alert = EmailOperator(
        task_id='send_email_alert',
        to='seu.email@gmail.com',
        subject='Airflow Alert',
        html_content = '''<h3>Alerta de Temperatura. </h3>
        <p> Dag: windturbine </p>
        <p> Temperatura da turbina eólica acima do limite. </p>
        ''',
        task_group=group_check_temp,
        dag=dag)

send_email = EmailOperator(
        task_id='send_email',
        to='seu.email@gmail.com',
        subject='Airflow Advise',
        html_content = '''<h3>Temperaturas Normais. </h3>
        <p> Dag: windturbine </p>
        <p> Temperatura da turbina eólica está normal. </p>
        ''',
        task_group=group_check_temp,
        dag=dag)

def avalia_temp(**context):
    temperature = float(context['ti'].xcom_pull(task_ids='get_data', key='temperature'))
    if temperature >= 30.0:  # Limite de temperatura
        return 'group_check_temp.send_email_alert'
    else:
        return 'group_check_temp.send_email'

check_temp_branch = BranchPythonOperator(
        task_id='check_temp_branch',
        python_callable=avalia_temp,
        provide_context=True,
        dag=dag,
        task_group=group_check_temp)

with group_check_temp:
    check_temp_branch >> [send_email_alert, send_email]

with group_database:
    create_table >> insert_data

file_sensor_task >> get_data
get_data >> group_check_temp
get_data >> group_database
