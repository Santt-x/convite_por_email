# Convite por e-mail — ZÉ Empréstimos

Atividade em Python que prepara convites individuais para o jantar de aniversário
da empresa, em **11/12/2026, às 20h30, na própria empresa**.

O programa lê os nomes e endereços de um CSV, monta a mensagem e pode simular ou
enviar os convites. As opções SIM e NÃO são texto: o cliente deve responder ao
e-mail marcando um X. A leitura e a contagem das respostas são manuais.

## Requisitos

- Python 3.10 ou superior.
- Para editar e depurar no VS Code, extensão Python da Microsoft.
- Nenhum pacote precisa ser instalado com pip: só há bibliotecas do Python.
- Para envio real, conta com acesso SMTP e os dados fornecidos pelo provedor.

## Começar pela simulação

Abra esta pasta no VS Code. Para executar com o interpretador selecionado, abra
`main.py` e use **Run Python File in Terminal** (botão de executar no editor).
Também é possível usar o terminal integrado:

```powershell
python main.py
```

O convite aparece no terminal, e uma mensagem `.eml` por cliente é gerada na
pasta `previas`. Esses arquivos podem ser abertos em um aplicativo de e-mail
compatível. A simulação usa remetente fictício, não solicita senha e não conecta
à internet. Rodá-la novamente atualiza os arquivos de mesmo nome.

Também é possível usar **Executar > Iniciar Depuração (F5)** com a configuração
“Simular convites (sem enviar e-mails)”. Se necessário, use **Python: Select
Interpreter** na paleta de comandos e selecione seu Python instalado.

Se o comando `python` não estiver disponível, experimente `py main.py` ou
selecione a instalação do Python no VS Code. A configuração local em
`.vscode/settings.json` aponta para o Python disponível no ambiente Codex deste
computador. Se mover o projeto, ajuste o interpretador para sua instalação.

## Lista de clientes

Edite `clientes.csv`, mantendo o cabeçalho e salvando em UTF-8:

```csv
nome,email
Ana Silva,ana@example.com
Bruno Souza,bruno@example.com
```

Os endereços incluídos são fictícios. Substitua-os antes do envio real. Para o
primeiro teste de envio, deixe somente seu nome e seu próprio endereço na lista.
Também é aceito o separador ponto e vírgula (`nome;email`). Nomes com vírgula
devem ficar entre aspas quando o separador for vírgula.

Se houver endereço com formato inválido, coluna faltando ou e-mail repetido, o
programa informa o problema antes de enviar qualquer convite. A validação é
básica e não confirma a existência das caixas de e-mail.

## Configurar o envio real

1. Copie `config.exemplo.json` para `config.json`.
2. Preencha servidor, porta, usuário e remetente com os dados da sua conta SMTP.
3. Use `"starttls"` ou `"ssl"` conforme as instruções do provedor; a porta também
   deve corresponder ao método informado. Os valores do exemplo são ilustrativos.
4. Execute:

```powershell
python main.py --enviar
```

A senha será solicitada no terminal e não aparecerá enquanto for digitada.
Caso o provedor exija senha de aplicativo, informe essa senha. Contas que não
permitem autenticação SMTP com senha precisam de outra forma de integração.
A variável de ambiente `SMTP_SENHA`, quando definida, também pode fornecer a senha.
O programa não lê arquivos `.env`.

Cada cliente recebe apenas seu próprio convite. As respostas voltam ao endereço
configurado como `remetente`. O resultado informa os envios aceitos pelo servidor
e as falhas; aceite pelo servidor não garante entrega na caixa de entrada.
Cada execução com `--enviar` faz novos envios, inclusive aos clientes já atendidos.
Se houver falhas ou interrupção, confira os resultados antes de repetir a lista.

## Outros comandos

```powershell
python main.py --help
python main.py --clientes outra_lista.csv --saida outras_previas
python -m unittest discover -s tests -v
```

Os testes usam um servidor SMTP simulado e não enviam e-mails.

## Organização e estudo do código

- `main.py`: aplicação e texto do convite, em `TEXTO_CONVITE`.
- `clientes.csv`: nomes e endereços de exemplo.
- `config.exemplo.json`: modelo de configuração para envio real.
- `.vscode/`: configuração de depuração e extensões recomendadas.
- `tests/test_main.py`: validação dos dados, mensagem e fluxo SMTP.

Em `main.py`, `ler_clientes` usa `csv` para ler e validar a lista;
`montar_mensagem` usa `EmailMessage` para criar o e-mail com acentos;
`simular` grava as prévias; `enviar_convites` usa `smtplib` com TLS para enviar;
e `main` escolhe o modo de execução com `argparse`.
