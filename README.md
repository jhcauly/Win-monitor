# WIN Monitor

Sistema de apoio ao estudo e a disciplina no day trade do Mini Indice (WIN).
Ele captura M60, M15 e M5, extrai observacoes visuais, aplica regras
deterministicas, salva a evidencia e envia os casos relevantes ao Telegram.

> **Modo estudo:** o sistema nao executa ordens e nao promete lucro.

## Estrategia atual

- **MA20:** filtro principal de tendencia pela inclinacao e posicao do preco.
- **MA8:** gatilho rapido; precisa acompanhar a direcao e ficar do lado correto
  da MA20 ou confirmar cruzamento a favor.
- **Estrutura:** topo/fundo relevante, pivo confirmado sem look-ahead,
  consolidacao e rompimento com candle fechado.
- **Stop:** fundo tecnico em compra e topo tecnico em venda.
- **Alvo:** precisa ser sustentado por nivel estrutural observavel antes da entrada.
- **Risco/retorno:** piso tecnico inicial de 1:1, sujeito a revisao por backtest.
- **Fibonacci:** contexto auxiliar e hipotese de teste, nunca sinal isolado.

## Arquitetura de decisao

A visao nao decide a operacao. O provedor visual apenas devolve dados estruturados
sobre MA20, MA8, preco, pivos, rompimento, candle e contexto. O motor local entao
classifica `ENTRADA`, `QUASE` ou `SEM_SETUP`. Cada observacao bruta fica salva em
`observacoes_visuais.jsonl`, separada da decisao, para auditoria posterior.

## Recursos desta versao

- interface grafica para Windows;
- seletor visual da area dos graficos;
- credenciais fora do codigo;
- captura alinhada ao fechamento M5;
- analise visual M60/M15/M5;
- motor deterministico de MA20/MA8, estrutura e rompimento;
- validacao de stop, alvo e risco/retorno;
- calculo de risco do WIN e quantidade entre 1 e 5 contratos;
- motivo estruturado para cenarios `QUASE`;
- evidencia anotada, CSV, JSONL e Telegram;
- acompanhamento aproximado de stop/alvo;
- importador de CSV intraday Profit/Nelogica;
- consolidacao historica M5/M15/M60;
- SMA e EMA implementadas como alternativas explicitas;
- pivos historicos confirmados sem look-ahead;
- metricas de backtest e divisao treino/validacao/teste;
- testes automatizados e build do executavel pelo GitHub Actions.

## Uso pelo executavel

1. Extraia o pacote e abra `WinMonitor.exe`.
2. Informe a chave Anthropic, token do bot e chat ID.
3. O modelo padrao e `claude-sonnet-5` e pode ser alterado na interface.
4. Clique em **Testar Telegram**.
5. Deixe os graficos M60, M15 e M5 visiveis.
6. Clique em **Selecionar area** e arraste sobre os tres graficos.
7. Clique em **Iniciar monitor**.

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
docs/                  estrategia, backtest e roadmap
tests/                 testes unitarios
.github/workflows/     CI e build do Windows
```

## Limitacoes conhecidas

- A extracao visual pode errar; por isso a decisao foi separada da leitura.
- A verificacao de stop/alvo em tempo real ocorre por amostragem, nao tick a tick.
- O modelo configurado precisa suportar entrada de imagem e estar disponivel na
  conta Anthropic usada.
- O motor historico multi-timeframe de sinais ainda precisa comparar a
  configuracao exata de MA8/MA20 e as regras de alvo antes de qualquer conclusao.
- Nenhuma ordem e enviada automaticamente.
