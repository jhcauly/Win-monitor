# Backtest - especificacao inicial

## Fonte de dados

O importador aceita o layout intraday oficial da Nelogica e variantes de cabecalho
em portugues/ingles. Campos essenciais: data, tempo/hora, abertura, maxima, minima
e fechamento. Ativo, numero de negocios, volume e quantidade sao opcionais.

O parser detecta virgula, ponto e virgula ou tabulacao como delimitador, aceita
UTF-8/Latin-1 e normaliza numeros no formato brasileiro.

## Timeframes

A base intraday pode ser consolidada deterministicamente para 5, 15 e 60 minutos.
Nenhum candle futuro pode participar da formacao do candle atual.

## Metricas implementadas

- numero de trades, vencedores e perdedores;
- taxa de acerto;
- resultado liquido e expectativa em pontos;
- ganho medio, perda media e payoff;
- profit factor;
- drawdown maximo;
- MAE e MFE medios quando disponiveis.

## Pendencia antes do simulador historico da estrategia

O tipo exato das medias MA8 e MA20 (por exemplo, simples ou exponencial) ainda
nao esta formalizado no projeto. O motor de sinais historicos nao deve assumir
isso silenciosamente. Importacao, consolidacao e metricas podem ser validadas
independentemente dessa definicao.
