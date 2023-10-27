import toga
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW, LEFT, RIGHT, Pack
from toga.constants import COLUMN, CENTER
from toga import ScrollContainer
from toga.style import Pack
from toga.handlers import wrapped_handler
from functools import partial
import io
import os
import textwrap

import http.client
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, quote
import re
import asyncio

numero_mp = ''
nome_usuario_g = ''
cor_vermelho = 'red'
cor_verde = 'green'
cor_amarelo = 'yellow'
cor_transparente = 'transparent'
cor_laranja = 'orange'
cor_preto = 'black'
cor_cinza = "gray"


class BancoAnder:
    def __init__(self):
        self.dados = {}

    def inserir(self, tabela, dados):
        if tabela not in self.dados:
            self.dados[tabela] = []
        self.dados[tabela].append(dados)

    def consultar(self, tabela):
        return self.dados.get(tabela, [])

    def consultar_cond(self, tabela, campo, condicao):
        return [dado for dado in self.dados.get(tabela, []) if dado.get(campo) == condicao]

    def atualizar(self, tabela, indice, dados):
        if tabela in self.dados and 0 <= indice < len(self.dados[tabela]):
            self.dados[tabela][indice] = dados

    def deletar(self, tabela, indice):
        if tabela in self.dados and 0 <= indice < len(self.dados[tabela]):
            del self.dados[tabela][indice]

    def atualizar_por_campo(self, tabela, campo, valor, campos_atualizacao):
        if tabela in self.dados:
            for indice, registro in enumerate(self.dados[tabela]):
                if campo in registro and registro[campo] == valor:
                    for campo_atualizacao, valor_atualizacao in campos_atualizacao.items():
                        self.dados[tabela][indice][campo_atualizacao] = valor_atualizacao

    def deletar_por_campo(self, tabela, campo, valor):
        if tabela in self.dados:
            indices_para_remover = []
            for indice, registro in enumerate(self.dados[tabela]):
                if campo in registro and registro[campo] == valor:
                    indices_para_remover.append(indice)

            for indice in reversed(indices_para_remover):
                self.deletar(tabela, indice)


class ConexaoBack4App:
    def __init__(self, banco):
        self.connection = http.client.HTTPSConnection('parseapi.back4app.com', 443)
        self.cabecalhos = {
            "X-Parse-Application-Id": "M6DRcF6dYX8nJ8W7AsXXh15DFLjLNzmLM6i5b8zO",
            "X-Parse-REST-API-Key": "e0pjcSIQHPjTZvYMx8jncgzOnZxcmoPfIhFrfKnr",
            "Content-Type": "application/json"
        }

        self.bc_ander = banco

    def query_sem_argumentos(self, tabela, ordem):
        parametro = {'order': ordem}
        query_string = urlencode(parametro)
        url = f'/classes/{tabela}?{query_string}'
        self.connection.request('GET', url, headers=self.cabecalhos)
        resposta = self.connection.getresponse()
        resultado = json.loads(resposta.read())
        lista_resultado = resultado['results']

        return lista_resultado

    def query_1_argumento(self, tabela, ordem, coluna, linhas):
        parametro = {'where': json.dumps({coluna: linhas}), 'order': ordem}
        query_string = urlencode(parametro)
        url = f'/classes/{tabela}?{query_string}'
        self.connection.request('GET', url, headers=self.cabecalhos)
        resposta = self.connection.getresponse()
        resultado = json.loads(resposta.read())
        lista_resultado = resultado['results']

        return lista_resultado

    def query_2_argumentos(self, tabela, ordem, coluna1, linha1, coluna2, linha2):
        lista_resultado = []
        parametro = {'where': json.dumps({coluna1: linha1, coluna2: linha2}), 'order': ordem}
        query_string = urlencode(parametro)
        url = f'/classes/{tabela}?{query_string}'
        self.connection.request('GET', url, headers=self.cabecalhos)
        resposta = self.connection.getresponse()
        resultado = json.loads(resposta.read())
        if resultado:
            lista_resultado = resultado['results']

        return lista_resultado

    def obter_usuario(self, username, senha):
        dados_usuario = []

        url = "/login?username={}&password={}".format(username, senha)
        self.connection.request('GET', url, headers=self.cabecalhos)
        response = self.connection.getresponse()
        response_data = response.read().decode('utf-8')
        result = json.loads(response_data)

        if 'objectId' in result:
            user_id = result['objectId']
        else:
            user_id = None

        if 'username' in result:
            user_nome = result['username']
        else:
            user_nome = None

        if 'email' in result:
            user_email = result['email']
        else:
            user_email = None

        dados = (user_id, user_nome, user_email)
        dados_usuario.append(dados)

        return result, dados_usuario

    def obter_mps_aberta(self, id_usuario):
        lista_completa = []

        resultado = self.query_2_argumentos('manutencao_preventiva', 'NUM_MP',
                                            'ID_USER', id_usuario,
                                            'STATUS', 'ABERTA')

        for mps in resultado:
            num_mp = mps['NUM_MP']
            texto_mp = f"MP {num_mp}"

            data_previsao = (mps['DATA_PREVISAO']['iso'])
            data = datetime.strptime(data_previsao, "%Y-%m-%dT%H:%M:%S.%fZ")
            data_formatada = data.strftime("%d/%m/%Y")

            id_cliente = mps['ID_CLIENTE']['objectId']
            resultado_cliente = self.query_1_argumento('cad_cliente', 'DESCRICAO', 'objectId', id_cliente)
            nome_cliente = resultado_cliente[0]['DESCRICAO']

            id_maquina = mps['ID_MAQUINA']['objectId']
            resultado_maquina = self.query_1_argumento('cad_maquina', 'DESCRICAO', 'objectId', id_maquina)
            nome_maquina = resultado_maquina[0]['DESCRICAO']

            dados_mp = (texto_mp, data_formatada, nome_cliente, nome_maquina, 'ABERTA')
            lista_completa.append(dados_mp)

        resultado1 = self.query_2_argumentos('manutencao_preventiva', 'NUM_MP',
                                             'ID_USER', id_usuario,
                                             'STATUS', 'INICIADA')

        for mps in resultado1:
            num_mp = mps['NUM_MP']
            texto_mp = f"MP {num_mp}"

            data_previsao = (mps['DATA_PREVISAO']['iso'])
            data = datetime.strptime(data_previsao, "%Y-%m-%dT%H:%M:%S.%fZ")
            data_formatada = data.strftime("%d/%m/%Y")

            id_cliente = mps['ID_CLIENTE']['objectId']
            resultado_cliente = self.query_1_argumento('cad_cliente', 'DESCRICAO', 'objectId', id_cliente)
            nome_cliente = resultado_cliente[0]['DESCRICAO']

            id_maquina = mps['ID_MAQUINA']['objectId']
            resultado_maquina = self.query_1_argumento('cad_maquina', 'DESCRICAO', 'objectId', id_maquina)
            nome_maquina = resultado_maquina[0]['DESCRICAO']

            dados_mp = (texto_mp, data_formatada, nome_cliente, nome_maquina, 'INICIADA')
            lista_completa.append(dados_mp)

        lista_de_listas_ordenada = sorted(lista_completa, key=lambda x: x[0])

        return lista_de_listas_ordenada

    def obter_dados_manut(self, num_mp):
        lista_completa = []

        resultado_mp = self.query_1_argumento('manutencao_preventiva', 'NUM_MP', 'NUM_MP', num_mp)
        id_mp = resultado_mp[0]['objectId']

        id_maq = resultado_mp[0]['ID_MAQUINA']['objectId']
        resultado_maquina = self.query_1_argumento('cad_maquina', 'objectId', 'objectId', id_maq)
        nome_maquina = resultado_maquina[0]['DESCRICAO']

        id_cliente = resultado_mp[0]['ID_CLIENTE']['objectId']
        resultado_cliente = self.query_1_argumento('cad_cliente', 'objectId', 'objectId', id_cliente)
        nome_cliente = resultado_cliente[0]['DESCRICAO']

        if resultado_mp and 'RECOMENDACAO' in resultado_mp[0]:
            considera = resultado_mp[0]['RECOMENDACAO']
        else:
            considera = ''

        if resultado_mp and 'DATA_INICIO' in resultado_mp[0]:
            data_inicio = resultado_mp[0]['DATA_INICIO']
        else:
            data_inicio = ''

        if resultado_mp and 'HORA_INICIO' in resultado_mp[0]:
            hora_inicio = resultado_mp[0]['HORA_INICIO']
        else:
            hora_inicio = ''

        if resultado_mp and 'DATA_FIM' in resultado_mp[0]:
            data_fim = resultado_mp[0]['DATA_FIM']
        else:
            data_fim = ''

        if resultado_mp and 'HORA_FIM' in resultado_mp[0]:
            hora_fim = resultado_mp[0]['HORA_FIM']
        else:
            hora_fim = ''

        if resultado_mp and 'STATUS' in resultado_mp[0]:
            status = resultado_mp[0]['STATUS']
        else:
            status = ''

        dados_mp = (id_mp, id_maq, nome_maquina, num_mp, nome_cliente,
                    considera, data_inicio, hora_inicio, data_fim, hora_fim)
        lista_completa.append(dados_mp)

        self.bc_ander.inserir('tab_manutencao_preventiva', {'objectId': id_mp,
                                                            'ID_MAQUINA': id_maq,
                                                            'nome_maquina': nome_maquina,
                                                            'NUM_MP': num_mp,
                                                            'ID_CLIENTE': id_cliente,
                                                            'nome_cliente': nome_cliente,
                                                            'RECOMENDACAO': considera,
                                                            'DATA_INICIO': data_inicio,
                                                            'HORA_INICIO': hora_inicio,
                                                            'DATA_FIM': data_fim,
                                                            'HORA_FIM': hora_fim,
                                                            'STATUS': status})

        return lista_completa

    def obter_num_serie(self, id_maq):
        lista_series = []

        resultado_num_serie = self.query_1_argumento('estrutura_num_serie', 'ID_MAQUINA', 'ID_MAQUINA', id_maq)

        if resultado_num_serie:
            for num_ser in resultado_num_serie:
                id_equip = num_ser['ID_EQUIPAMENTO']['objectId']
                resultado_equipamento = self.query_1_argumento('cad_equipamento', 'objectId',
                                                               'objectId', id_equip)
                nome_equipamento = resultado_equipamento[0]['DESCRICAO']

                modelo = num_ser['MODELO']
                num_serie = num_ser['NUMERO_SERIE']
                id_num_serie = num_ser['objectId']

                dados_series = (id_num_serie, id_equip, nome_equipamento, modelo, num_serie)
                lista_series.append(dados_series)

                self.bc_ander.inserir('tab_estrutura_num_serie', {'objectId': id_num_serie,
                                                                  'ID_EQUIPAMENTO': id_equip,
                                                                  'nome_equipamento': nome_equipamento,
                                                                  'MODELO': modelo,
                                                                  'NUMERO_SERIE': num_serie})

        return lista_series

    def obter_situacao(self):
        lista_completa = []
        resultado = self.query_sem_argumentos('cad_situacao', 'DESCRICAO')
        for checks in resultado:
            id_situacao = checks['objectId']
            nome_situacao = checks['DESCRICAO']

            dados = (id_situacao, nome_situacao)
            lista_completa.append(dados)

            self.bc_ander.inserir('tab_cad_situacao', {'objectId': id_situacao,
                                                       'NOME_SITUACAO': nome_situacao})

        return lista_completa

    def obter_checklist(self, id_mp):
        lista_completa = []

        resultado_check = self.query_1_argumento('mp_checklist', 'ID_MP', 'ID_MP', id_mp)

        for checks in resultado_check:
            id_check = checks['objectId']
            id_situacao = checks['ID_SITUACAO']['objectId']
            id_parametro = checks['ID_PARAMETRO']['objectId']

            resultado_parametro = self.query_1_argumento('cad_parametro', 'objectId', 'objectId', id_parametro)
            nome_parametro = resultado_parametro[0]['DESCRICAO']

            resultado_situacao = self.query_1_argumento('cad_situacao', 'objectId', 'objectId', id_situacao)
            nome_situacao = resultado_situacao[0]['DESCRICAO']

            dados = (id_check, id_situacao, nome_situacao, id_parametro, nome_parametro)
            lista_completa.append(dados)

        lista_de_listas_ordenada = sorted(lista_completa, key=lambda x: x[4])

        for lista in lista_de_listas_ordenada:
            id_check_l, id_situacao_l, nome_situacao_l, id_parametro_l, nome_parametro_l = lista

            self.bc_ander.inserir('tab_mp_checklist', {'objectId': id_check_l,
                                                       'ID_SITUACAO': id_situacao_l,
                                                       'NOME_SITUACAO': nome_situacao_l,
                                                       'ID_PARAMETRO': id_parametro_l,
                                                       'NOME_PARAMETRO': nome_parametro_l})

        return lista_completa

    def obter_obs(self, id_mp):
        lista_completa = []

        resultado_obs = self.query_1_argumento('mp_observacao', 'ID_MP', 'ID_MP', id_mp)

        for obs in resultado_obs:
            id_obs = obs['objectId']
            id_medicao = obs['ID_MEDICAO']['objectId']
            texto_obs = obs['OBSERVACAO']

            dados = (id_obs, id_medicao, texto_obs)
            lista_completa.append(dados)

            self.bc_ander.inserir('tab_mp_obs', {'objectId': id_obs,
                                                 'ID_MEDICAO': id_medicao,
                                                 'OBSERVACAO': texto_obs})

        return lista_completa

    def obter_medicao_carvoes(self, id_mp):
        resultado_carvao = self.query_1_argumento('mp_medicao_carvao', 'ID_MP', 'ID_MP', id_mp)

        carvao_por_motor = {}

        if resultado_carvao:
            for carvao in resultado_carvao:
                id_carvao = carvao['objectId']
                ordem_carvao = carvao['ORDEM_CARVAO']
                motor = carvao['MOTOR']

                if motor in carvao_por_motor:
                    if ordem_carvao in carvao_por_motor[motor]:
                        self.main_window.info_dialog("Atenção!", "A ORDEM_CARVAO está repetida para o mesmo motor!")
                        self.main_window.close()
                        break
                    else:
                        carvao_por_motor[motor].append(ordem_carvao)
                else:
                    carvao_por_motor[motor] = [ordem_carvao]

                if resultado_carvao and 'SEQ_1' in carvao:
                    seq_1 = carvao['SEQ_1']
                else:
                    seq_1 = ''

                if resultado_carvao and 'SEQ_2' in carvao:
                    seq_2 = carvao['SEQ_2']
                else:
                    seq_2 = ''

                if resultado_carvao and 'SEQ_3' in carvao:
                    seq_3 = carvao['SEQ_3']
                else:
                    seq_3 = ''

                if resultado_carvao and 'SEQ_4' in carvao:
                    seq_4 = carvao['SEQ_4']
                else:
                    seq_4 = ''

                if resultado_carvao and 'SEQ_5' in carvao:
                    seq_5 = carvao['SEQ_5']
                else:
                    seq_5 = ''

                if resultado_carvao and 'TROCA' in carvao:
                    seq_troca = carvao['TROCA']
                else:
                    seq_troca = ''

                self.bc_ander.inserir('tab_mp_medicao_carvao', {'objectId': id_carvao,
                                                                'MOTOR': motor,
                                                                'ORDEM_CARVAO': ordem_carvao,
                                                                'SEQ_1': seq_1,
                                                                'SEQ_2': seq_2,
                                                                'SEQ_3': seq_3,
                                                                'SEQ_4': seq_4,
                                                                'SEQ_5': seq_5,
                                                                'TROCA': seq_troca})

    def obter_medicao_capacitores(self, id_mp):
        lista_completa = []

        resultado_capacitor = self.query_1_argumento('mp_medicao_capacitor', 'ID_MP', 'ID_MP', id_mp)
        if resultado_capacitor:
            for capacitor in resultado_capacitor:
                id_capacitor = capacitor['objectId']
                filtro_capacitor = capacitor['FILTRO']

                if resultado_capacitor and 'FASE_A' in capacitor:
                    fase_a = capacitor['FASE_A']
                else:
                    fase_a = None

                if resultado_capacitor and 'FASE_B' in capacitor:
                    fase_b = capacitor['FASE_B']
                else:
                    fase_b = None

                if resultado_capacitor and 'FASE_C' in capacitor:
                    fase_c = capacitor['FASE_C']
                else:
                    fase_c = None

                if resultado_capacitor and 'TEMPERATURA' in capacitor:
                    temperatura = capacitor['TEMPERATURA']
                else:
                    temperatura = None

                dados = (id_capacitor, filtro_capacitor, fase_a, fase_b, fase_c, temperatura)
                lista_completa.append(dados)

                self.bc_ander.inserir('tab_mp_medicao_capacitor', {'objectId': id_capacitor,
                                                                   'FILTRO': filtro_capacitor,
                                                                   'FASE_A': fase_a,
                                                                   'FASE_B': fase_b,
                                                                   'FASE_C': fase_c,
                                                                   'TEMPERATURA': temperatura})

        return lista_completa

    def obter_medicao_barramentos(self, id_mp):
        lista_completa = []

        resultado_barramento = self.query_1_argumento('mp_medicao_barramento', 'ID_MP', 'ID_MP', id_mp)
        if resultado_barramento:
            for barramento in resultado_barramento:
                id_barra = barramento['objectId']

                if resultado_barramento and 'FASE_AB' in barramento:
                    fase_ab = barramento['FASE_AB']
                else:
                    fase_ab = None

                if resultado_barramento and 'FASE_AC' in barramento:
                    fase_ac = barramento['FASE_AC']
                else:
                    fase_ac = None

                if resultado_barramento and 'FASE_BC' in barramento:
                    fase_bc = barramento['FASE_BC']
                else:
                    fase_bc = None

                dados = (id_barra, id_mp, fase_ab, fase_ac, fase_bc)
                lista_completa.append(dados)

                self.bc_ander.inserir('tab_mp_medicao_barramento', {'objectId': id_barra,
                                                                    'FASE_AB': fase_ab,
                                                                    'FASE_AC': fase_ac,
                                                                    'FASE_BC': fase_bc})

        return lista_completa

    def salvar_no_banco(self, objetos):
        dados_json = json.dumps({"requests": objetos})

        url = '/batch'

        self.connection.request('POST', url, headers=self.cabecalhos, body=dados_json)

        response = self.connection.getresponse()
        response_data = response.read().decode('utf-8')

        result = json.loads(response_data)

        self.connection.close()


