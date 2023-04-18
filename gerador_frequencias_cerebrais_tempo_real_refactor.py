import threading
import os
from dotenv import load_dotenv
import logging
import sys
import time
import datetime as date
import mysql.connector
import matplotlib.pyplot as plt
import mne
import numpy as np
import matplotlib
matplotlib.use('agg')
logging.getLogger('mne').setLevel(logging.ERROR)

pacientes = [
    ("Paciente 1", "./arquivos/ST7011J0-PSG.edf", 0),
    ("Paciente 2", "./arquivos/SC4281G0-PSG.edf", 1),
    ("Paciente 3", "./arquivos/SC4482F0-PSG.edf", 0),
    ("Paciente 4", "./arquivos/SC4592G0-PSG.edf", 0),
    ("Paciente 5", "./arquivos/SC4772G0-PSG.edf", 1),
]


def criar_conexao():
    load_dotenv("./enviroments.env")
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    host = os.getenv('HOST')
    database = os.getenv('DATABASE')

    cnx = mysql.connector.connect(user=user,
                                  password=password,
                                  host=host,
                                  database=database)
    return cnx


def insert_query(data):
    cnx = criar_conexao()
    cursor = cnx.cursor()

    query = 'insert into frequencias_cerebrais(data_coleta, valor_frequencia_delta, valor_frequencia_theta, valor_frequencia_alpha, valor_frequencia_beta, espaco_utilizado, tempo_utilizado, nome_paciente) values(%s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.executemany(query, data)

    cnx.commit()
    cursor.close()
    cnx.close()
    return


def carregar_dados_edf(path):
    arquivo_edf = path
    dados = mne.io.read_raw_edf(arquivo_edf, preload=True)
    return dados


def gerar_frequencias(path, possui_apnea, nome_paciente):
    dados = carregar_dados_edf(path)

    frequencias_delta_simuladas = []
    frequencias_theta_simuladas = []
    frequencias_alpha_simuladas = []
    frequencias_beta_simuladas = []

    dataInserts = []
    origem = "local"

    if 'AWS_EXECUTION_ENV' in os.environ:
        origem = "nuvem"

    frequencias = dados.get_data(picks='EEG Fpz-Cz')
    while True:
        tempo_de_inicio = time.time()

        freqs, delta_freq = mne.time_frequency.psd_array_welch(
            frequencias, sfreq=dados.info['sfreq'], fmin=0.5, fmax=4, n_fft=4096)
        freqs, alpha_freq = mne.time_frequency.psd_array_welch(
            frequencias, sfreq=dados.info['sfreq'], fmin=8, fmax=13, n_fft=4096)
        freqs, beta_freq = mne.time_frequency.psd_array_welch(
            frequencias, sfreq=dados.info['sfreq'], fmin=13, fmax=30, n_fft=4096)
        freqs, theta_freq = mne.time_frequency.psd_array_welch(
            frequencias, sfreq=dados.info['sfreq'], fmin=4, fmax=8, n_fft=4096)

        frequencias_alpha_simuladas.append(np.random.normal(
            0, np.sqrt(alpha_freq), size=alpha_freq.shape))
        frequencias_beta_simuladas.append(np.random.normal(
            0, np.sqrt(beta_freq), size=beta_freq.shape))
        frequencias_theta_simuladas.append(np.random.normal(
            0, np.sqrt(theta_freq), size=theta_freq.shape))
        frequencias_delta_simuladas.append(np.random.normal(
            0, np.sqrt(delta_freq), size=delta_freq.shape))

        for i in range(1, len(frequencias_delta_simuladas[0]) - 1):
            dataInserts.append((date.datetime.now(), float(frequencias_delta_simuladas[0][i]), float(frequencias_theta_simuladas[0][i]), float(frequencias_alpha_simuladas[0][i]),
                                float(frequencias_beta_simuladas[0][i]), sys.getsizeof(frequencias_theta_simuladas), time.time() - tempo_de_inicio, nome_paciente, origem))

        insert_query(dataInserts)
        print(f"Insert de {len(frequencias_delta_simuladas[0])} dados feito para o {nome_paciente}")


def monitorar_pacientes():
    for paciente in pacientes:
        nome_paciente, caminho_arquivo_edf, possui_apnea = paciente
        for i in range(1, 2):
            thread = threading.Thread(target=gerar_frequencias, args=(
                caminho_arquivo_edf, possui_apnea, nome_paciente))
            print(f"Thread do {nome_paciente} - Numero Thread {i}")
            thread.start()
    return


monitorar_pacientes()
