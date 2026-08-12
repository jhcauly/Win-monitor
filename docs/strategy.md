# Estrategia operacional v0.3

## Principio

A estrutura de mercado e a MA20 definem o contexto principal. A MA8 funciona
como gatilho rapido. Fibonacci permanece como contexto auxiliar e hipotese de
filtro ate ser validado por backtest; nunca e sinal isolado.

## MA20: filtro principal de tendencia

- Compra: MA20 inclinada para cima.
- Venda: MA20 inclinada para baixo.
- O preco pode retornar/tocar a MA20 com pequena margem de seguranca.
- Em compra, perda confirmada da MA20 para baixo invalida a leitura.
- Em venda, rompimento confirmado da MA20 para cima invalida a leitura.
- MA20 lateral, ilegivel ou sem direcao bloqueia nova entrada.

## MA8: gatilho rapido

- Compra: MA8 acompanha a alta e fica acima da MA20 ou cruza para cima.
- Venda: MA8 acompanha a baixa e fica abaixo da MA20 ou cruza para baixo.
- Se a MA8 apenas toca a MA20 sem cruzar nem permanecer do lado correto, o setup
  continua como `QUASE`.
- Cruzamento sem inclinacao e sem estrutura nao e entrada.

## Estrutura: topo, fundo e rompimento

- Usar o topo ou fundo mais proximo e tecnicamente relevante.
- O pivo precisa estar confirmado sem usar candles futuros.
- Consolidacao bloqueia entrada ate existir rompimento valido.
- Compra exige rompimento do topo relevante a favor da tendencia.
- Venda exige rompimento do fundo relevante a favor da tendencia.
- O gatilho so e confirmado com candle fechado.

## Entrada, stop e alvo

- Entrada: rompimento/resumida da estrutura na direcao da MA20, com MA8 alinhada.
- Stop de compra: fundo tecnico relevante que invalida a operacao.
- Stop de venda: topo tecnico relevante que invalida a operacao.
- O alvo deve vir da estrutura tecnica observavel e ser registrado antes da entrada.
- Regras antigas de alvo fixo e projecoes de Fibonacci ficam como hipoteses de teste,
  nao como justificativa para inventar um alvo quando a tela nao o sustenta.

## Risco/retorno

Enquanto o backtest ainda nao definiu um limiar estatisticamente superior, o motor
usa `1:1` como piso tecnico de seguranca: o alvo 1 precisa oferecer recompensa
pelo menos igual ao risco ate o stop. Esse piso e uma decisao de engenharia do
MVP e deve ser reavaliado com dados, nao tratado como vantagem comprovada.

## Saida defensiva

- Violacao da MA20 contra a posicao exige saida defensiva.
- Se o movimento passar a andar contra a posicao e ocorrer cruzamento contrario da
  MA8, a posicao deve ser encerrada defensivamente.
- Stop nunca pode ser afastado para aumentar risco.

## Auditoria

Cada ciclo salva separadamente a observacao visual bruta e a decisao produzida
pelo motor deterministico. Isso permite descobrir se um erro veio da leitura da
tela ou da regra operacional, em vez de misturar as duas coisas.

## Classificacoes

- `ENTRADA`: tendencia, estrutura, gatilho, stop, alvo e RR confirmados.
- `QUASE`: existe contexto, mas falta uma confirmacao objetiva.
- `SEM_SETUP`: nao existe contexto operacional seguro ou a leitura e insuficiente.

Codigos iniciais de `QUASE`:

- `MA8_SEM_INCLINACAO`
- `MA8_SEM_CRUZAMENTO`
- `M60_FRACO`
- `RANGE`
- `ROMPIMENTO_AUSENTE`
- `CANDLE_NAO_FECHADO`
- `STOP_GRANDE`
- `RR_INSUFICIENTE`
- `PIVO_NAO_CONFIRMADO`
- `PLANO_INCOMPLETO`
- `LEITURA_INSUFICIENTE`

## Fibonacci

Fibonacci pode ser registrado como contexto de retracao, confluencia ou alvo
candidato. A influencia real sobre expectativa, payoff e drawdown sera decidida
por backtest, nao por autoridade visual ou exemplos selecionados.
