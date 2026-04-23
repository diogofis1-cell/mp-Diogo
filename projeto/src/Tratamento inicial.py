# %%
## 1. Leitura da base de dados
import pandas as pd

df = pd.read_csv("../dados/trafego.csv")
alvo = "Visualizações" # Mude aqui se decidir focar em Sessões depois
df.head()

# %%
## 2. Verificação da estrutura dos dados
df.info()

# %% [markdown]
# ## 3. Conversão da coluna de data
# 
# A coluna `Data` foi inicialmente carregada como texto (`str`), e não como data reconhecida pelo Python. Por isso, foi necessário realizar algumas conversões antes de utilizá-la na análise.
# 
# Primeiro, os nomes abreviados dos meses em português, como `jul.` e `ago.`, foram substituídos por seus respectivos números (`07`, `08` etc.). Essa etapa foi necessária porque a função de conversão de datas utilizada no pandas trabalha mais facilmente com valores numéricos padronizados no formato dia/mês/ano.
# 
# Em seguida, a expressão textual `" de "` foi substituída pelo caractere `/`, transformando datas como `1 de jul. de 2023` em um padrão mais adequado para conversão, como `1/07/2023`.
# 
# Por fim, a coluna foi convertida para o tipo `datetime`, que é o formato apropriado para trabalhar com datas no pandas. Essa conversão é importante porque permite extrair variáveis temporais úteis ao modelo, como dia da semana, mês, fim de semana e outras características calendáricas que podem influenciar o comportamento do tráfego.
# 

# %%
meses = {
    "jan.": "01", "fev.": "02", "mar.": "03", "abr.": "04",
    "mai.": "05", "jun.": "06", "jul.": "07", "ago.": "08",
    "set.": "09", "out.": "10", "nov.": "11", "dez.": "12"
}

for mes_pt, mes_num in meses.items():
    df["Data"] = df["Data"].str.replace(mes_pt, mes_num, regex=False)

df["Data"] = df["Data"].str.replace(" de ", "/", regex=False)
df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")

df.head()
df = df.sort_values('Data').reset_index(drop=True)

# %% [markdown]
# ## 4. Criação da variável dia da semana
# 
# Nesta etapa, é criada uma variável representando o dia da semana de cada observação. Essa informação pode ser relevante para o modelo, pois o tráfego do portal apresenta comportamento distinto entre dias úteis e finais de semana.

# %%
df["dia_semana"] = df["Data"].dt.dayofweek + 1
df[["Data", "dia_semana"]].head(10)

# %% [markdown]
# ## 5. Criação da variável indicadora de fim de semana
# 
# Além do dia da semana, foi criada uma variável binária para identificar se a observação pertence a um fim de semana. Essa variável pode ser útil porque o tráfego do portal tende a cair significativamente aos sábados e domingos.

# %%
df["fim_de_semana"] = (df["Data"].dt.dayofweek >= 5).astype(int)
df[["Data", "dia_semana", "fim_de_semana"]].head(10)

# %% [markdown]
# ## 6. Criação da variável mês
# 
# Também foi criada uma variável correspondente ao mês de cada observação. Essa informação pode ajudar o modelo a captar padrões sazonais mais amplos no comportamento do tráfego ao longo do ano.

# %%
df["mes"] = df["Data"].dt.month
df[["Data", "mes"]].head(90)

# %% [markdown]
# ## 7. Criação da variável de recesso judiciário
# 
# Foi criada uma variável binária para identificar o período de recesso judiciário, compreendido entre 20 de dezembro e 6 de janeiro. Essa variável foi incluída porque esse intervalo tende a alterar de forma relevante o padrão de utilização do portal.

# %%
df["recesso_judiciario"] = (
    ((df["Data"].dt.month == 12) & (df["Data"].dt.day >= 20)) |
    ((df["Data"].dt.month == 1) & (df["Data"].dt.day <= 6))
).astype(int)



# %% [markdown]
# ## 8. Criação de variáveis relacionadas a feriados nacionais e feriados móveis
# 
# Nesta etapa, foram criadas variáveis indicadoras para representar datas com potencial impacto no tráfego do Portal. Foram considerados tanto os feriados nacionais de data fixa quanto feriados móveis relevantes para o funcionamento do Judiciário, como Carnaval, quarta-feira de cinzas, sexta-feira da Paixão e Corpus Christi.
# 
# A inclusão dessas variáveis é importante porque tais datas podem provocar reduções abruptas no volume de acessos, em razão da suspensão de expediente, da diminuição da atividade institucional ou da alteração do comportamento dos usuários. Dessa forma, busca-se fornecer aos modelos informações temporais adicionais que permitam explicar melhor oscilações atípicas da série.

# %%
from dateutil.easter import easter
import pandas as pd

