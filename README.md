# WIN Monitor

Sistema de apoio ao estudo e a disciplina no day trade do Mini Indice (WIN).
Ele captura a tela com M60, M15 e M5, pede uma leitura visual, classifica o
cenario em `ENTRADA`, `QUASE` ou `SEM_SETUP`, salva a evidencia e envia os
casos relevantes ao Telegram.

> **Modo estudo:** o sistema nao executa ordens e nao promete lucro.

## Estrategia atual

- **M60:** vies pela relacao entre preco, MA8 e MA20.
- **M15:** swing/pivo, consolidacao e zona Fibonacci de 50% a 61,8%.
- **M5:** cruzamento e inclinacao da MA8 dentro da zona.
- **Stop:** estrutura que originou o swing.
- **Alvos:** projecoes Fibonacci de 100% e 161,8%.

A zona de Fibonacci e apenas uma zona de atencao. A MA8 e o fechamento do
candle confirmam ou cancelam a entrada.

## Melhorias desta versao

- credenciais fora do codigo;
- interface grafica para Windows;
- validacao que bloqueia `ENTRADA` sem stop/alvo completos;
- calculo de risco do WIN e quantidade entre 1 e 5 contratos;
- motivo estruturado para cenarios `QUASE`;
- armazenamento atomico dos sinais em aberto;
- testes automatizados;
- build de executavel pelo GitHub Actions.

## Uso pelo executavel

1. Baixe o artefato `WinMonitor-Windows` na aba **Actions** do GitHub.
2. Extraia o ZIP e abra `WinMonitor.exe`.
3. Informe a chave Anthropic, token do bot e chat ID.
4. Clique em **Testar Telegram**.
5. Deixe os graficos M60, M15 e M5 visiveis e clique em **Iniciar monitor**.

As credenciais ficam em `%APPDATA%\WinMonitor\.env` e nao entram no GitHub.
Capturas e logs ficam na mesma pasta.

## Uso pelo codigo-fonte

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
copy .env.example .env
python -m win_monitor.launcher
```

Modo texto:

```powershell
win-monitor --once
win-monitor
```

## Testes

```powershell
pytest
ruff check .
```

## Estrutura

```text
src/win_monitor/       codigo modular
docs/                  estrategia e roadmap
tests/                 testes unitarios
.github/workflows/     CI e build do Windows
```

## Limitacoes conhecidas

- A decisao visual ainda depende de um provedor de visao e pode errar.
- A verificacao de stop/alvo ocorre por amostragem, nao tick a tick.
- O modelo deve conseguir ler imagens e estar disponivel na conta configurada.
- O backtest com dados intraday reais do Profit ainda sera implementado.
