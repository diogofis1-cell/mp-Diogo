# Análise Comparativa de Algoritmos para Previsão de Visualizações Diárias em Portal Institucional do Setor Público

## Descrição

Este repositório contém os códigos-fonte, notebooks, bases tratadas e resultados produzidos na pesquisa de mestrado intitulada:

**"Análise Comparativa de Algoritmos para Previsão de Visualizações Diárias em Portal Institucional do Setor Público"**

O estudo compara diferentes algoritmos de previsão de séries temporais aplicados ao Portal do Tribunal Regional do Trabalho da 18ª Região (TRT18), utilizando dados históricos de visualizações de páginas extraídos do Google Analytics 4 (GA4).

---

## Objetivo

Avaliar e comparar o desempenho de diferentes modelos estatísticos, de aprendizado de máquina e de redes neurais na previsão do número diário de visualizações do Portal do TRT18.

A pesquisa busca identificar quais algoritmos apresentam melhor capacidade preditiva para apoiar futuras iniciativas de planejamento e gestão da infraestrutura digital do Portal.

---

## Base de Dados

**Fonte:** Google Analytics 4 (GA4)

**Portal analisado:** Portal Institucional do TRT18

**Variável-alvo:** Número diário de visualizações de páginas (Page Views)

**Período analisado:** 01/07/2023 a 15/04/2026

**Quantidade de registros:** 1020 observações diárias

Os dados foram exportados por meio do Looker Studio e submetidos a etapas de tratamento, padronização e enriquecimento com atributos temporais e institucionais.

---

## Variáveis Utilizadas

Além da variável-alvo (visualizações), foram criados atributos relacionados ao calendário, incluindo:

* Dia da semana
* Mês
* Dia do ano
* Ano
* Indicador de final de semana
* Recesso judiciário
* Feriados nacionais
* Feriados móveis derivados da Páscoa
* Datas específicas do Poder Judiciário
* Pontos facultativos

Para alguns modelos também foram utilizadas:

* Defasagem de 1 dia
* Defasagem de 7 dias
* Defasagem de 30 dias
* Média móvel de 7 dias
* Média móvel de 30 dias

---

## Algoritmos Avaliados

Foram comparados seis modelos de previsão:

### ARIMA

Modelo estatístico clássico para séries temporais.

### SARIMAX

Extensão do ARIMA com componente sazonal e variáveis exógenas.

### Prophet

Modelo desenvolvido pelo Facebook para séries temporais com tendência, sazonalidade e efeitos de calendário.

### SVR (Support Vector Regression)

Algoritmo de aprendizado de máquina baseado em máquinas de vetores de suporte.

### GRU (Gated Recurrent Unit)

Rede neural recorrente voltada para aprendizado de dependências temporais.

### LSTM (Long Short-Term Memory)

Rede neural recorrente com memória de longo prazo.

---

## Métricas de Avaliação

Todos os modelos foram avaliados utilizando:

* MAE (Mean Absolute Error)
* RMSE (Root Mean Squared Error)
* R² (Coeficiente de Determinação)

A divisão entre treino e teste foi realizada de forma sequencial:

* 80% dos registros para treinamento
* 20% dos registros para teste

Sem embaralhamento dos dados.

---

## Resultados Obtidos

| Modelo  | MAE   | RMSE   | R²    |
| ------- | ----- | ------ | ----- |
| ARIMA   | 6.710 | 11.852 | 0,502 |
| SARIMAX | 6.488 | 10.279 | 0,626 |
| Prophet | 7.826 | 9.742  | 0,664 |
| SVR     | 3.179 | 4.636  | 0,924 |
| GRU     | 4.306 | 6.812  | 0,835 |
| LSTM    | 4.230 | 6.693  | 0,841 |

### Melhor desempenho

O modelo **SVR** apresentou os melhores resultados em todas as métricas avaliadas:

* MAE = 3.179
* RMSE = 4.636
* R² = 0,924

---

## Estrutura do Projeto

```text
projeto/
│
├── dados/
│   ├── trafego_tratado.csv
│   └── demais arquivos de entrada
│
├── Notebooks/
│   ├── Arima.ipynb
│   ├── SARIMAX.ipynb
│   ├── Prophet.ipynb
│   ├── SVR.ipynb
│   ├── GRU.ipynb
│   └── LSTM.ipynb
│
├── resultados/
│   ├── figuras/
│   ├── métricas/
│   └── previsões/
│
└── README.md
```

---

## Tecnologias Utilizadas

* Python 3.12
* Jupyter Notebook
* Pandas
* NumPy
* Matplotlib
* Scikit-learn
* Statsmodels
* Prophet
* TensorFlow / Keras

---

## Reprodutibilidade

Para reproduzir os experimentos:

1. Clone o repositório.
2. Instale as dependências listadas em `requirements.txt`.
3. Execute os notebooks individualmente.
4. Os resultados serão gerados automaticamente na pasta `resultados`.

---

## Autor

**Diogo Felipe de Aguiar**

Mestrado Profissional em Tecnologia, Gestão e Sustentabilidade

Instituto Federal de Goiás (IFG)

---

## Orientador

**Prof. Dr. Raphael de Aquino Gomes**

Instituto Federal de Goiás (IFG)