class Login(toga.App):
    formal_name = 'M. Preventiva Suzuki'

    def startup(self):
        self.bc_ander = BancoAnder()
        self.conexao = ConexaoBack4App(self.bc_ander)

        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=10))

        box1 = self.cria_box1()
        box2 = self.cria_box2()
        box3 = self.cria_box3()

        self.box_final.add(box1, box2, box3)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.box_final

        self.main_window.show()

    def cria_logo(self):
        self.box_imagem = toga.Box(style=Pack(padding=60, flex=1))

        self.image = toga.Image("resources/logo.png")
        self.imageview = toga.ImageView(self.image, style=Pack(flex=1))

        self.box_imagem.add(self.imageview)

        return self.box_imagem

    def cria_box1(self):
        self.box_um = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        box_imagem = self.cria_logo()
        self.box_um.add(box_imagem)

        return self.box_um

    def cria_box2(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=10))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Tela de Login', style=Pack(font_size=25, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=25, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=25, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.btn_box, self.width, self.height)

        return self.box_dois

    def cria_login(self):
        self.box_login = toga.Box(style=Pack(direction=COLUMN))

        self.input_usuario = toga.TextInput(placeholder='Nome de Usuário/E-mail', style=Pack(padding=1, height=45))
        self.input_senha = toga.PasswordInput(placeholder='Senha', style=Pack(padding=1, height=45))
        self.btn_login = toga.Button('Login', on_press=self.verifica_usuario, style=Pack(padding=10, font_size=15))

        self.box_login.add(self.input_usuario)
        self.box_login.add(self.input_senha)
        self.box_login.add(self.btn_login)

        return self.box_login

    def cria_box3(self):
        self.box_tres = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=2))
        login = self.cria_login()
        self.box_tres.add(login)

        return self.box_tres

    def verifica_usuario(self, widget):
        nome_usuario = self.input_usuario.value
        senha_usuario = self.input_senha.value

        if " " in nome_usuario:
            self.main_window.info_dialog("Atenção!", f'O campo "Nome de Usuário/E-mail"\n'
                                                     f'não pode conter espaços em branco!')
        elif " " in senha_usuario:
            self.main_window.info_dialog("Atenção!", f'O campo "Senha"\n'
                                                     f'não pode conter espaços em branco!')
        elif not nome_usuario:
            self.main_window.info_dialog("Atenção!", f'O campo "Nome de Usuário/E-mail" é obrigatório')
        elif not senha_usuario:
            self.main_window.info_dialog("Atenção!", f'O campo "senha" é obrigatório')
        else:
            resultado, dados_usuario = self.conexao.obter_usuario(nome_usuario, senha_usuario)

            if 'sessionToken' in resultado:
                user_id, user_nome, user_email = dados_usuario[0]
                self.bc_ander.inserir('tab_user', {'objectId': user_id, 'username': user_nome, 'email': user_email})
                self.mostrar_tela_principal(widget)
            else:
                error_message = resultado.get('error')

                if error_message == "username/email is required.":
                    msg_certa = 'O campo "Nome de Usuário/E-mail" é obrigatório'
                elif error_message == 'password is required.':
                    msg_certa = 'O campo "senha" é obrigatório'
                elif error_message == 'Invalid username/password.':
                    msg_certa = 'Nome de usuário/senha inválidos.'
                else:
                    msg_certa = f'{error_message}'

                self.main_window.error_dialog("Atenção!", f"{msg_certa}")

    def mostrar_tela_principal(self, widget):
        banco = self.bc_ander

        self.tela_principal = TelaPrincipal(self.main_window, banco)
        self.tela_principal.startup()


class TelaPrincipal:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_user = self.bc_ander.consultar('tab_user')
        user_id = dados_user[0]['objectId']

        self.lista_mps = self.conexao.obter_mps_aberta(user_id)

        self.box_principal = toga.Box(style=Pack(direction=COLUMN, padding=10))

        titulo = self.cria_titulo_pri()
        self.box_principal.add(titulo)

        self.label_mp = toga.Label('MP Abertas:', style=Pack(padding=5))
        self.box_principal.add(self.label_mp)

        num_mp_list = [itens[0] for itens in self.lista_mps]
        num_mp_set = set(num_mp_list)

        if len(num_mp_list) != len(num_mp_set):
            main_window.info_dialog("Atenção!", f'NÃO PODE HAVER NÚMERO DE "MP" REPETIDO!')
            main_window.close()
        else:
            for itens in self.lista_mps:
                num_mp, data_prev, cliente, maquina, status = itens
                self.btn_lista = toga.Button(f'{num_mp} ({status}) - {maquina} - {cliente}', style=Pack(padding=10),
                                             on_press=partial(self.chama_tudo))
                self.box_principal.add(self.btn_lista)

        self.main_window = main_window

    def cria_titulo_pri(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Tela Principal', style=Pack(font_size=25, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.width, self.btn_box, self.height)

        return self.box_dois

    def startup(self):
        self.main_window.content = self.box_principal

    def chama_tudo(self, widget):
        dados_botao = widget.text

        pos_inicio = dados_botao.find("MP ") + 3
        pos_final = dados_botao.find(" (")
        num_mp = dados_botao[pos_inicio:pos_final]

        dados_tabelas = self.conexao.obter_dados_manut(num_mp)
        num_mp_list = [itens[2] for itens in dados_tabelas]
        num_mp_set = set(num_mp_list)
        if len(num_mp_list) != len(num_mp_set):
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER PARAMETRO REPETIDO NA MESMA MP!')
            self.main_window.close()

        id_mp, id_maq, nome_maquina, num_mp, nome_cliente, \
        considera, data_inicio, hora_inicio, data_fim, hora_fim = dados_tabelas[0]

        lista_series = self.conexao.obter_num_serie(id_maq)
        num_mp_list = [itens[4] for itens in lista_series]
        num_mp_set = set(num_mp_list)
        if len(num_mp_list) != len(num_mp_set):
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER PARAMETRO REPETIDO NA MESMA MP!')
            self.main_window.close()

        lista_situacao = self.conexao.obter_situacao()

        lista_checklist = self.conexao.obter_checklist(id_mp)
        num_mp_list = [itens[3] for itens in lista_checklist]
        num_mp_set = set(num_mp_list)
        if len(num_mp_list) != len(num_mp_set):
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER PARAMETRO REPETIDO NA MESMA MP!')
            self.main_window.close()

        lista_observacao = self.conexao.obter_obs(id_mp)
        num_mp_list = [itens[1] for itens in lista_observacao]
        num_mp_set = set(num_mp_list)
        if len(num_mp_list) != len(num_mp_set):
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER MAIS DE UMA OBS PARA\n'
                                                     f' CADA EQUIPAMENTO REPETIDO NA MESMA MP!')
            self.main_window.close()

        self.conexao.obter_medicao_carvoes(id_mp)

        lista_capacitores = self.conexao.obter_medicao_capacitores(id_mp)
        if lista_capacitores:
            num_mp_list = [itens[1] for itens in lista_capacitores]
            num_mp_set = set(num_mp_list)
            if len(num_mp_list) != len(num_mp_set):
                self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER SEQUENCIA CAPACITORES REPETIDO NA MESMA MP!')
                self.main_window.close()

        lista_barramentos = self.conexao.obter_medicao_barramentos(id_mp)
        if lista_barramentos:
            num_mp_list = [itens[1] for itens in lista_barramentos]
            num_mp_set = set(num_mp_list)
            if len(num_mp_list) != len(num_mp_set):
                self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER BARRAMENTO REPETIDO NA MESMA MP!')
                self.main_window.close()

        self.mostrar_tela_maquina()

    def mostrar_tela_maquina(self):
        banco = self.bc_ander

        tela_maquina = TelaMaquina(self.main_window, banco)
        tela_maquina.startup()

    def mostrar_tela_maq_ext3(self, widget):
        bababa = widget.text
        pos_num_final = bababa.find(" -")
        define_mp = bababa[:pos_num_final]

        self.tela_extr3 = TelaMaqExt3(self.main_window, define_mp)
        self.tela_extr3.startup()

    def mostrar_tela_maq_ext5(self, widget):
        bababa = widget.text
        pos_num_final = bababa.find(" -")
        define_mp = bababa[:pos_num_final]

        self.tela_extr5 = TelaMaqExt5(self.main_window, define_mp)
        self.tela_extr5.startup()

    def mostrar_tela_maq_sub(self, widget):
        bababa = widget.text
        pos_num_final = bababa.find(" -")
        define_mp = bababa[:pos_num_final]

        self.tela_sub = TelaMaqSub(self.main_window, define_mp)
        self.tela_sub.startup()