# =========================================
# 9.1 Feriados nacionais de data fixa
# =========================================

feriados_fixos = [
    (1, 1),    # Confraternização Universal
    (4, 21),   # Tiradentes
    (5, 1),    # Dia do Trabalho
    (9, 7),    # Independência do Brasil
    (10, 12),  # Nossa Senhora Aparecida
    (11, 2),   # Finados
    (11, 15),  # Proclamação da República
    (12, 25)   # Natal
]

datas_feriados_fixos = []

ano_inicial = df['Data'].dt.year.min()
ano_final = df['Data'].dt.year.max()

for ano in range(ano_inicial, ano_final + 1):
    for mes, dia in feriados_fixos:
        datas_feriados_fixos.append(pd.Timestamp(year=ano, month=mes, day=dia))

    # Consciência Negra: feriado nacional a partir de 2024
    if ano >= 2024:
        datas_feriados_fixos.append(pd.Timestamp(year=ano, month=11, day=20))

feriados_nacionais_fixos = pd.DatetimeIndex(datas_feriados_fixos)

feriados_nacionais_fixos = feriados_nacionais_fixos[
    (feriados_nacionais_fixos >= df['Data'].min()) &
    (feriados_nacionais_fixos <= df['Data'].max())
]

df['feriado_nacional_fixo'] = (
    df['Data'].isin(feriados_nacionais_fixos) & 
    (df['fim_de_semana'] == 0)
).astype(int)

# =========================================
# 9.2 Feriados móveis relevantes
# =========================================

datas_carnaval = []
datas_quarta_cinzas = []
datas_sexta_paixao = []
datas_corpus_christi = []

for ano in range(ano_inicial, ano_final + 1):
    pascoa = pd.Timestamp(easter(ano))

    carnaval_segunda = pascoa - pd.Timedelta(days=48)
    carnaval_terca = pascoa - pd.Timedelta(days=47)
    quarta_cinzas = pascoa - pd.Timedelta(days=46)
    sexta_paixao = pascoa - pd.Timedelta(days=2)
    corpus_christi = pascoa + pd.Timedelta(days=60)

    datas_carnaval.extend([carnaval_segunda, carnaval_terca])
    datas_quarta_cinzas.append(quarta_cinzas)
    datas_sexta_paixao.append(sexta_paixao)
    datas_corpus_christi.append(corpus_christi)

df['carnaval'] = (df['Data'].isin(pd.DatetimeIndex(datas_carnaval)) & (df['fim_de_semana'] == 0)).astype(int)
df['quarta_cinzas'] = (df['Data'].isin(pd.DatetimeIndex(datas_quarta_cinzas)) & (df['fim_de_semana'] == 0)).astype(int)
df['sexta_paixao'] = (df['Data'].isin(pd.DatetimeIndex(datas_sexta_paixao)) & (df['fim_de_semana'] == 0)).astype(int)
df['corpus_christi'] = (df['Data'].isin(pd.DatetimeIndex(datas_corpus_christi)) & (df['fim_de_semana'] == 0)).astype(int)

# =========================================
# Visualização rápida
# =========================================

df.loc[
    (df['feriado_nacional_fixo'] == 1) |
    (df['carnaval'] == 1) |
    (df['quarta_cinzas'] == 1) |
    (df['sexta_paixao'] == 1) |
    (df['corpus_christi'] == 1),
    ['Data', 'feriado_nacional_fixo', 'carnaval', 'quarta_cinzas', 'sexta_paixao', 'corpus_christi']
].sort_values('Data')

# %%
df.loc[df["feriado_nacional_fixo"] == 1, "Data"].dt.year.value_counts().sort_index()

# %% [markdown]
# ## 09. Criação da variável de datas fixas relevantes ao Judiciário
# 
# Além dos feriados nacionais de data fixa, foi criada uma variável binária para identificar datas fixas relevantes ao Poder Judiciário e à administração pública. Essas datas podem influenciar o padrão de acesso ao portal e, por isso, foram tratadas separadamente dos feriados nacionais.
# 
# Optou-se por não incluir o dia 20 de novembro nessa variável, pois essa data já foi considerada na variável de feriado nacional fixo a partir de 2024.
# 

# %%
datas_judiciario = [
    (8, 11),   # Dia do Magistrado
    (10, 28),  # Dia do Servidor Público
    (12, 8)    # Dia da Justiça
]

datas_especificas = []

ano_inicial = df["Data"].dt.year.min()
ano_final = df["Data"].dt.year.max()

for ano in range(ano_inicial, ano_final + 1):
    for mes, dia in datas_judiciario:
        datas_especificas.append(pd.Timestamp(year=ano, month=mes, day=dia))

datas_judiciario_fixas = pd.DatetimeIndex(datas_especificas)

