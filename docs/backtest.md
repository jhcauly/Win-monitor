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

## Medias

O motor de backtest implementa SMA e EMA explicitamente. Como o projeto ainda nao
formalizou qual tipo corresponde a MA8/MA20 da configuracao visual, nenhum deles e
tratado silenciosamente como padrao da estrategia. Os dois podem ser comparados
quando a simulacao historica estiver conectada.

## Pivos sem look-ahead

Topos e fundos sao detectados com janelas esquerda/direita, mas o pivo so fica
disponivel para a estrategia depois que os candles de confirmacao a direita ja
fecharam. Assim, o backtest nao entrega ao sinal uma informacao que ainda nao
existia naquele instante.

## Metricas implementadas

- numero de trades, vencedores e perdedores;
- taxa de acerto;
- resultado liquido e expectativa em pontos;
- ganho medio, perda media e payoff;
- profit factor;
- drawdown maximo;
- MAE e MFE medios quando disponiveis.

## Validacao

A base pode ser dividida cronologicamente em treino, validacao e teste fora da
amostra. A ordem temporal e preservada; nao ha embaralhamento aleatorio.

## Pendencia para o simulador historico da estrategia

Falta ligar os indicadores e pivos ao conjunto exato de regras multi-timeframe da
estrategia. O tipo de media e a distribuicao de MA8/MA20 entre M60/M15/M5 devem
ser tratados como parametros comparaveis ate a configuracao operacional ficar
formalizada.
