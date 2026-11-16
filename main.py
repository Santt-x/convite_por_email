"""Envia o convite da ZÉ Empréstimos ou gera uma prévia sem acessar a internet."""

import argparse
import csv
import getpass
import json
import os
from pathlib import Path
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formataddr, formatdate, make_msgid


PASTA_PROJETO = Path(__file__).resolve().parent
ASSUNTO = "Convite de aniversário — ZÉ Empréstimos"
TEXTO_CONVITE = """Olá, {nome}!

Você é convidado para mais um aniversário da empresa ZÉ Empréstimos, onde
será servido um delicioso jantar no dia 11/12/2026, às 20h30, na própria empresa.

Por favor, marque uma das opções abaixo com um X e responda a este e-mail:

[ ] SIM, estarei presente.
[ ] NÃO conseguirei participar.

Esperamos por você!
ZÉ Empréstimos
"""


def email_valido(endereco):
    """Faz uma verificação básica; não confirma se a caixa de e-mail existe."""
    return bool(re.fullmatch(r"[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+", endereco))


def ler_clientes(caminho):
    """Valida a lista inteira antes de começar qualquer envio."""
    clientes = []
    emails_lidos = set()
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        primeira_linha = arquivo.readline()
        arquivo.seek(0)
        separador = ";" if ";" in primeira_linha else ","
        leitor = csv.DictReader(arquivo, delimiter=separador)
        if leitor.fieldnames != ["nome", "email"]:
            raise ValueError("O CSV deve começar com nome,email (ou nome;email).")
        for linha, registro in enumerate(leitor, start=2):
            nome = (registro.get("nome") or "").strip()
            endereco = (registro.get("email") or "").strip()
            if None in registro or not nome or "\n" in nome or "\r" in nome:
                raise ValueError(f"Nome ou quantidade de colunas inválidos na linha {linha}.")
            if not email_valido(endereco):
                raise ValueError(f"E-mail inválido na linha {linha}.")
            if endereco.casefold() in emails_lidos:
                raise ValueError(f"E-mail repetido na linha {linha}: {endereco}.")
            emails_lidos.add(endereco.casefold())
            clientes.append({"nome": nome, "email": endereco})
    if not clientes:
        raise ValueError("A lista de clientes está vazia.")
    return clientes


def montar_mensagem(cliente, remetente, nome_remetente="ZÉ Empréstimos"):
    mensagem = EmailMessage()
    mensagem["Subject"] = ASSUNTO
    mensagem["From"] = formataddr((nome_remetente, remetente))
    mensagem["To"] = cliente["email"]
    mensagem["Reply-To"] = remetente
    mensagem["Date"] = formatdate(localtime=True)
    mensagem["Message-ID"] = make_msgid()
    mensagem.set_content(TEXTO_CONVITE.format(nome=cliente["nome"]))
    return mensagem


def simular(clientes, pasta_saida):
    """Salva mensagens .eml que podem ser abertas em um aplicativo de e-mail."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    for numero, cliente in enumerate(clientes, start=1):
        mensagem = montar_mensagem(cliente, "convites@example.com")
        caminho = pasta_saida / f"convite_{numero:03d}.eml"
        caminho.write_bytes(mensagem.as_bytes(policy=SMTP))
        print(f"Prévia criada: {caminho.name} — {cliente['nome']} <{cliente['email']}>")
    print("\n" + TEXTO_CONVITE.format(nome=clientes[0]["nome"]))
    print(f"Simulação concluída. Nenhum e-mail enviado. Prévias em: {pasta_saida}")


def ler_configuracao(caminho):
    if not caminho.is_file():
        raise ValueError("Crie config.json a partir de config.exemplo.json antes de enviar.")
    with caminho.open(encoding="utf-8-sig") as arquivo:
        config = json.load(arquivo)
    if not isinstance(config, dict):
        raise ValueError("A configuração deve ser um objeto JSON.")
    for campo in ("servidor", "usuario", "remetente", "nome_remetente", "seguranca"):
        valor = config.get(campo)
        if not isinstance(valor, str) or not valor.strip() or "\n" in valor or "\r" in valor:
            raise ValueError(f"Preencha corretamente o campo {campo} em config.json.")
    if not email_valido(config["remetente"]):
        raise ValueError("O e-mail do remetente é inválido.")
    porta = config.get("porta")
    if type(porta) is not int or not 1 <= porta <= 65535:
        raise ValueError("A porta deve ser um número entre 1 e 65535.")
    if config["seguranca"] not in ("starttls", "ssl"):
        raise ValueError("Use starttls ou ssl no campo seguranca.")
    return config


def enviar_convites(clientes, config, senha):
    contexto = ssl.create_default_context()
    if config["seguranca"] == "ssl":
        servidor = smtplib.SMTP_SSL(
            config["servidor"], config["porta"], context=contexto, timeout=30
        )
    else:
        servidor = smtplib.SMTP(config["servidor"], config["porta"], timeout=30)

    enviados = 0
    with servidor:
        if config["seguranca"] == "starttls":
            servidor.ehlo()
            servidor.starttls(context=contexto)
            servidor.ehlo()
        servidor.login(config["usuario"], senha)
        for cliente in clientes:
            mensagem = montar_mensagem(cliente, config["remetente"], config["nome_remetente"])
            try:
                servidor.send_message(mensagem)
            except (smtplib.SMTPException, OSError) as erro:
                print(f"Falha para {cliente['email']}: {erro}")
            else:
                enviados += 1
                print(f"Enviado para {cliente['nome']} <{cliente['email']}>")
    print(f"\nResultado: {enviados} enviado(s), {len(clientes) - enviados} com falha.")
    return 0 if enviados == len(clientes) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clientes", type=Path, default=PASTA_PROJETO / "clientes.csv",
                        help="Arquivo CSV com nome e email.")
    parser.add_argument("--config", type=Path, default=PASTA_PROJETO / "config.json",
                        help="Arquivo de configuração SMTP para envio real.")
    parser.add_argument("--saida", type=Path, default=PASTA_PROJETO / "previas",
                        help="Pasta das mensagens geradas na simulação.")
    parser.add_argument("--enviar", action="store_true",
                        help="Envia e-mails de verdade. Sem esta opção, apenas simula.")
    args = parser.parse_args(argv)
    try:
        clientes = ler_clientes(args.clientes)
        if not args.enviar:
            simular(clientes, args.saida)
            return 0
        config = ler_configuracao(args.config)
        senha = os.environ.get("SMTP_SENHA") or getpass.getpass("Senha SMTP (oculta): ")
        if not senha:
            raise ValueError("Informe a senha SMTP para enviar os convites.")
        return enviar_convites(clientes, config, senha)
    except (ValueError, OSError, csv.Error, smtplib.SMTPException, EOFError) as erro:
        print(f"Erro: {erro}")
        return 1
    except KeyboardInterrupt:
        print("\nOperação interrompida.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