class TelaMaquina:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.porc_checklist = ''
        self.porc_carvao = ''
        self.porc_capacitor = ''
        self.porc_barramento = ''

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1()
        self.box_final.add(box1)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        nome_maquina = dados_manut[0]['nome_maquina']

        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label(f'Manutenção {nome_maquina}', style=Pack(font_size=25, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.width, self.btn_box, self.height)

        return self.box_dois

    def cria_num_mp(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        num_mp = dados_manut[0]['NUM_MP']
        status = dados_manut[0]['STATUS']

        self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.label_mp_extraido = toga.Label(f'MP {num_mp} ({status})', style=Pack(font_size=20, padding=5, flex=1))
        self.box_mp.add(self.label_mp_extraido)
        return self.box_mp

    def cria_data_inicio(self):
        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')
        if resultado_mp and 'DATA_INICIO' in resultado_mp[0]:
            data_inicio = resultado_mp[0]['DATA_INICIO']
        else:
            data_inicio = ''

        self.box_data = toga.Box(style=Pack(direction=ROW, padding=2))
        self.box_cx_data = toga.Box(style=Pack(direction=ROW, padding=2))

        self.label_data = toga.Label('Data Inicio:',
                                     style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
        self.box_data.add(self.label_data)

        # Definição da máscara da data
        date_mask = "##/##/####"

        self.textinput_data_ini = toga.TextInput(style=Pack(padding=2, flex=1 / 2),
                                                 value=data_inicio,
                                                 placeholder="DD/MM/AAAA",
                                                 on_change=self.configura_data)

        # Aplicação da máscara no TextInput
        self.textinput_data_ini.mask = textwrap.dedent(f"""{date_mask}{date_mask.replace('#', '9')}""")

        self.box_cx_data.add(self.textinput_data_ini)

        return self.box_data, self.box_cx_data

    def cria_hora_inicio(self):
        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')
        if resultado_mp and 'HORA_INICIO' in resultado_mp[0]:
            hora_inicio = resultado_mp[0]['HORA_INICIO']
        else:
            hora_inicio = ''

        self.box_inihora = toga.Box(style=Pack(direction=ROW, padding=2))
        self.box_cx_inihora = toga.Box(style=Pack(direction=ROW, padding=2))

        self.label_hora_ini = toga.Label('Hora Início:',
                                         style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
        self.box_inihora.add(self.label_hora_ini)

        # Definição da máscara de horário
        time_mask = "##:##"

        self.textinput_hora_ini = toga.TextInput(style=Pack(padding=1, flex=1 / 2),
                                                 value=hora_inicio,
                                                 placeholder="HH:MM",
                                                 on_change=self.configura_hora)

        # Aplicação da máscara no TextInput
        self.textinput_hora_ini.mask = textwrap.dedent(f"""{time_mask}{time_mask.replace('#', '9')}""")
        self.box_cx_inihora.add(self.textinput_hora_ini)

        return self.box_inihora, self.box_cx_inihora

    def cria_salvar_inicio(self):
        self.box_btn_finalizar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_finalizar = toga.Button('Salvar Data/Hora Início',
                                         on_press=self.verifica_salva_ini,
                                         style=Pack(padding_bottom=5))
        self.box_btn_finalizar.add(self.btn_finalizar)

        return self.box_btn_finalizar

    def cria_recomendacao(self):
        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')
        if resultado_mp and 'RECOMENDACAO' in resultado_mp[0]:
            considera = resultado_mp[0]['RECOMENDACAO']
        else:
            considera = ''

        self.box_obs = toga.Box(style=Pack(direction=COLUMN, padding=5))

        if considera:
            palavras = considera.split()

            grupos_de_palavras = [palavras[i:i + 9] for i in range(0, len(palavras), 9)]

            texto_separado = []

            for i, grupo in enumerate(grupos_de_palavras):
                nova_variavel = '_'.join(grupo)
                nova_variavel = nova_variavel.replace('_', ' ')

                texto_separado.append(nova_variavel)

            self.label_rec1 = toga.Label(f"Recomendações:",
                                         style=Pack(flex=1, font_size=15, font_weight='bold', padding=5))
            self.box_obs.add(self.label_rec1)

            for textinho in texto_separado:
                self.label_considera = toga.Label(f"{textinho}", style=Pack(flex=1, padding=3))
                self.box_obs.add(self.label_considera)

        return self.box_obs

    def cria_num_serie(self):
        box_botao = toga.Box(style=Pack(direction=COLUMN, padding=5))
        resultado_mp = self.bc_ander.consultar('tab_estrutura_num_serie')
        if resultado_mp:
            btn_verifica = toga.Button('Nº de Série - Equipamentos', on_press=self.mostrar_telarecetapaserie,
                                       style=Pack(flex=1, padding_bottom=3))
            box_botao.add(btn_verifica)

        return box_botao

    def cria_checklist(self):
        box_botao = toga.Box(style=Pack(direction=COLUMN, padding=5))

        resultado_mp = self.bc_ander.consultar('tab_mp_checklist')
        if resultado_mp:
            qtde_parametros = len(resultado_mp)
            qtde_nenhum = 0

            for situacao in resultado_mp:
                nome_sit = situacao['NOME_SITUACAO']
                if nome_sit == "NENHUM":
                    qtde_nenhum = qtde_nenhum + 1

            porc_concluido = ((qtde_parametros - qtde_nenhum) / qtde_parametros) * 100

            corzinha = cor_transparente
            if porc_concluido >= 100:
                self.porc_checklist = str("%.0f" % 100) + "%"
                corzinha = cor_verde
            else:
                self.porc_checklist = str("%.0f" % porc_concluido) + "%"

            btn_verifica = toga.Button(f'Checklist - Parâmetros - {self.porc_checklist} Concluído',
                                       on_press=self.mostrar_telachecklist,
                                       style=Pack(flex=1, padding_bottom=3, background_color=corzinha))
            box_botao.add(btn_verifica)

        return box_botao

    def cria_carvao_motor(self):
        box_botao = toga.Box(style=Pack(direction=COLUMN, padding=5))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_carvao')
        if resultado_mp:
            qtde_itens = len(resultado_mp) * 5
            qtde_nenhum = 0
            for carvao in resultado_mp:
                seq_1 = carvao['SEQ_1']
                seq_2 = carvao['SEQ_2']
                seq_3 = carvao['SEQ_3']
                seq_4 = carvao['SEQ_4']
                seq_5 = carvao['SEQ_5']
                if seq_1 == "":
                    qtde_nenhum = qtde_nenhum + 1
                if seq_2 == "":
                    qtde_nenhum = qtde_nenhum + 1
                if seq_3 == "":
                    qtde_nenhum = qtde_nenhum + 1
                if seq_4 == "":
                    qtde_nenhum = qtde_nenhum + 1
                if seq_5 == "":
                    qtde_nenhum = qtde_nenhum + 1

            porc_concluido = ((qtde_itens - qtde_nenhum) / qtde_itens) * 100

            corzinha = cor_transparente
            if porc_concluido >= 100:
                self.porc_carvao = str("%.0f" % 100) + "%"
                corzinha = cor_verde
            else:
                self.porc_carvao = str("%.0f" % porc_concluido) + "%"

            btn_verifica = toga.Button(f'Medição Carvões - {self.porc_carvao} Concluído',
                                       on_press=self.mostrar_telacarvaomotor,
                                       style=Pack(flex=1, padding_bottom=3, background_color=corzinha))
            box_botao.add(btn_verifica)

        return box_botao

    def cria_capacitor(self):
        box_botao = toga.Box(style=Pack(direction=COLUMN, padding=5))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_capacitor')
        if resultado_mp:
            qtde_itens = len(resultado_mp) * 3
            qtde_nenhum = 0
            for carvao in resultado_mp:
                fase_a = carvao['FASE_A']
                fase_b = carvao['FASE_B']
                fase_c = carvao['FASE_C']

                if fase_a == "":
                    qtde_nenhum = qtde_nenhum + 1
                if fase_b == "":
                    qtde_nenhum = qtde_nenhum + 1
                if fase_c == "":
                    qtde_nenhum = qtde_nenhum + 1

            porc_concluido = ((qtde_itens - qtde_nenhum) / qtde_itens) * 100

            corzinha = cor_transparente
            if porc_concluido >= 100:
                self.porc_capacitor = str("%.0f" % 100) + "%"
                corzinha = cor_verde
            else:
                self.porc_capacitor = str("%.0f" % porc_concluido) + "%"

            btn_verifica = toga.Button(f'Medição Capacitores - {self.porc_capacitor} Concluído',
                                       on_press=self.mostrar_telacapacitor,
                                       style=Pack(flex=1, padding_bottom=3, background_color=corzinha))
            box_botao.add(btn_verifica)

        return box_botao

    def cria_barramento(self):
        box_botao = toga.Box(style=Pack(direction=COLUMN, padding=5))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_barramento')
        if resultado_mp:
            qtde_itens = len(resultado_mp) * 3
            qtde_nenhum = 0
            for carvao in resultado_mp:
                fase_a = carvao['FASE_AB']
                fase_b = carvao['FASE_AC']
                fase_c = carvao['FASE_BC']

                if fase_a == "":
                    qtde_nenhum = qtde_nenhum + 1
                if fase_b == "":
                    qtde_nenhum = qtde_nenhum + 1
                if fase_c == "":
                    qtde_nenhum = qtde_nenhum + 1

            porc_concluido = ((qtde_itens - qtde_nenhum) / qtde_itens) * 100

            corzinha = cor_transparente
            if porc_concluido >= 100:
                self.porc_barramento = str("%.0f" % 100) + "%"
                corzinha = cor_verde
            else:
                self.porc_barramento = str("%.0f" % porc_concluido) + "%"

            btn_verifica = toga.Button(f'Medição Barramentos - {self.porc_barramento} Concluído',
                                       on_press=self.mostrar_telabarramento,
                                       style=Pack(flex=1, padding_bottom=3, background_color=corzinha))
            box_botao.add(btn_verifica)

        return box_botao

    def cria_data_fim(self):
        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')
        if resultado_mp and 'DATA_FIM' in resultado_mp[0]:
            data_fim = resultado_mp[0]['DATA_FIM']
        else:
            data_fim = ''

        self.box_datafim = toga.Box(style=Pack(direction=ROW, padding=2))
        self.box_cx_datafim = toga.Box(style=Pack(direction=ROW, padding=2))

        self.label_datafim = toga.Label('Data Final:',
                                        style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
        self.box_datafim.add(self.label_datafim)

        # Definição da máscara da data
        date_mask = "##/##/####"

        self.textinput_data_fim = toga.TextInput(style=Pack(padding=2, flex=1 / 2),
                                                 value=data_fim,
                                                 placeholder="DD/MM/AAAA",
                                                 on_change=self.configura_data)

        # Aplicação da máscara no TextInput
        self.textinput_data_fim.mask = textwrap.dedent(f"""{date_mask}{date_mask.replace('#', '9')}""")

        self.box_cx_datafim.add(self.textinput_data_fim)

        return self.box_datafim, self.box_cx_datafim

    def cria_hora_fim(self):
        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')
        if resultado_mp and 'HORA_FIM' in resultado_mp[0]:
            hora_fim = resultado_mp[0]['HORA_FIM']
        else:
            hora_fim = ''

        self.box_fimhora = toga.Box(style=Pack(direction=ROW, padding=2))
        self.box_cx_fimhora = toga.Box(style=Pack(direction=ROW, padding=2))

        self.label_hora_fim = toga.Label('Hora Final:',
                                         style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
        self.box_fimhora.add(self.label_hora_fim)

        # Definição da máscara de horário
        time_mask = "##:##"

        self.textinput_hora_fim = toga.TextInput(style=Pack(padding=1, flex=1 / 2),
                                                 value=hora_fim,
                                                 placeholder="HH:MM",
                                                 on_change=self.configura_hora)

        # Aplicação da máscara no TextInput
        self.textinput_hora_fim.mask = textwrap.dedent(f"""{time_mask}{time_mask.replace('#', '9')}""")
        self.box_cx_fimhora.add(self.textinput_hora_fim)

        return self.box_fimhora, self.box_cx_fimhora

    def cria_finalizar(self):
        self.box_btn_finalizar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_finalizar = toga.Button('Finalizar',
                                         on_press=self.verifica_data_final,
                                         style=Pack(padding_bottom=5))
        self.box_btn_finalizar.add(self.btn_finalizar)

        return self.box_btn_finalizar

    def cria_principal(self):
        self.box_btn_principal = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.btn_tela_principal = toga.Button('Ir para Tela Principal',
                                              on_press=self.mostrar_tela_principal,
                                              style=Pack(padding_bottom=5))
        self.box_btn_principal.add(self.btn_tela_principal)

        return self.box_btn_principal

    def cria_box1(self):
        self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        titulo = self.cria_titulo()
        num_mp = self.cria_num_mp()
        considera = self.cria_recomendacao()
        ini_data, cx_inidata = self.cria_data_inicio()
        ini_hora, cx_inihora = self.cria_hora_inicio()
        salvar_ini = self.cria_salvar_inicio()
        etapaserie = self.cria_num_serie()
        etapa1 = self.cria_checklist()
        etapa2 = self.cria_carvao_motor()
        etapa3 = self.cria_capacitor()
        etapa4 = self.cria_barramento()
        fim_data, cx_fimdata = self.cria_data_fim()
        fimhora, cx_fimhora = self.cria_hora_fim()
        finalizar = self.cria_finalizar()
        principal = self.cria_principal()

        self.box_semifinal1.add(titulo, num_mp, considera, ini_data, cx_inidata, ini_hora, cx_inihora, salvar_ini,
                                etapaserie, etapa1, etapa2, etapa3, etapa4, fim_data, cx_fimdata,
                                fimhora, cx_fimhora, finalizar, principal)

        return self.box_semifinal1

    def startup(self):
        self.main_window.content = self.scroll_container

    def mostrar_telarecetapaserie(self, widget):
        banco = self.bc_ander

        self.tela_recupera_serie = TelaNumeroSerie(self.main_window, banco)
        self.tela_recupera_serie.startup()

    def mostrar_telachecklist(self, widget):
        banco = self.bc_ander

        self.tela_recupera_verifica = TelaChecklist(self.main_window, banco)
        self.tela_recupera_verifica.startup()

    def mostrar_telacarvaomotor(self, widget):
        banco = self.bc_ander

        self.tela_recupera_carvoes = TelaCarvaoMotor(self.main_window, banco)
        self.tela_recupera_carvoes.startup()

    def mostrar_telacapacitor(self, widget):
        banco = self.bc_ander

        self.tela_recupera_carvoes = TelaCapacitor(self.main_window, banco)
        self.tela_recupera_carvoes.startup()

    def mostrar_telabarramento(self, widget):
        banco = self.bc_ander

        tela = TelaBarramento(self.main_window, banco)
        tela.startup()

    def mostrar_tela_principal(self, widget):
        dados_user = self.bc_ander.consultar('tab_user')
        user_id = dados_user[0]['objectId']
        user_nome = dados_user[0]['username']
        user_email = dados_user[0]['email']

        banco = BancoAnder()
        banco.inserir('tab_user', {'objectId': user_id, 'username': user_nome, 'email': user_email})

        self.tela_principal = TelaPrincipal(self.main_window, banco)
        self.tela_principal.startup()

    def configura_data(self, widget):
        try:
            # Remove caracteres não numéricos
            input_text = ''.join(filter(str.isdigit, widget.value))

            # Formatação da data (DD/MM/AAAA)
            if len(input_text) >= 8:
                formatted_date = f"{input_text[:2]}/{input_text[2:4]}/{input_text[4:]}"
                if widget.value != formatted_date:
                    widget.value = formatted_date

        except Exception as e:
            print("\n\n\n\n\n")
            print(f"Erro durante o evento on_change: {e}")
            print("\n\n\n\n\n")

    def configura_hora(self, widget):
        try:
            # Remover caracteres não numéricos
            input_text = ''.join(filter(str.isdigit, widget.value))

            # Formatação do horário (HH:MM)
            if len(input_text) >= 4:
                formatted_time = f"{input_text[:2]}:{input_text[2:4]}"
                if widget.value != formatted_time:
                    widget.value = formatted_time

        except Exception as e:
            print(f"Erro durante o evento on_change: {e}")

    def verifica_salva_ini(self, widget):
        def validar_data_hora(data_str, hora_str):
            try:
                data = datetime.strptime(data_str, '%d/%m/%Y')
                hora = datetime.strptime(hora_str, '%H:%M')

                return data, hora
            except ValueError:
                return None, None

        data_lancada = self.textinput_data_ini.value
        hora_lancada = self.textinput_hora_ini.value

        data_str, hora_str = validar_data_hora(data_lancada, hora_lancada)

        if data_str and hora_str:
            self.salvar_ini(widget)
        else:
            self.main_window.info_dialog("Atenção!", f'FORMATO DE DATA E HORA INVÁLIDOS!')

    def salvar_ini(self, widget):
        lista_json_dataini = []

        data_lancada = self.textinput_data_ini.value
        hora_lancada = self.textinput_hora_ini.value

        resultado_mp = self.bc_ander.consultar('tab_manutencao_preventiva')

        if resultado_mp and 'DATA_INICIO' in resultado_mp[0]:
            data_inicio = resultado_mp[0]['DATA_INICIO']
        else:
            data_inicio = ''

        if resultado_mp and 'HORA_INICIO' in resultado_mp[0]:
            hora_inicio = resultado_mp[0]['HORA_INICIO']
        else:
            hora_inicio = ''

        if data_lancada == '':
            self.main_window.info_dialog("Atenção!", f'O CAMPO "DATA INÍCIO" NÃO PODE ESTAR VAZIO!')
        elif hora_lancada == '':
            self.main_window.info_dialog("Atenção!", f'O CAMPO "HORA INÍCIO" NÃO PODE ESTAR VAZIO!')
        elif data_lancada == data_inicio and hora_lancada == hora_inicio:
            self.main_window.info_dialog("Atenção!", f'DATA E HORA PRECISA SER\n ALTERADO PARA SALVAR!')
        elif data_lancada == data_inicio:
            print("alterar só a hora")
            pra_atualizar = {"HORA_INICIO": hora_lancada, "STATUS": "INICIADA"}

            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}", "body": pra_atualizar}
            lista_json_dataini.append(objeto)

            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp, pra_atualizar)

        elif hora_lancada == hora_inicio:
            print("alterar só a data")

            pra_atualizar = {"DATA_INICIO": data_lancada, "STATUS": "INICIADA"}

            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}", "body": pra_atualizar}
            lista_json_dataini.append(objeto)

            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp, pra_atualizar)

        else:
            print("salva data e hora")
            pra_atualizar = {"DATA_INICIO": data_lancada, "HORA_INICIO": hora_lancada, "STATUS": "INICIADA"}

            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}", "body": pra_atualizar}
            lista_json_dataini.append(objeto)

            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp, pra_atualizar)

        final = 0

        if not lista_json_dataini:
            final = 0
        elif lista_json_dataini:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_dataini)

        if final > 0:
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')

    async def confirm_and_proceed(self, widget, dados):
        resposta = await self.main_window.confirm_dialog("Atenção!", f"{dados}\n"
                                                                     f"DESEJA ENCERRAR MESMO ASSIM?")
        if resposta:
            self.finalizar(widget)

    def verifica_data_final(self, widget):
        def validar_data_hora(data_str_ini, hora_str_ini, data_str_fim, hora_str_fim):
            try:
                data_ini = datetime.strptime(data_str_ini, '%d/%m/%Y')
                hora_ini = datetime.strptime(hora_str_ini, '%H:%M')

                data_fim = datetime.strptime(data_str_fim, '%d/%m/%Y')
                hora_fim = datetime.strptime(hora_str_fim, '%H:%M')

                return data_ini, hora_ini, data_fim, hora_fim
            except ValueError:
                return None, None, None, None

        dt_inicio_la = self.textinput_data_ini.value
        hor_inicio_la = self.textinput_hora_ini.value

        dt_final_la = self.textinput_data_fim.value
        hor_final_la = self.textinput_hora_fim.value

        dt_in, hor_in, dt_fi, hor_fi = validar_data_hora(dt_inicio_la, hor_inicio_la, dt_final_la, hor_final_la)

        if dt_in and hor_in and dt_fi and hor_fi:
            self.verifica_salvamento(widget)
        else:
            self.main_window.info_dialog("Atenção!", f'FORMATO DE DATA E HORA INVÁLIDOS!')

    def verifica_salvamento(self, widget):
        dt_inicio_lanc = self.textinput_data_ini.value
        hor_inicio_lanc = self.textinput_hora_ini.value

        dt_final_lanc = self.textinput_data_fim.value
        hor_final_lanc = self.textinput_hora_fim.value

        tudo_concluido = []

        if dt_final_lanc == "" or hor_final_lanc == "" or dt_inicio_lanc == "" or hor_inicio_lanc == "":
            self.main_window.info_dialog("Atenção!", f'DATA E HORA PRECISA SER\n PREENCHIDO PARA FINALIZAR!')
        else:
            if self.porc_checklist:
                posicao_check = self.porc_checklist.find(" %")
                check = self.porc_checklist[:posicao_check]
                if int(check) < 100:
                    dados = ("CHECKLIST", self.porc_checklist)
                    tudo_concluido.append(dados)

            if self.porc_carvao:
                posicao_carvao = self.porc_carvao.find(" %")
                carvao = self.porc_carvao[:posicao_carvao]
                if int(carvao) < 100:
                    dados = ("CARVÃO", self.porc_carvao)
                    tudo_concluido.append(dados)

            if self.porc_capacitor:
                posicao_capacitor = self.porc_capacitor.find(" %")
                capacitor = self.porc_capacitor[:posicao_capacitor]
                if int(capacitor) < 100:
                    dados = ("CAPACITOR", self.porc_capacitor)
                    tudo_concluido.append(dados)

            if self.porc_barramento:
                posicao_barramento = self.porc_barramento.find(" %")
                barramento = self.porc_barramento[:posicao_barramento]
                if int(barramento) < 100:
                    dados = ("BARRAMENTO", self.porc_barramento)
                    tudo_concluido.append(dados)

            if tudo_concluido:
                texto = ''
                if len(tudo_concluido) == 1:
                    for i in tudo_concluido:
                        medicao, porc = i
                        texto += f"A MEDIÇÃO DO {medicao} NÃO ESTÁ CONCLUÍDA!"
                else:
                    texto += f"ALGUMAS MEDIÇÕES NÃO ESTÃO CONCLUÍDAS:\n"
                    for i in tudo_concluido:
                        medicao, porc = i
                        texto += f"- {medicao} {porc}\n"

                asyncio.create_task(self.confirm_and_proceed(widget, texto))
            else:
                self.finalizar(widget)

    def finalizar(self, widget):
        lista_json_datafim = []

        dt_final_lanc = self.textinput_data_fim.value
        hor_final_lanc = self.textinput_hora_fim.value

        print("salva data e hora")

        pra_atualizar = {"DATA_FIM": dt_final_lanc,
                         "HORA_FIM": hor_final_lanc,
                         "STATUS": "FINALIZADA"}

        objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}", "body": pra_atualizar}
        lista_json_datafim.append(objeto)

        self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp, pra_atualizar)

        final = 0

        if not lista_json_datafim:
            final = 0
        elif lista_json_datafim:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_datafim)

        if final > 0:
            dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
            num_mp = dados_manut[0]['NUM_MP']

            self.main_window.info_dialog("Atenção!", f'MP {num_mp} FINALIZADA COM SUCESSO!')
            self.mostrar_tela_principal(widget)


