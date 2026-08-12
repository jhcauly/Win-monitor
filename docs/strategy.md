# Estrategia operacional v0.1

## Principio

A zona de Fibonacci e uma zona de atencao, nao um gatilho. A entrada so pode
ser classificada como valida quando o contexto M60, a estrutura M15 e o
gatilho M5 convergem.

## M60: vies

- Compra: preco acima da MA20 e MA8 acima da MA20.
- Venda: preco abaixo da MA20 e MA8 abaixo da MA20.
- Medias embaracadas ou sem inclinacao: sem vies.

## M15: estrutura

- Identificar o ultimo swing relevante por pivo/fractal confirmado.
- Um pivo que depende de candles a direita so existe depois desses candles
  fecharem.
- Mercado em consolidacao deve bloquear a entrada.
- A retracao de 50% a 61,8% do swing forma a zona de atencao.

## M5: gatilho

Dentro da zona de atencao:

1. o preco cruza a MA8 a favor do vies;
2. a MA8 inclina na mesma direcao;
3. o candle fecha;
4. entrada, stop e alvo ficam legiveis.

## Stop e alvos

- Stop: abaixo do fundo ou acima do topo que originou o swing.
- Alvo 1: projecao de Fibonacci em 100%.
- Alvo 2: projecao de Fibonacci em 161,8%.

## Classificacoes

- `ENTRADA`: todas as condicoes confirmadas.
- `QUASE`: contexto existente, mas faltou uma confirmacao objetiva.
- `SEM_SETUP`: sem contexto operacional ou leitura insuficiente.

Codigos iniciais de `QUASE`:

- `FIB_SEM_MA8`
- `MA8_SEM_INCLINACAO`
- `M60_FRACO`
- `RANGE`
- `STOP_GRANDE`
- `RR_INSUFICIENTE`
- `PIVO_NAO_CONFIRMADO`
- `LEITURA_INSUFICIENTE`
