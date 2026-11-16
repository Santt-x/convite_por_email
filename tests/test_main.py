import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main


class TestConvites(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.csv = self.pasta / "clientes.csv"
        self.cliente = {"nome": "João", "email": "joao@example.com"}

    def test_csv_com_bom_e_ponto_e_virgula(self):
        self.csv.write_text("nome;email\nJoão;joao@example.com\n", encoding="utf-8-sig")
        self.assertEqual(main.ler_clientes(self.csv), [self.cliente])

    def test_lista_invalida_nao_inicia_envio(self):
        self.csv.write_text("nome,email\nAna,ana@example.com\nJoão,invalido\n", encoding="utf-8")
        with patch("main.enviar_convites") as envio:
            self.assertEqual(main.main(["--clientes", str(self.csv), "--enviar"]), 1)
        envio.assert_not_called()

    def test_emails_duplicados_sao_rejeitados(self):
        self.csv.write_text("nome,email\nAna,ana@example.com\nOutra,ANA@example.com\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "repetido"):
            main.ler_clientes(self.csv)

    def test_simulacao_preserva_convite_sem_acessar_smtp(self):
        self.csv.write_text("nome,email\nJoão,joao@example.com\n", encoding="utf-8")
        saida = self.pasta / "previas"
        with patch("main.smtplib.SMTP") as smtp, patch("main.smtplib.SMTP_SSL") as smtp_ssl:
            resultado = main.main(["--clientes", str(self.csv), "--saida", str(saida)])
        self.assertEqual(resultado, 0)
        smtp.assert_not_called()
        smtp_ssl.assert_not_called()
        mensagem = BytesParser(policy=policy.default).parsebytes((saida / "convite_001.eml").read_bytes())
        self.assertEqual(mensagem["Subject"], main.ASSUNTO)
        self.assertEqual(mensagem["To"], "joao@example.com")
        for texto in ("João", "11/12/2026", "20h30", "[ ] SIM", "[ ] NÃO"):
            self.assertIn(texto, mensagem.get_content())

    def test_configuracao_nao_aceita_conexao_sem_tls(self):
        config = {"servidor": "smtp.example.com", "porta": 587, "seguranca": "nenhuma",
                  "usuario": "empresa@example.com", "remetente": "empresa@example.com",
                  "nome_remetente": "ZÉ Empréstimos"}
        caminho = self.pasta / "config.json"
        caminho.write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "starttls ou ssl"):
            main.ler_configuracao(caminho)

    def test_envio_usa_tls_antes_da_senha_e_um_destinatario_por_mensagem(self):
        config = {"servidor": "smtp.example.com", "porta": 587, "seguranca": "starttls",
                  "usuario": "empresa@example.com", "remetente": "empresa@example.com",
                  "nome_remetente": "ZÉ Empréstimos"}
        clientes = [self.cliente, {"nome": "Ana", "email": "ana@example.com"}]
        with patch("main.smtplib.SMTP") as smtp:
            servidor = smtp.return_value
            resultado = main.enviar_convites(clientes, config, "senha-de-teste")
        self.assertEqual(resultado, 0)
        chamadas = [chamada[0] for chamada in servidor.method_calls]
        self.assertLess(chamadas.index("starttls"), chamadas.index("login"))
        mensagens = [chamada.args[0] for chamada in servidor.send_message.call_args_list]
        self.assertEqual([m["To"] for m in mensagens], [c["email"] for c in clientes])
        self.assertTrue(all(m["Reply-To"] == config["remetente"] for m in mensagens))

    def test_falha_em_um_cliente_permite_enviar_para_o_seguinte(self):
        config = {"servidor": "smtp.example.com", "porta": 465, "seguranca": "ssl",
                  "usuario": "empresa@example.com", "remetente": "empresa@example.com",
                  "nome_remetente": "ZÉ Empréstimos"}
        clientes = [self.cliente, {"nome": "Ana", "email": "ana@example.com"}]
        with patch("main.smtplib.SMTP_SSL") as smtp:
            servidor = smtp.return_value
            servidor.send_message.side_effect = [main.smtplib.SMTPRecipientsRefused({}), {}]
            resultado = main.enviar_convites(clientes, config, "senha-de-teste")
        self.assertEqual(resultado, 1)
        self.assertEqual(servidor.send_message.call_count, 2)
        servidor.starttls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