class TelaNumeroSerie:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.id_medicao_serie = 'OGHwDvvZkK'

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1_recserie()
        self.box_final.add(box1)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo_recserie(self):
        try:
            self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
            self.name_box = toga.Box(style=Pack(direction=ROW))

            self.button = toga.Label('Nº de Série - Equipamentos', style=Pack(font_size=24, font_weight='bold'))

            self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
            self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

            self.btn_box = toga.Box(style=Pack(direction=ROW))
            self.btn_box.add(self.button)

            self.box_dois.add(self.name_box)
            self.box_dois.add(self.btn_box, self.width, self.height)

            return self.box_dois

        except Exception as e:
            print(f'Houve um problema com a função "cria_titulo_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_num_mp_maq_recserie(self):
        try:
            dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
            num_mp = dados_manut[0]['NUM_MP']

            self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
            self.label_mp_extraido = toga.Label(f'MP {num_mp}', style=Pack(font_size=20, padding=5, flex=1))
            self.box_mp.add(self.label_mp_extraido)
            return self.box_mp

        except Exception as e:
            print(f'Houve um problema com a função "cria_num_mp_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def verifica_equipamento(self):
        try:
            self.lista_equip_salva = []
            lista_equipamentos = []

            box_final = toga.Box(style=Pack(direction=COLUMN, padding=1))

            resultado_mp = self.bc_ander.consultar('tab_estrutura_num_serie')
            if resultado_mp:
                for indices in resultado_mp:
                    id_equip_i = indices['ID_EQUIPAMENTO']
                    nome_equip_i = indices['nome_equipamento']

                    if id_equip_i in lista_equipamentos:
                        pass
                    else:
                        dadis = (id_equip_i, nome_equip_i)
                        lista_equipamentos.append(dadis)

            if lista_equipamentos:
                teste = []

                for idezinho, nomezinho in lista_equipamentos:
                    if not idezinho in teste:
                        teste.append(idezinho)
                        box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
                        name_box = toga.Box(style=Pack(direction=ROW))

                        button = toga.Label(f'Equipamento: {nomezinho}', style=Pack(font_size=15, font_weight='bold'))

                        width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
                        height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

                        btn_box = toga.Box(style=Pack(direction=ROW))
                        btn_box.add(button)

                        box_dois.add(name_box)
                        box_dois.add(btn_box, width, height)
                        box_final.add(box_dois)

                        box_titulo = toga.Box(style=Pack(direction=ROW, padding=1))

                        label_modelo = toga.Label('Modelo:',
                                                  style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
                        box_titulo.add(label_modelo)

                        label_num_serie = toga.Label('Número de Série:',
                                                     style=Pack(text_align='center', font_weight='bold', flex=1 / 3))
                        box_titulo.add(label_num_serie)
                        box_final.add(box_titulo)

                        box_caixa_final = toga.Box(style=Pack(direction=COLUMN, padding=1))

                        for indices1 in resultado_mp:
                            id_num_serie_i = indices1['objectId']
                            modelo_i = indices1['MODELO']
                            num_serie_i = indices1['NUMERO_SERIE']
                            id_equip_i = indices1['ID_EQUIPAMENTO']

                            if idezinho == id_equip_i:
                                box_caixa_mod = toga.Box(style=Pack(direction=ROW, padding=1))

                                textinput_mod2 = toga.TextInput(value=f"{modelo_i}", style=Pack(font_size=14, padding=1,
                                                                                                flex=1 / 3))
                                textinput_mod3 = toga.TextInput(value=f"{num_serie_i}",
                                                                style=Pack(font_size=14, padding=1,
                                                                           flex=1 / 3))
                                didos = (id_num_serie_i, textinput_mod2, textinput_mod3)
                                self.lista_equip_salva.append(didos)

                                box_caixa_mod.add(textinput_mod2, textinput_mod3)
                                box_caixa_final.add(box_caixa_mod)
                                box_final.add(box_caixa_final)

            return box_final

        except Exception as e:
            print(f'Houve um problema com a função "verifica_equipamento".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_obs_recserie(self):
        try:
            self.box_obs = toga.Box(style=Pack(padding=20))

            txt_check = ''

            resultado_mp = self.bc_ander.consultar('tab_mp_obs')
            if resultado_mp:
                for indices in resultado_mp:
                    id_equip = indices['ID_MEDICAO']

                    if id_equip == f"{self.id_medicao_serie}":
                        texto_obs = indices['OBSERVACAO']

                        txt_check = texto_obs

            self.textinput_obs = toga.MultilineTextInput(value=txt_check, placeholder='Observação', style=Pack(flex=1))
            self.textinput_obs.style.update(height=100)
            self.textinput_obs.style.update(width=self.box_obs.style.width)

            self.box_obs.add(self.textinput_obs)

            return self.box_obs

        except Exception as e:
            print(f'Houve um problema com a função "cria_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_salvar_recserie(self):
        try:
            self.box_btn_salvar = toga.Box(style=Pack(direction=COLUMN, padding=10))
            self.btn_salvar = toga.Button('Salvar Observação ref. Nº de Séries',
                                          on_press=self.salvar_recserie,
                                          style=Pack(padding_bottom=5))
            self.box_btn_salvar.add(self.btn_salvar)

            return self.box_btn_salvar

        except Exception as e:
            print(f'Houve um problema com a função "cria_salvar_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_maq_recserie(self):
        try:
            self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

            self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                           on_press=self.mostrar_tela_maq_recserie,
                                                           style=Pack(padding_bottom=5))
            self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

            return self.box_btn_check_recuperadora

        except Exception as e:
            print(f'Houve um problema com a função "cria_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_box1_recserie(self):
        try:
            self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

            titulo = self.cria_titulo_recserie()
            mp = self.cria_num_mp_maq_recserie()
            box_series = self.verifica_equipamento()
            obs = self.cria_obs_recserie()
            btn_salvar = self.cria_salvar_recserie()
            btn_maq_rec = self.cria_maq_recserie()

            self.box_semifinal1.add(titulo, mp, box_series, obs, btn_salvar, btn_maq_rec)

            return self.box_semifinal1

        except Exception as e:
            print(f'Houve um problema com a função "cria_box1_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def startup(self):
        try:
            self.main_window.content = self.scroll_container

        except Exception as e:
            print(f'Houve um problema com a função "startup".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def mostrar_tela_maq_recserie(self, widget):
        try:
            banco = self.bc_ander

            tela = TelaMaquina(self.main_window, banco)
            tela.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salva_obs_recserie(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_serie)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_recserie(self, widget):
        final = 0

        lista_json_obs = self.salva_obs_recserie()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_recserie_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_recserie_atualizada(self, widget):
        try:
            banco = self.bc_ander

            self.tela_recupera = TelaMaquina(self.main_window, banco)
            self.tela_recupera.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie_atualizada".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')


class TelaChecklist:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.id_medicao_check = 'QWJH1GZinb'

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        box1 = self.cria_box1_rec1()
        self.box_final.add(box1)

        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo_rec1(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Checklist - Parâmetros', style=Pack(font_size=24, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.btn_box, self.width, self.height)

        return self.box_dois

    def cria_num_mp_maq_rec1(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        num_mp = dados_manut[0]['NUM_MP']

        self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.label_mp_extraido = toga.Label(f'MP {num_mp}', style=Pack(font_size=20, padding=5, flex=1))
        self.box_mp.add(self.label_mp_extraido)
        return self.box_mp

    def cria_check_rec1(self):
        self.box_checklist = toga.Box(style=Pack(direction=COLUMN))

        self.lista_box_check = []
        self.lista_lb_sel = []

        opcoes = []
        opcoes_selection = []

        resultado_situacao = self.bc_ander.consultar('tab_cad_situacao')
        if resultado_situacao:
            for situacao in resultado_situacao:
                id_sit = situacao['objectId']
                nome_sit = situacao['NOME_SITUACAO']

                dadus = (id_sit, nome_sit)
                opcoes.append(dadus)

        for item_opcao in opcoes:
            objectid, descricao = item_opcao
            opcoes_selection.append(descricao)

        resultado_mp = self.bc_ander.consultar('tab_mp_checklist')
        if resultado_mp:
            for indices in resultado_mp:
                nome_param = indices['NOME_PARAMETRO']

                self.box_check = toga.Box(style=Pack(direction=ROW, padding_top=15, padding_left=8))
                self.label_check = toga.Label(f"{nome_param}", style=Pack(flex=5))
                self.selection_check = toga.Selection(items=opcoes_selection,
                                                      on_select=partial(self.altera_cor_check,
                                                                        widget_id=len(self.lista_box_check)),
                                                      style=Pack(padding_right=5, flex=4))
                self.box_check.add(self.label_check)
                self.box_check.add(self.selection_check)

                self.box_checklist.add(self.box_check)
                self.lista_box_check.append(self.box_check)
                dadus = (self.label_check, self.selection_check)
                self.lista_lb_sel.append(dadus)

        return self.box_checklist

    def verifica_valores_lancados(self):
        for label, selection in self.lista_lb_sel:
            valor_label = label.text

            id_param = None
            valor_lancado = None
            resultado_mp = self.bc_ander.consultar('tab_mp_checklist')
            if resultado_mp:
                for indices in resultado_mp:
                    id_p = indices['ID_PARAMETRO']
                    nome_p = indices['NOME_PARAMETRO']
                    id_s = indices['ID_SITUACAO']

                    if nome_p == valor_label:
                        id_param = id_p
                        valor_lancado = id_s
                        break

            if id_param:
                resultado_situacao = self.bc_ander.consultar('tab_cad_situacao')
                if resultado_situacao:
                    for situacao in resultado_situacao:
                        id_sit = situacao['objectId']
                        nome_sit = situacao['NOME_SITUACAO']

                        if id_sit == valor_lancado:
                            selection.value = nome_sit
                            self.altera_cor_check(selection, self.lista_lb_sel.index((label, selection)))
                            break
            else:
                selection.value = "NENHUM"
                self.altera_cor_check(selection, self.lista_lb_sel.index((label, selection)))

    def altera_cor_check(self, widget, widget_id):
        selected_option = widget.value

        if selected_option == 'REGULAR':
            if 0 <= widget_id < len(self.lista_box_check):
                box_check = self.lista_box_check[widget_id]
                box_check.style.update(background_color=cor_verde)

        elif selected_option == 'IRREGULAR':
            if 0 <= widget_id < len(self.lista_box_check):
                box_check = self.lista_box_check[widget_id]
                box_check.style.update(background_color=cor_amarelo)

        elif selected_option == 'TROCA EFETUADA':
            if 0 <= widget_id < len(self.lista_box_check):
                box_check = self.lista_box_check[widget_id]
                box_check.style.update(background_color=cor_laranja)

        elif selected_option == 'NENHUM':
            if 0 <= widget_id < len(self.lista_box_check):
                box_check = self.lista_box_check[widget_id]
                box_check.style.update(background_color=cor_transparente)

    def cria_obs_rec1(self):
        self.box_obs = toga.Box(style=Pack(padding=20))

        txt_check = ''

        resultado_mp = self.bc_ander.consultar('tab_mp_obs')
        if resultado_mp:
            for indices in resultado_mp:
                id_equip = indices['ID_MEDICAO']

                if id_equip == f"{self.id_medicao_check}":
                    texto_obs = indices['OBSERVACAO']

                    txt_check = texto_obs

        self.textinput_obs = toga.MultilineTextInput(value=txt_check, placeholder='Observação', style=Pack(flex=1))

        self.textinput_obs.style.update(height=100)
        self.textinput_obs.style.update(width=self.box_obs.style.width)

        self.box_obs.add(self.textinput_obs)

        return self.box_obs

    def cria_salvar_rec1(self):
        self.box_btn_salvar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_salvar = toga.Button('Salvar Etapa 1',
                                      on_press=self.salvar_rec1,
                                      style=Pack(padding_bottom=5))
        self.box_btn_salvar.add(self.btn_salvar)

        return self.box_btn_salvar

    def cria_btn_imagem(self):
        box_btn = toga.Box(style=Pack(direction=COLUMN, padding=10))

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        nome_maquina = dados_manut[0]['nome_maquina']
        if nome_maquina == "EXTRUSORA 3 CAMADAS":
            btn_tela1 = toga.Button('CONEXÃO CONVERSORES', on_press=self.mostrar_tela_imagem1,
                                    style=Pack(padding_bottom=5))
            box_btn.add(btn_tela1)

            btn_tela2 = toga.Button('CONVERSOR EXT. INTERNA/EXTERNA', on_press=self.mostrar_tela_imagem2,
                                    style=Pack(padding_bottom=5))
            box_btn.add(btn_tela2)

            btn_tela3 = toga.Button('CONVERSOR EXT. MEIO', on_press=self.mostrar_tela_imagem3,
                                    style=Pack(padding_bottom=5))
            box_btn.add(btn_tela3)

            btn_tela4 = toga.Button('CONEXÃO PARAFUSO CONVERSORES', on_press=self.mostrar_tela_imagem4,
                                    style=Pack(padding_bottom=5))
            box_btn.add(btn_tela4)

        return box_btn

    def cria_maq_rec1(self):
        self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                       on_press=self.mostrar_tela_maq_rec,
                                                       style=Pack(padding_bottom=5))
        self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

        return self.box_btn_check_recuperadora

    def cria_box1_rec1(self):
        self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        titulo = self.cria_titulo_rec1()
        mp = self.cria_num_mp_maq_rec1()
        checklist = self.cria_check_rec1()
        obs = self.cria_obs_rec1()
        btn_salvar = self.cria_salvar_rec1()
        btn_imagem = self.cria_btn_imagem()
        btn_maq_rec = self.cria_maq_rec1()

        self.box_semifinal1.add(titulo, mp, checklist, obs, btn_salvar, btn_imagem, btn_maq_rec)

        self.verifica_valores_lancados()

        return self.box_semifinal1

    def startup(self):
        self.main_window.content = self.scroll_container

    def mostrar_tela_maq_rec(self, widget):
        banco = self.bc_ander

        tela = TelaMaquina(self.main_window, banco)
        tela.startup()

    def mostrar_tela_imagem1(self, widget):
        banco = self.bc_ander

        tela = TelaImagem1(self.main_window, banco)
        tela.startup()

    def mostrar_tela_imagem2(self, widget):
        banco = self.bc_ander

        tela = TelaImagem2(self.main_window, banco)
        tela.startup()

    def mostrar_tela_imagem3(self, widget):
        banco = self.bc_ander

        tela = TelaImagem3(self.main_window, banco)
        tela.startup()

    def mostrar_tela_imagem4(self, widget):
        banco = self.bc_ander

        tela = TelaImagem4(self.main_window, banco)
        tela.startup()

    def salva_check_rec1(self):
        lista_json_check = []

        for box_check in self.lista_box_check:
            label_parametro_atual = box_check.children[0].text
            selection_situacao_atual = box_check.children[1].value

            resultado_mp = self.bc_ander.consultar('tab_mp_checklist')
            for indices in resultado_mp:
                id_check = indices['objectId']
                nome_param_banco = indices['NOME_PARAMETRO']
                nome_situa_banco = indices['NOME_SITUACAO']

                if nome_param_banco == label_parametro_atual:
                    if nome_situa_banco != selection_situacao_atual:
                        busca_mp = self.bc_ander.consultar_cond('tab_cad_situacao', 'NOME_SITUACAO',
                                                                selection_situacao_atual)
                        id_situacao_atual = busca_mp[0]['objectId']

                        print("PUT", id_check, nome_param_banco, id_situacao_atual, selection_situacao_atual)

                        objeto = {"method": "PUT", "path": f"/classes/mp_checklist/{id_check}",
                                  "body": {"ID_SITUACAO": {"__type": "Pointer",
                                                           "className": "cad_situacao",
                                                           "objectId": f"{id_situacao_atual}"}}}
                        lista_json_check.append(objeto)

                        pra_atualizar = {"ID_SITUACAO": id_situacao_atual, "NOME_SITUACAO": selection_situacao_atual}
                        self.bc_ander.atualizar_por_campo('tab_mp_checklist', 'objectId', id_check,
                                                          pra_atualizar)

                        pra_atualizar = {"STATUS": "INICIADA"}

                        objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                                  "body": pra_atualizar}
                        lista_json_check.append(objeto)

                        self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                          pra_atualizar)

                        break

        return lista_json_check

    def salva_obs_rec1(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_check)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_rec1(self, widget):
        final = 0

        lista_json_check = self.salva_check_rec1()
        if lista_json_check:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_check)

        lista_json_obs = self.salva_obs_rec1()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_rec1_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_rec1_atualizada(self, widget):
        banco = self.bc_ander

        self.tela_recupera = TelaMaquina(self.main_window, banco)
        self.tela_recupera.startup()


class TelaCarvaoMotor:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.id_medicao_carvao = 'j5rPCZ8Dbs'

        self.lista_cv_atual = []

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))

        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        box1 = self.cria_box1_rec2()
        box2 = self.cria_box2_rec2()

        self.box_final.add(box1, box2)

        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo_rec2(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Medição Carvões', style=Pack(font_size=24, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.width, self.btn_box, self.height)

        return self.box_dois

    def cria_num_mp_maq_rec2(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        num_mp = dados_manut[0]['NUM_MP']

        self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.label_mp_extraido = toga.Label(f'MP {num_mp}', style=Pack(font_size=20, padding=5, flex=1))
        self.box_mp.add(self.label_mp_extraido)
        return self.box_mp

    def cria_informe1_rec2(self):
        self.box_informe = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Carvão Motor | Máximo 40mm | Mínimo 20mm |',
                                 style=Pack(font_size=15, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_informe.add(self.name_box)
        self.box_informe.add(self.width, self.btn_box, self.height)

        return self.box_informe

    def cria_informe2_rec2(self):
        self.button = toga.Label('Taco | Máximo 15mm | Mínimo 10mm |',
                                 style=Pack(font_size=15, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_informe.add(self.name_box)
        self.box_informe.add(self.width, self.btn_box, self.height)

        return self.box_informe

    def totalzao(self):
        motores = []
        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_carvao')
        if resultado_mp:
            for dados in resultado_mp:
                motor = dados['MOTOR']
                if motor not in motores:
                    motores.append(motor)

        box_dados = toga.Box(style=Pack(direction=COLUMN, padding=1, padding_left=8))

        if motores:
            for i in motores:
                box_dados1 = self.cria_titulo2_rec2(i)
                box_dados2 = self.cria_cabecalho_rec2()
                box_dados3 = self.cria_dados_motor_rec2(i)
                box_dados.add(box_dados1, box_dados2, box_dados3)

        return box_dados

    def cria_titulo2_rec2(self, motor):
        box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        name_box = toga.Box(style=Pack(direction=ROW))

        button = toga.Label(f'Motor {motor}', style=Pack(font_size=20, font_weight='bold'))

        width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        btn_box = toga.Box(style=Pack(direction=ROW))
        btn_box.add(button)

        box_dois.add(name_box)
        box_dois.add(width, btn_box, height)

        return box_dois

    def cria_cabecalho_rec2(self):
        box_cabecalho = toga.Box(style=Pack(direction=ROW, padding=1))
        label_cab1 = toga.Label(' ', style=Pack(text_align='center', padding=1, flex=1))
        label_cab2 = toga.Label('1', style=Pack(text_align='center', padding=1, flex=1))
        label_cab3 = toga.Label('2', style=Pack(text_align='center', padding=1, flex=1))
        label_cab4 = toga.Label('3', style=Pack(text_align='center', padding=1, flex=1))
        label_cab5 = toga.Label('4', style=Pack(text_align='center', padding=1, flex=1))
        label_cab6 = toga.Label('5', style=Pack(text_align='center', padding=1, flex=1))
        label_cab7 = toga.Label('Troca', style=Pack(text_align='center', padding=1, flex=1))
        box_cabecalho.add(label_cab1, label_cab2, label_cab3,
                          label_cab4, label_cab5, label_cab6,
                          label_cab7)
        return box_cabecalho

    def cria_dados_motor_rec2(self, motor):
        pad = 2
        onde_entrou = []

        box_dados = toga.Box(style=Pack(direction=COLUMN, padding=1, padding_left=8))
        box_dados1 = toga.Box(style=Pack(direction=ROW, padding=1))
        box_dados2 = toga.Box(style=Pack(direction=ROW, padding=1))
        box_dados3 = toga.Box(style=Pack(direction=ROW, padding=1))
        box_dados4 = toga.Box(style=Pack(direction=ROW, padding=1))
        box_dados5 = toga.Box(style=Pack(direction=ROW, padding=1))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_carvao')
        if resultado_mp:
            for dados in resultado_mp:
                motors = dados['MOTOR']
                id_carv = dados['objectId']
                letra = dados['ORDEM_CARVAO']
                seq_1 = dados['SEQ_1']
                seq_2 = dados['SEQ_2']
                seq_3 = dados['SEQ_3']
                seq_4 = dados['SEQ_4']
                seq_5 = dados['SEQ_5']
                troca = dados['TROCA']

                if motors == motor:
                    if letra == 'A':
                        onde_entrou.append('A')

                        label_1dado1 = toga.Label('A', style=Pack(text_align='center', padding=1, flex=1 / 8))
                        textinput_1dado1 = toga.TextInput(value=seq_1, style=Pack(padding=pad, flex=1 / 7))
                        textinput_1dado2 = toga.TextInput(value=seq_2, style=Pack(padding=pad, flex=1 / 7))
                        textinput_1dado3 = toga.TextInput(value=seq_3, style=Pack(padding=pad, flex=1 / 7))
                        textinput_1dado4 = toga.TextInput(value=seq_4, style=Pack(padding=pad, flex=1 / 7))
                        textinput_1dado5 = toga.TextInput(value=seq_5, style=Pack(padding=pad, flex=1 / 7))
                        textinput_1dado6 = toga.TextInput(value=troca, style=Pack(padding=pad, flex=1 / 7))
                        box_dados1.add(label_1dado1, textinput_1dado1, textinput_1dado2,
                                       textinput_1dado3, textinput_1dado4, textinput_1dado5,
                                       textinput_1dado6)
                        dados = (id_carv, motors, label_1dado1, textinput_1dado1, textinput_1dado2,
                                 textinput_1dado3, textinput_1dado4, textinput_1dado5,
                                 textinput_1dado6)
                        self.lista_cv_atual.append(dados)

                    elif letra == 'B':
                        onde_entrou.append('B')

                        label_2dado1 = toga.Label('B', style=Pack(text_align='center', padding=1,
                                                                  flex=1 / 8))
                        textinput_2dado1 = toga.TextInput(value=seq_1, style=Pack(padding=pad, flex=1 / 7))
                        textinput_2dado2 = toga.TextInput(value=seq_2, style=Pack(padding=pad, flex=1 / 7))
                        textinput_2dado3 = toga.TextInput(value=seq_3, style=Pack(padding=pad, flex=1 / 7))
                        textinput_2dado4 = toga.TextInput(value=seq_4, style=Pack(padding=pad, flex=1 / 7))
                        textinput_2dado5 = toga.TextInput(value=seq_5, style=Pack(padding=pad, flex=1 / 7))
                        textinput_2dado6 = toga.TextInput(value=troca, style=Pack(padding=pad, flex=1 / 7))
                        box_dados2.add(label_2dado1, textinput_2dado1, textinput_2dado2,
                                       textinput_2dado3, textinput_2dado4, textinput_2dado5,
                                       textinput_2dado6)
                        dados = (id_carv, motors, label_2dado1, textinput_2dado1, textinput_2dado2,
                                 textinput_2dado3, textinput_2dado4, textinput_2dado5,
                                 textinput_2dado6)
                        self.lista_cv_atual.append(dados)

                    elif letra == 'C':
                        onde_entrou.append('C')

                        label_3dado1 = toga.Label('C', style=Pack(text_align='center', padding=1,
                                                                  flex=1 / 8))
                        textinput_3dado1 = toga.TextInput(value=seq_1, style=Pack(padding=pad, flex=1 / 7))
                        textinput_3dado2 = toga.TextInput(value=seq_2, style=Pack(padding=pad, flex=1 / 7))
                        textinput_3dado3 = toga.TextInput(value=seq_3, style=Pack(padding=pad, flex=1 / 7))
                        textinput_3dado4 = toga.TextInput(value=seq_4, style=Pack(padding=pad, flex=1 / 7))
                        textinput_3dado5 = toga.TextInput(value=seq_5, style=Pack(padding=pad, flex=1 / 7))
                        textinput_3dado6 = toga.TextInput(value=troca, style=Pack(padding=pad, flex=1 / 7))
                        box_dados3.add(label_3dado1, textinput_3dado1, textinput_3dado2,
                                       textinput_3dado3, textinput_3dado4, textinput_3dado5,
                                       textinput_3dado6)
                        dados = (id_carv, motors, label_3dado1, textinput_3dado1, textinput_3dado2,
                                 textinput_3dado3, textinput_3dado4, textinput_3dado5,
                                 textinput_3dado6)
                        self.lista_cv_atual.append(dados)

                    elif letra == 'D':
                        onde_entrou.append('D')

                        label_4dado1 = toga.Label('D', style=Pack(text_align='center', padding=1,
                                                                  flex=1 / 8))
                        textinput_4dado1 = toga.TextInput(value=seq_1, style=Pack(padding=pad, flex=1 / 7))
                        textinput_4dado2 = toga.TextInput(value=seq_2, style=Pack(padding=pad, flex=1 / 7))
                        textinput_4dado3 = toga.TextInput(value=seq_3, style=Pack(padding=pad, flex=1 / 7))
                        textinput_4dado4 = toga.TextInput(value=seq_4, style=Pack(padding=pad, flex=1 / 7))
                        textinput_4dado5 = toga.TextInput(value=seq_5, style=Pack(padding=pad, flex=1 / 7))
                        textinput_4dado6 = toga.TextInput(value=troca, style=Pack(padding=pad, flex=1 / 7))
                        box_dados4.add(label_4dado1, textinput_4dado1, textinput_4dado2,
                                       textinput_4dado3, textinput_4dado4, textinput_4dado5,
                                       textinput_4dado6)
                        dados = (id_carv, motors, label_4dado1, textinput_4dado1, textinput_4dado2,
                                 textinput_4dado3, textinput_4dado4, textinput_4dado5,
                                 textinput_4dado6)
                        self.lista_cv_atual.append(dados)

                    elif letra == 'TACO':
                        onde_entrou.append('TACO')

                        label_5dado1 = toga.Label('TACO', style=Pack(text_align='center', padding=1,
                                                                     flex=1 / 8))
                        textinput_5dado1 = toga.TextInput(value=seq_1, style=Pack(padding=pad, flex=1 / 7))
                        textinput_5dado2 = toga.TextInput(value=seq_2, style=Pack(padding=pad, flex=1 / 7))
                        textinput_5dado3 = toga.TextInput(value=seq_3, style=Pack(padding=pad, flex=1 / 7))
                        textinput_5dado4 = toga.TextInput(value=seq_4, style=Pack(padding=pad, flex=1 / 7))
                        textinput_5dado5 = toga.TextInput(value=seq_5, style=Pack(padding=pad, flex=1 / 7))
                        textinput_5dado6 = toga.TextInput(value=troca, style=Pack(padding=pad, flex=1 / 7))
                        box_dados5.add(label_5dado1, textinput_5dado1, textinput_5dado2,
                                       textinput_5dado3, textinput_5dado4, textinput_5dado5,
                                       textinput_5dado6)
                        dados = (id_carv, motors, label_5dado1, textinput_5dado1, textinput_5dado2,
                                 textinput_5dado3, textinput_5dado4, textinput_5dado5,
                                 textinput_5dado6)
                        self.lista_cv_atual.append(dados)

        box_dados.add(box_dados1, box_dados2, box_dados3, box_dados4,
                      box_dados5)
        return box_dados

    def cria_obs_rec2(self):
        self.box_obs = toga.Box(style=Pack(padding=20))

        txt_check = ''

        resultado_mp = self.bc_ander.consultar('tab_mp_obs')
        if resultado_mp:
            for indices in resultado_mp:
                id_equip = indices['ID_MEDICAO']

                if id_equip == f"{self.id_medicao_carvao}":
                    texto_obs = indices['OBSERVACAO']

                    txt_check = texto_obs

        self.textinput_obs = toga.MultilineTextInput(value=txt_check, placeholder='Observação',
                                                     style=Pack(flex=1))
        self.textinput_obs.style.update(height=100)
        self.textinput_obs.style.update(width=self.box_obs.style.width)

        self.box_obs.add(self.textinput_obs)

        return self.box_obs

    def cria_imagem_rec2(self):
        self.box_imagem = toga.Box(style=Pack(padding=1, flex=1))

        self.image = toga.Image("resources/carvao.png")
        self.imageview = toga.ImageView(self.image, style=Pack(flex=1))

        self.box_imagem.add(self.imageview)

        return self.box_imagem

    def cria_salvar_rec2(self):
        self.box_btn_salvar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_salvar = toga.Button('Salvar Etapa 2',
                                      on_press=self.salvar_rec2,
                                      style=Pack(padding_bottom=5))
        self.box_btn_salvar.add(self.btn_salvar)

        return self.box_btn_salvar

    def cria_maq_rec2(self):
        self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                       on_press=self.mostrar_tela_maq_rec,
                                                       style=Pack(padding_bottom=5))
        self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

        return self.box_btn_check_recuperadora

    def cria_box1_rec2(self):
        self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        titulo = self.cria_titulo_rec2()
        mp = self.cria_num_mp_maq_rec2()
        informe1 = self.cria_informe1_rec2()
        informe2 = self.cria_informe2_rec2()
        dados_motor = self.totalzao()
        obs = self.cria_obs_rec2()
        salvar = self.cria_salvar_rec2()
        maq_rec = self.cria_maq_rec2()

        self.box_semifinal1.add(titulo, mp, informe1, informe2, dados_motor, obs, salvar, maq_rec)

        return self.box_semifinal1

    def cria_box2_rec2(self):
        self.box_semifinal2 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=2))
        imagem = self.cria_imagem_rec2()
        self.box_semifinal2.add(imagem)

        return self.box_semifinal2

    def startup(self):
        self.main_window.content = self.scroll_container

    def mostrar_tela_maq_rec(self, widget):
        banco = self.bc_ander

        tela = TelaMaquina(self.main_window, banco)
        tela.startup()

    def salva_carvao_rec2(self):
        def v_num(sequence):
            pattern = r'^$|^\d+(,\d+)*$'
            return re.match(pattern, sequence) is not None

        lista_json_carvao = []

        pode_ir = 0

        for dados in self.lista_cv_atual:
            id_carv, motor, letra, seq_1, seq_2, seq_3, seq_4, seq_5, troca = dados
            seq_1_t = seq_1.value
            seq_2_t = seq_2.value
            seq_3_t = seq_3.value
            seq_4_t = seq_4.value
            seq_5_t = seq_5.value

            if v_num(seq_1_t) and v_num(seq_2_t) and v_num(seq_3_t) and v_num(seq_4_t) and v_num(seq_5_t):
                pass
            else:
                pode_ir = pode_ir + 1

        if not pode_ir:
            for dados in self.lista_cv_atual:
                id_carv, motor, letra, seq_1, seq_2, seq_3, seq_4, seq_5, troca = dados
                letra_f = letra.text
                seq_1_f = seq_1.value
                seq_2_f = seq_2.value
                seq_3_f = seq_3.value
                seq_4_f = seq_4.value
                seq_5_f = seq_5.value
                troca_f = troca.value
                troca_maiusc = troca_f.upper()
                tutu = (id_carv, motor, letra_f, seq_1_f, seq_2_f, seq_3_f, seq_4_f, seq_5_f, troca_f)

                resultado_mp = self.bc_ander.consultar('tab_mp_medicao_carvao')
                lista_carvoes = []

                for indices in resultado_mp:
                    id_carv_b1 = indices['objectId']
                    motores = indices['MOTOR']
                    letra_b1 = indices['ORDEM_CARVAO']
                    seq_1_b1 = indices['SEQ_1']
                    seq_2_b1 = indices['SEQ_2']
                    seq_3_b1 = indices['SEQ_3']
                    seq_4_b1 = indices['SEQ_4']
                    seq_5_b1 = indices['SEQ_5']
                    troca_b1 = indices['TROCA']

                    cucu = (id_carv_b1, motores, letra_b1, seq_1_b1, seq_2_b1, seq_3_b1, seq_4_b1, seq_5_b1, troca_b1)
                    lista_carvoes.append(cucu)

                for grup_carvao in lista_carvoes:
                    id_carv_b, motor_b, letra_b, seq_1_b, seq_2_b, seq_3_b, seq_4_b, seq_5_b, troca_b = grup_carvao
                    if id_carv_b == id_carv:
                        if grup_carvao != tutu:
                            print("PUT")
                            pra_atualizar = {"SEQ_1": f"{seq_1_f}",
                                             "SEQ_2": f"{seq_2_f}",
                                             "SEQ_3": f"{seq_3_f}",
                                             "SEQ_4": f"{seq_4_f}",
                                             "SEQ_5": f"{seq_5_f}",
                                             "TROCA": f"{troca_maiusc}"}

                            objeto = {"method": "PUT", "path": f"/classes/mp_medicao_carvao/{id_carv_b}",
                                      "body": pra_atualizar}
                            lista_json_carvao.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_mp_medicao_carvao', 'objectId', id_carv_b,
                                                              pra_atualizar)

                            pra_atualizar = {"STATUS": "INICIADA"}

                            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                                      "body": pra_atualizar}
                            lista_json_carvao.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                              pra_atualizar)

        else:
            objeto = "NÃO VAI"
            lista_json_carvao.append(objeto)

        return lista_json_carvao

    def salva_obs_rec2(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_carvao)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_rec2(self, widget):
        final = 0

        lista_json_carvao = self.salva_carvao_rec2()
        if not lista_json_carvao:
            pass
        elif lista_json_carvao[0] == "NÃO VAI":
            final = final + 100
        elif lista_json_carvao:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_carvao)

        lista_json_obs = self.salva_obs_rec2()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if 0 < final < 99:
            self.mostrar_tela_maq_rec(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        elif final > 99:
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER TEXTOS\nNOS CAMPOS DE MEDIÇÕES')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')


class TelaCapacitor:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.id_medicao_capaci = 'Y9Q2EfArej'

        self.lista_cap_atual = []

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))

        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        box1 = self.cria_box1_rec3()

        self.box_final.add(box1)

        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo_rec3(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Medição Capacitores', style=Pack(font_size=24, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.width, self.btn_box, self.height)

        return self.box_dois

    def cria_num_mp_maq_rec3(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        num_mp = dados_manut[0]['NUM_MP']

        self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.label_mp_extraido = toga.Label(f'MP {num_mp}', style=Pack(font_size=20, padding=5, flex=1))
        self.box_mp.add(self.label_mp_extraido)
        return self.box_mp

    def cria_cabecalho_rec3(self):
        self.box_cabecalho = toga.Box(style=Pack(direction=ROW, padding=1))
        self.label_cab1 = toga.Label('Filtros', style=Pack(padding=1, flex=1))
        self.label_cab2 = toga.Label('Fase A', style=Pack(padding=1, flex=1))
        self.label_cab3 = toga.Label('Fase B', style=Pack(padding=1, flex=1))
        self.label_cab4 = toga.Label('Fase C', style=Pack(padding=1, flex=1))
        self.label_cab5 = toga.Label('Temperatura', style=Pack(padding=1, flex=1))
        self.box_cabecalho.add(self.label_cab1, self.label_cab2, self.label_cab3,
                               self.label_cab4, self.label_cab5)
        return self.box_cabecalho

    def totalzao(self):
        total_filtros = []
        box_dados = toga.Box(style=Pack(direction=COLUMN, padding=1, padding_left=8))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_capacitor')
        if resultado_mp:
            for indices in resultado_mp:
                filtro_cap = indices['FILTRO']

                if filtro_cap not in total_filtros:
                    dados = (int(filtro_cap), filtro_cap)
                    total_filtros.append(dados)

        lista_classificada = sorted(total_filtros)

        if lista_classificada:
            for i, y in lista_classificada:
                box_filtro = self.cria_dados_capac_rec3(y)
                box_dados.add(box_filtro)

        return box_dados

    def cria_dados_capac_rec3(self, num_fil):
        box = toga.Box(style=Pack(direction=ROW, padding=1))

        resultado_mp = self.bc_ander.consultar_cond('tab_mp_medicao_capacitor', 'FILTRO', num_fil)
        id_cap = resultado_mp[0]['objectId']
        fase_a = resultado_mp[0]['FASE_A']
        fase_b = resultado_mp[0]['FASE_B']
        fase_c = resultado_mp[0]['FASE_C']
        temp = resultado_mp[0]['TEMPERATURA']

        label_1dado1 = toga.Label(num_fil, style=Pack(padding=1, flex=1))
        textinput_1dado1 = toga.TextInput(value=fase_a, style=Pack(padding=2, flex=1))
        textinput_1dado2 = toga.TextInput(value=fase_b, style=Pack(padding=2, flex=1))
        textinput_1dado3 = toga.TextInput(value=fase_c, style=Pack(padding=2, flex=1))
        textinput_1dado4 = toga.TextInput(value=temp, style=Pack(padding=2, flex=1))
        box.add(label_1dado1, textinput_1dado1, textinput_1dado2,
                textinput_1dado3, textinput_1dado4)
        dados = (id_cap, label_1dado1, textinput_1dado1, textinput_1dado2,
                 textinput_1dado3, textinput_1dado4)
        self.lista_cap_atual.append(dados)

        return box

    def cria_obs_rec3(self):
        self.box_obs = toga.Box(style=Pack(padding=20))

        txt_check = ''

        resultado_mp = self.bc_ander.consultar('tab_mp_obs')
        if resultado_mp:
            for indices in resultado_mp:
                id_equip = indices['ID_MEDICAO']

                if id_equip == f"{self.id_medicao_capaci}":
                    texto_obs = indices['OBSERVACAO']

                    txt_check = texto_obs

        self.textinput_obs = toga.MultilineTextInput(value=txt_check,
                                                     placeholder='Observação',
                                                     style=Pack(flex=1))
        self.textinput_obs.style.update(height=100)
        self.textinput_obs.style.update(width=self.box_obs.style.width)

        self.box_obs.add(self.textinput_obs)

        return self.box_obs

    def cria_salvar_rec3(self):
        self.box_btn_salvar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_salvar = toga.Button('Salvar Etapa 3',
                                      on_press=self.salvar_rec3,
                                      style=Pack(padding_bottom=5))
        self.box_btn_salvar.add(self.btn_salvar)

        return self.box_btn_salvar

    def cria_maq_rec3(self):
        self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                       on_press=self.mostrar_tela_maq_rec,
                                                       style=Pack(padding_bottom=5))
        self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

        return self.box_btn_check_recuperadora

    def cria_box1_rec3(self):
        self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        titulo = self.cria_titulo_rec3()
        mp = self.cria_num_mp_maq_rec3()
        cabecalho = self.cria_cabecalho_rec3()
        dados_capac = self.totalzao()
        obs = self.cria_obs_rec3()
        salvar = self.cria_salvar_rec3()
        maq_rec = self.cria_maq_rec3()

        self.box_semifinal1.add(titulo, mp, cabecalho,
                                dados_capac, obs, salvar, maq_rec)

        return self.box_semifinal1

    def startup(self):
        self.main_window.content = self.scroll_container

    def mostrar_tela_maq_rec(self, widget):
        banco = self.bc_ander

        tela = TelaMaquina(self.main_window, banco)
        tela.startup()

    def salva_capacitores_rec3(self):
        def v_num(sequence):
            pattern = r'^$|^\d+(,\d+)*$'
            return re.match(pattern, sequence) is not None

        lista_json_capacitores = []

        pode_ir = 0

        for dados in self.lista_cap_atual:
            id_cap, filtro, fase_a, fase_b, fase_c, temp = dados
            fase_a_t = fase_a.value
            fase_b_t = fase_b.value
            fase_c_t = fase_c.value
            temp_t = temp.value

            if v_num(fase_a_t) and v_num(fase_b_t) and v_num(fase_c_t) and v_num(temp_t):
                pass
            else:
                pode_ir = pode_ir + 1

        if not pode_ir:
            for dados in self.lista_cap_atual:
                id_cap, filtro, fase_a, fase_b, fase_c, temp = dados
                filtro_f = filtro.text
                fase_a_f = fase_a.value
                fase_b_f = fase_b.value
                fase_c_f = fase_c.value
                temp_f = temp.value
                tutu = (id_cap, filtro_f, fase_a_f, fase_b_f, fase_c_f, temp_f)

                lista_capac = []
                resultado_mp = self.bc_ander.consultar('tab_mp_medicao_capacitor')
                if resultado_mp:
                    for indices in resultado_mp:
                        id_cap_b1 = indices['objectId']
                        filtro_cap_b1 = indices['FILTRO']
                        fase_a_b1 = indices['FASE_A']
                        fase_b_b1 = indices['FASE_B']
                        fase_c_b1 = indices['FASE_C']
                        temp_b1 = indices['TEMPERATURA']

                        cucu = (id_cap_b1, filtro_cap_b1, fase_a_b1, fase_b_b1, fase_c_b1, temp_b1)
                        lista_capac.append(cucu)

                for grup_capa in lista_capac:
                    id_cap_b, filtro_cap_b, fase_a_b, fase_b_b, fase_c_b, temp_b = grup_capa
                    if id_cap_b == id_cap:
                        if grup_capa != tutu:
                            print("PUT")

                            pra_atualizar = {'FASE_A': fase_a_f,
                                             'FASE_B': fase_b_f,
                                             'FASE_C': fase_c_f,
                                             'TEMPERATURA': temp_f}

                            objeto = {"method": "PUT", "path": f"/classes/mp_medicao_capacitor/{id_cap_b}",
                                      "body": pra_atualizar}
                            lista_json_capacitores.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_mp_medicao_capacitor', 'objectId', id_cap_b,
                                                              pra_atualizar)

                            pra_atualizar = {"STATUS": "INICIADA"}

                            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                                      "body": pra_atualizar}
                            lista_json_capacitores.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                              pra_atualizar)

        else:
            objeto = "NÃO VAI"
            lista_json_capacitores.append(objeto)

        return lista_json_capacitores

    def salva_obs_rec3(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_capaci)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_rec3(self, widget):
        final = 0

        lista_json_cap = self.salva_capacitores_rec3()
        if not lista_json_cap:
            pass
        elif lista_json_cap[0] == "NÃO VAI":
            final = final + 100
        elif lista_json_cap:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_cap)

        lista_json_obs = self.salva_obs_rec3()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if 0 < final < 99:
            self.mostrar_tela_maq_rec3_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        elif final > 99:
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER TEXTOS\nNOS CAMPOS DE MEDIÇÕES')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_rec3_atualizada(self, widget):
        banco = self.bc_ander

        self.tela_recupera = TelaMaquina(self.main_window, banco)
        self.tela_recupera.startup()


