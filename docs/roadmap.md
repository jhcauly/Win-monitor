# Roadmap

## Fase 1A - monitor de estudo

- [x] Captura alinhada ao fechamento M5.
- [x] Analise visual M60/M15/M5.
- [x] Classificacao ENTRADA, QUASE e SEM_SETUP.
- [x] Evidencia anotada, log CSV e Telegram.
- [x] Acompanhamento aproximado de stop/alvo.
- [x] Seletor visual da area de captura.
- [x] Nenhuma execucao de ordem.

## Fase 1B - regras deterministicas

- [x] Separar extracao visual de decisao operacional.
- [x] Formalizar MA20 como filtro principal e MA8 como gatilho rapido.
- [x] Formalizar topo/fundo, rompimento, candle fechado e consolidacao.
- [x] Formalizar stop tecnico e saida defensiva.
- [x] Adicionar piso tecnico de risco/retorno de 1:1, ajustavel apos backtest.
- [x] Registrar o motivo de cada QUASE.
- [x] Integrar o motor deterministico ao extrator visual.
- [x] Persistir observacao visual bruta para auditoria e backtest.

## Fase 1C - backtest

- [x] Importador de CSV intraday no layout Profit/Nelogica.
- [x] Consolidacao deterministica de candles para M5/M15/M60.
- [x] Metricas: expectativa, payoff, profit factor, drawdown, MAE e MFE.
- [ ] Formalizar o tipo de MA8/MA20 antes de simular sinais historicos.
- [ ] Implementar motor historico sem look-ahead.
- [ ] Separacao treino, validacao e teste fora da amostra.

## Fase 2 - ProfitDLL

- [ ] Receber candles e precos diretamente da API oficial.
- [ ] Substituir gradualmente leitura de pixels por dados estruturados.
- [ ] Manter roteamento de ordens desligado ate validacao formal.

## Fase 3 - semi-automacao

- [ ] Plano operacional completo.
- [ ] Confirmacao humana obrigatoria.
- [ ] Travas de risco e stop que nunca pode ser afastado.
