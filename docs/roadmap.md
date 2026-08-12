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

- [ ] Separar extracao visual de decisao operacional.
- [x] Formalizar MA20 como filtro principal e MA8 como gatilho rapido.
- [x] Formalizar topo/fundo, rompimento, candle fechado e consolidacao.
- [x] Formalizar stop tecnico e saida defensiva.
- [ ] Adicionar validacao deterministica de risco/retorno.
- [x] Registrar o motivo de cada QUASE.
- [ ] Integrar o motor deterministico ao extrator visual.

## Fase 1C - backtest

- [ ] Importador de CSV exportado pelo Profit.
- [ ] Dados M5/M15/M60 sem look-ahead.
- [ ] Expectativa, payoff, profit factor, drawdown, MAE e MFE.
- [ ] Separacao treino, validacao e teste fora da amostra.

## Fase 2 - ProfitDLL

- [ ] Receber candles e precos diretamente da API oficial.
- [ ] Substituir gradualmente leitura de pixels por dados estruturados.
- [ ] Manter roteamento de ordens desligado ate validacao formal.

## Fase 3 - semi-automacao

- [ ] Plano operacional completo.
- [ ] Confirmacao humana obrigatoria.
- [ ] Travas de risco e stop que nunca pode ser afastado.