class TelaBarramento:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        self.id_mp = dados_manut[0]['objectId']

        self.id_medicao_barramento = 'cfAX6w6t2q'

        self.lista_cap_atual = []

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))

        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        box1 = self.cria_box1_rec3()

        self.box_final.add(box1)

        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_titulo_rec3(self):
        self.box_dois = toga.Box(style=Pack(direction=COLUMN, alignment="center", padding=5))
        self.name_box = toga.Box(style=Pack(direction=ROW))

        self.button = toga.Label('Medição Barramentos', style=Pack(font_size=24, font_weight='bold'))

        self.width = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))
        self.height = toga.Label(f'', style=Pack(font_size=5, font_weight='bold'))

        self.btn_box = toga.Box(style=Pack(direction=ROW))
        self.btn_box.add(self.button)

        self.box_dois.add(self.name_box)
        self.box_dois.add(self.width, self.btn_box, self.height)

        return self.box_dois

    def cria_num_mp_maq_rec3(self):
        dados_manut = self.bc_ander.consultar('tab_manutencao_preventiva')
        num_mp = dados_manut[0]['NUM_MP']

        self.box_mp = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.label_mp_extraido = toga.Label(f'MP {num_mp}', style=Pack(font_size=20, padding=5, flex=1))
        self.box_mp.add(self.label_mp_extraido)
        return self.box_mp

    def cria_cabecalho_rec3(self):
        self.box_cabecalho = toga.Box(style=Pack(direction=ROW, padding=1))
        self.label_cab2 = toga.Label('Fase AB', style=Pack(padding=1, flex=1))
        self.label_cab3 = toga.Label('Fase AC', style=Pack(padding=1, flex=1))
        self.label_cab4 = toga.Label('Fase BC', style=Pack(padding=1, flex=1))
        self.box_cabecalho.add(self.label_cab2, self.label_cab3, self.label_cab4)
        return self.box_cabecalho

    def totalzao(self):
        box = toga.Box(style=Pack(direction=ROW, padding=1))

        resultado_mp = self.bc_ander.consultar('tab_mp_medicao_barramento')
        id_cap = resultado_mp[0]['objectId']
        fase_ab = resultado_mp[0]['FASE_AB']
        fase_ac = resultado_mp[0]['FASE_AC']
        fase_bc = resultado_mp[0]['FASE_BC']

        textinput_1dado1 = toga.TextInput(value=fase_ab, style=Pack(padding=2, flex=1))
        textinput_1dado2 = toga.TextInput(value=fase_ac, style=Pack(padding=2, flex=1))
        textinput_1dado3 = toga.TextInput(value=fase_bc, style=Pack(padding=2, flex=1))
        box.add(textinput_1dado1, textinput_1dado2,
                textinput_1dado3)
        dados = (id_cap, textinput_1dado1, textinput_1dado2,
                 textinput_1dado3)
        self.lista_cap_atual.append(dados)

        return box

    def cria_obs_rec3(self):
        self.box_obs = toga.Box(style=Pack(padding=20))

        txt_check = ''

        resultado_mp = self.bc_ander.consultar('tab_mp_obs')
        if resultado_mp:
            for indices in resultado_mp:
                id_equip = indices['ID_MEDICAO']

                if id_equip == f"{self.id_medicao_barramento}":
                    texto_obs = indices['OBSERVACAO']

                    txt_check = texto_obs

        self.textinput_obs = toga.MultilineTextInput(value=txt_check,
                                                     placeholder='Observação',
                                                     style=Pack(flex=1))
        self.textinput_obs.style.update(height=100)
        self.textinput_obs.style.update(width=self.box_obs.style.width)

        self.box_obs.add(self.textinput_obs)

        return self.box_obs

    def cria_salvar_rec3(self):
        self.box_btn_salvar = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.btn_salvar = toga.Button('Salvar Medição Barramento',
                                      on_press=self.salvar_rec3,
                                      style=Pack(padding_bottom=5))
        self.box_btn_salvar.add(self.btn_salvar)

        return self.box_btn_salvar

    def cria_maq_rec3(self):
        self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                       on_press=self.mostrar_tela_maq_rec,
                                                       style=Pack(padding_bottom=5))
        self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

        return self.box_btn_check_recuperadora

    def cria_box1_rec3(self):
        self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

        titulo = self.cria_titulo_rec3()
        mp = self.cria_num_mp_maq_rec3()
        cabecalho = self.cria_cabecalho_rec3()
        dados_capac = self.totalzao()
        obs = self.cria_obs_rec3()
        salvar = self.cria_salvar_rec3()
        maq_rec = self.cria_maq_rec3()

        self.box_semifinal1.add(titulo, mp, cabecalho,
                                dados_capac, obs, salvar, maq_rec)

        return self.box_semifinal1

    def startup(self):
        self.main_window.content = self.scroll_container

    def mostrar_tela_maq_rec(self, widget):
        banco = self.bc_ander

        tela = TelaMaquina(self.main_window, banco)
        tela.startup()

    def salva_capacitores_rec3(self):
        def v_num(sequence):
            pattern = r'^$|^\d+(,\d+)*$'
            return re.match(pattern, sequence) is not None

        lista_json_capacitores = []

        pode_ir = 0

        for dados in self.lista_cap_atual:
            id_cap, fase_ab, fase_ac, fase_bc = dados
            fase_ab_t = fase_ab.value
            fase_ac_t = fase_ac.value
            fase_bc_t = fase_bc.value

            if v_num(fase_ab_t) and v_num(fase_ac_t) and v_num(fase_bc_t):
                pass
            else:
                pode_ir = pode_ir + 1

        if not pode_ir:
            for dados in self.lista_cap_atual:
                id_cap, fase_a, fase_b, fase_c = dados
                fase_a_f = fase_a.value
                fase_b_f = fase_b.value
                fase_c_f = fase_c.value
                tutu = (id_cap, fase_a_f, fase_b_f, fase_c_f)

                lista_capac = []
                resultado_mp = self.bc_ander.consultar('tab_mp_medicao_barramento')
                if resultado_mp:
                    for indices in resultado_mp:
                        id_cap_b1 = indices['objectId']
                        fase_a_b1 = indices['FASE_AB']
                        fase_b_b1 = indices['FASE_AC']
                        fase_c_b1 = indices['FASE_BC']

                        cucu = (id_cap_b1, fase_a_b1, fase_b_b1, fase_c_b1)
                        lista_capac.append(cucu)

                for grup_capa in lista_capac:
                    id_cap_b, fase_a_b, fase_b_b, fase_c_b = grup_capa
                    if id_cap_b == id_cap:
                        if grup_capa != tutu:
                            print("PUT")

                            pra_atualizar = {'FASE_AB': fase_a_f,
                                             'FASE_AC': fase_b_f,
                                             'FASE_BC': fase_c_f}

                            objeto = {"method": "PUT", "path": f"/classes/mp_medicao_barramento/{id_cap_b}",
                                      "body": pra_atualizar}
                            lista_json_capacitores.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_mp_medicao_barramento', 'objectId', id_cap_b,
                                                              pra_atualizar)

                            pra_atualizar = {"STATUS": "INICIADA"}

                            objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                                      "body": pra_atualizar}
                            lista_json_capacitores.append(objeto)

                            self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                              pra_atualizar)

        else:
            objeto = "NÃO VAI"
            lista_json_capacitores.append(objeto)

        return lista_json_capacitores

    def salva_obs_rec3(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_barramento)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_rec3(self, widget):
        final = 0

        lista_json_cap = self.salva_capacitores_rec3()
        if not lista_json_cap:
            pass
        elif lista_json_cap[0] == "NÃO VAI":
            final = final + 100
        elif lista_json_cap:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_cap)

        lista_json_obs = self.salva_obs_rec3()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if 0 < final < 99:
            self.mostrar_tela_maq_rec3_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        elif final > 99:
            self.main_window.info_dialog("Atenção!", f'NÃO PODE HAVER TEXTOS\nNOS CAMPOS DE MEDIÇÕES')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_rec3_atualizada(self, widget):
        banco = self.bc_ander

        self.tela_recupera = TelaMaquina(self.main_window, banco)
        self.tela_recupera.startup()


