# Roadmap

## Fase 1A - monitor de estudo

- Captura alinhada ao fechamento M5.
- Analise visual M60/M15/M5.
- Classificacao ENTRADA, QUASE e SEM_SETUP.
- Evidencia anotada, log CSV e Telegram.
- Acompanhamento aproximado de stop/alvo.
- Nenhuma execucao de ordem.

## Fase 1B - regras deterministicas

- Separar extracao visual de decisao operacional.
- Formalizar pivos, consolidacao, Fibonacci e inclinacao da MA8.
- Adicionar validacao de risco/retorno.
- Registrar o motivo de cada QUASE.

## Fase 1C - backtest

- Importador de CSV exportado pelo Profit.
- Dados M5/M15/M60 sem look-ahead.
- Expectativa, payoff, profit factor, drawdown, MAE e MFE.
- Separacao treino, validacao e teste fora da amostra.

## Fase 2 - ProfitDLL

- Receber candles e precos diretamente da API oficial.
- Substituir gradualmente leitura de pixels por dados estruturados.
- Manter roteamento de ordens desligado ate validacao formal.

## Fase 3 - semi-automacao

- Plano operacional completo.
- Confirmacao humana obrigatoria.
- Travas de risco e stop que nunca pode ser afastado.