datas_judiciario_fixas = datas_judiciario_fixas[
    (datas_judiciario_fixas >= df["Data"].min()) &
    (datas_judiciario_fixas <= df["Data"].max())
]

df["data_especifica_judiciario"] = (
    df["Data"].isin(datas_judiciario_fixas) & 
    (df['fim_de_semana'] == 0)
).astype(int)

df.loc[df["data_especifica_judiciario"] == 1, ["Data", "data_especifica_judiciario"]]

# %% [markdown]
# ## 10. Criação da variável de ponto facultativo por emenda
# 
# Foi criada uma variável binária para identificar pontos facultativos decorrentes da prática de emenda de feriados. Considerou-se que, quando um feriado nacional fixo ocorre em uma terça-feira, a segunda-feira imediatamente anterior também tende a apresentar alteração relevante no funcionamento institucional e no padrão de uso do portal. De forma análoga, quando o feriado ocorre em uma quinta-feira, a sexta-feira imediatamente posterior também passa a ser tratada como data de emenda.
# 
# Essa variável foi mantida separada da variável de feriado, a fim de distinguir o efeito do feriado propriamente dito do efeito da suspensão de atividades por emenda.

# %%
datas_emenda = []

for data in feriados_nacionais_fixos:
    dia_semana = data.dayofweek  # segunda=0 ... domingo=6

    if dia_semana == 1:  # terça-feira
        datas_emenda.append(data - pd.Timedelta(days=1))

    elif dia_semana == 3:  # quinta-feira
        datas_emenda.append(data + pd.Timedelta(days=1))
for data_cc in datas_corpus_christi:
    datas_emenda.append(data_cc + pd.Timedelta(days=1))
# --------------------------

pontos_facultativos_emenda = pd.DatetimeIndex(datas_emenda)

pontos_facultativos_emenda = pontos_facultativos_emenda[
    (pontos_facultativos_emenda >= df["Data"].min()) &
    (pontos_facultativos_emenda <= df["Data"].max())
]

df["ponto_facultativo_emenda"] = df["Data"].isin(pontos_facultativos_emenda).astype(int)

df.loc[df["ponto_facultativo_emenda"] == 1, ["Data", "ponto_facultativo_emenda"]]

# %% [markdown]
# ## 11. Verifica se alguns valores estão faltando
# 
# Nesta etapa, foi realizada a verificação de valores ausentes em todas as colunas da base de dados.
# 
# A análise mostrou que **não há valores ausentes no dataset**, o que indica que, nesse aspecto, a base está íntegra para as próximas etapas de tratamento e modelagem.

# %%
print('=== VALORES AUSENTES POR COLUNA ===')

missing = df.isna().sum()
missing_pct = (missing / len(df)) * 100

missing_df = pd.DataFrame({
    'Valores_Nulos': missing,
    'Percentual (%)': missing_pct.round(2)
})

missing_df = missing_df[missing_df['Valores_Nulos'] > 0].sort_values(
    by='Valores_Nulos',
    ascending=False
)

if len(missing_df) > 0:
    print(missing_df)
else:
    print('✓ Não há valores ausentes no dataset!')

# %% [markdown]
# ##12. Verificação de duplicatas
# 
# Nesta etapa, foi realizada a verificação de registros duplicados na base de dados, com o objetivo de identificar possíveis repetições que pudessem comprometer a consistência da análise.

# %%
print("=== VERIFICAÇÃO DE DUPLICATAS ===")

duplicadas_total = df.duplicated().sum()
duplicadas_data = df.duplicated(subset=['Data']).sum()

print(f"Linhas totalmente duplicadas: {duplicadas_total}")
print(f"Datas duplicadas: {duplicadas_data}")

# %%
df.info()

# %% [markdown]
# 13- Verificação de Outliers

# %%
# %%
import matplotlib.pyplot as plt

plt.figure(figsize=(15, 4))
plt.plot(df['Data'], df[alvo])
plt.title(f'{alvo} ao longo do tempo (Verificação visual de Outliers)')
plt.show()

media = df[alvo].mean()
mediana = df[alvo].median()

print(f"Média de {alvo}: {media:.2f}")
print(f"Mediana de {alvo}: {mediana:.2f}")

print(f"--- 5 Dias de MAIOR tráfego ({alvo}) ---")
print(df.nlargest(5, alvo)[['Data', alvo, 'dia_semana']])

print(f"\n--- 5 Dias de MENOR tráfego ({alvo}) ---")
print(df.nsmallest(5, alvo)[['Data', alvo, 'dia_semana']])
desvio_padrao = df[alvo].std()
print(f"Desvio padrão de {alvo}: {desvio_padrao:.2f}")

# %% [markdown]
# 14- Gera a planilha final tratada 

# %%
df.to_csv("../dados/trafego_tratado.csv", index=False)