class TelaImagem1:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1()
        box2 = self.cria_imagem_1()
        self.box_final.add(box1, box2)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_voltar(self):
        try:
            self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

            self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                           on_press=self.mostrar_tela_maq_recserie,
                                                           style=Pack(padding_bottom=5))
            self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

            return self.box_btn_check_recuperadora

        except Exception as e:
            print(f'Houve um problema com a função "cria_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_imagem_1(self):
        box_imagem = toga.Box(style=Pack(padding=1, flex=1))

        image = toga.Image(f"resources/conversores.png")
        imageview = toga.ImageView(image, style=Pack(flex=1))

        box_imagem.add(imageview)

        return box_imagem

    def cria_box1(self):
        try:
            self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

            voltar = self.cria_voltar()

            self.box_semifinal1.add(voltar)

            return self.box_semifinal1

        except Exception as e:
            print(f'Houve um problema com a função "cria_box1".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def startup(self):
        try:
            self.main_window.content = self.scroll_container

        except Exception as e:
            print(f'Houve um problema com a função "startup".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def mostrar_tela_maq_recserie(self, widget):
        try:
            banco = self.bc_ander

            tela = TelaChecklist(self.main_window, banco)
            tela.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salva_obs_recserie(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_serie)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_recserie(self, widget):
        final = 0

        lista_json_obs = self.salva_obs_recserie()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_recserie_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_recserie_atualizada(self, widget):
        try:
            banco = self.bc_ander

            self.tela_recupera = TelaMaquina(self.main_window, banco)
            self.tela_recupera.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie_atualizada".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')


class TelaImagem2:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1()
        box2 = self.cria_imagem_1()
        self.box_final.add(box1, box2)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_voltar(self):
        try:
            self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

            self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                           on_press=self.mostrar_tela_maq_recserie,
                                                           style=Pack(padding_bottom=5))
            self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

            return self.box_btn_check_recuperadora

        except Exception as e:
            print(f'Houve um problema com a função "cria_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_imagem_1(self):
        box_imagem = toga.Box(style=Pack(padding=1, flex=1))

        image = toga.Image(f"resources/extrusora.png")
        imageview = toga.ImageView(image, style=Pack(flex=1))

        box_imagem.add(imageview)

        return box_imagem

    def cria_box1(self):
        try:
            self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

            voltar = self.cria_voltar()

            self.box_semifinal1.add(voltar)

            return self.box_semifinal1

        except Exception as e:
            print(f'Houve um problema com a função "cria_box1".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def startup(self):
        try:
            self.main_window.content = self.scroll_container

        except Exception as e:
            print(f'Houve um problema com a função "startup".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def mostrar_tela_maq_recserie(self, widget):
        try:
            banco = self.bc_ander

            tela = TelaChecklist(self.main_window, banco)
            tela.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salva_obs_recserie(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_serie)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_recserie(self, widget):
        final = 0

        lista_json_obs = self.salva_obs_recserie()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_recserie_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_recserie_atualizada(self, widget):
        try:
            banco = self.bc_ander

            self.tela_recupera = TelaMaquina(self.main_window, banco)
            self.tela_recupera.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie_atualizada".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')


class TelaImagem3:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1()
        box2 = self.cria_imagem_1()
        self.box_final.add(box1, box2)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_voltar(self):
        try:
            self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

            self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                           on_press=self.mostrar_tela_maq_recserie,
                                                           style=Pack(padding_bottom=5))
            self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

            return self.box_btn_check_recuperadora

        except Exception as e:
            print(f'Houve um problema com a função "cria_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_imagem_1(self):
        box_imagem = toga.Box(style=Pack(padding=1, flex=1))

        image = toga.Image(f"resources/meio.png")
        imageview = toga.ImageView(image, style=Pack(flex=1))

        box_imagem.add(imageview)

        return box_imagem

    def cria_box1(self):
        try:
            self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

            voltar = self.cria_voltar()

            self.box_semifinal1.add(voltar)

            return self.box_semifinal1

        except Exception as e:
            print(f'Houve um problema com a função "cria_box1".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def startup(self):
        try:
            self.main_window.content = self.scroll_container

        except Exception as e:
            print(f'Houve um problema com a função "startup".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def mostrar_tela_maq_recserie(self, widget):
        try:
            banco = self.bc_ander

            tela = TelaChecklist(self.main_window, banco)
            tela.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salva_obs_recserie(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_serie)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_recserie(self, widget):
        final = 0

        lista_json_obs = self.salva_obs_recserie()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_recserie_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_recserie_atualizada(self, widget):
        try:
            banco = self.bc_ander

            self.tela_recupera = TelaMaquina(self.main_window, banco)
            self.tela_recupera.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie_atualizada".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')


class TelaImagem4:
    def __init__(self, main_window, banco):
        self.bc_ander = banco
        self.conexao = ConexaoBack4App(self.bc_ander)

        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.box_final = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))
        box1 = self.cria_box1()
        box2 = self.cria_imagem_1()
        self.box_final.add(box1, box2)
        self.scroll_container.content = self.box_final

        self.main_window = main_window

    def cria_voltar(self):
        try:
            self.box_btn_check_recuperadora = toga.Box(style=Pack(direction=COLUMN, padding=10))

            self.btn_tela_check_recuperadora = toga.Button('Voltar',
                                                           on_press=self.mostrar_tela_maq_recserie,
                                                           style=Pack(padding_bottom=5))
            self.box_btn_check_recuperadora.add(self.btn_tela_check_recuperadora)

            return self.box_btn_check_recuperadora

        except Exception as e:
            print(f'Houve um problema com a função "cria_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def cria_imagem_1(self):
        box_imagem = toga.Box(style=Pack(padding=1, flex=1))

        image = toga.Image(f"resources/parafuso.png")
        imageview = toga.ImageView(image, style=Pack(flex=1))

        box_imagem.add(imageview)

        return box_imagem

    def cria_box1(self):
        try:
            self.box_semifinal1 = toga.Box(style=Pack(direction=COLUMN, padding=1, flex=1))

            voltar = self.cria_voltar()

            self.box_semifinal1.add(voltar)

            return self.box_semifinal1

        except Exception as e:
            print(f'Houve um problema com a função "cria_box1".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def startup(self):
        try:
            self.main_window.content = self.scroll_container

        except Exception as e:
            print(f'Houve um problema com a função "startup".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def mostrar_tela_maq_recserie(self, widget):
        try:
            banco = self.bc_ander

            tela = TelaChecklist(self.main_window, banco)
            tela.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salva_obs_recserie(self):
        try:
            lista_json_obs = []

            if self.textinput_obs.value:
                texto_editado = self.textinput_obs.value
                texto_editado = texto_editado.upper()
            else:
                texto_editado = ''

            busca_obs = self.bc_ander.consultar_cond('tab_mp_obs', 'ID_MEDICAO', self.id_medicao_serie)

            for cada_obs in busca_obs:
                id_obs = cada_obs['objectId']
                texto_obs = cada_obs['OBSERVACAO']

                if texto_editado != texto_obs:
                    print("PUT")
                    pra_atualizar = {"OBSERVACAO": texto_editado}

                    objeto = {"method": "PUT", "path": f"/classes/mp_observacao/{id_obs}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_mp_obs', 'objectId', id_obs, pra_atualizar)

                    pra_atualizar = {"STATUS": "INICIADA"}

                    objeto = {"method": "PUT", "path": f"/classes/manutencao_preventiva/{self.id_mp}",
                              "body": pra_atualizar}
                    lista_json_obs.append(objeto)

                    self.bc_ander.atualizar_por_campo('tab_manutencao_preventiva', 'objectId', self.id_mp,
                                                      pra_atualizar)

            return lista_json_obs

        except Exception as e:
            print(f'Houve um problema com a função "salva_obs_recserie".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')

    def salvar_recserie(self, widget):
        final = 0

        lista_json_obs = self.salva_obs_recserie()
        if lista_json_obs:
            final = final + 1
            self.conexao.salvar_no_banco(lista_json_obs)

        if final > 0:
            self.mostrar_tela_maq_recserie_atualizada(widget)
            self.main_window.info_dialog("Atenção!", f'DADOS SALVO COM SUCESSO!')
        else:
            self.main_window.info_dialog("Atenção!", f'ALGUM ITEM PRECISA SER\n ALTERADO PARA SALVAR!')

    def mostrar_tela_maq_recserie_atualizada(self, widget):
        try:
            banco = self.bc_ander

            self.tela_recupera = TelaMaquina(self.main_window, banco)
            self.tela_recupera.startup()

        except Exception as e:
            print(f'Houve um problema com a função "mostrar_tela_maq_recserie_atualizada".\n'
                  f'Comunique o desenvolvedor sobre o erro abaixo:\n'
                  f'{e}')


def main():
    return Login()


if __name__ == '__main__':
    main().main_loop()