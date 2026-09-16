# Dashboard EPTRAN

Dashboard interativo (Streamlit) para monitoramento dos programas
socioeducativos e atendimentos da EPTRAN, com Sankey, mapa coroplético por
bairro, evolução temporal, Top 15 bairros e modo kiosk (rotação automática
a cada 15s entre as 3 telas).

## Estrutura do projeto

```
app.py                       # ponto de entrada (streamlit run app.py)
config.py                    # todas as configurações (planilha, cores, regras)
data_loader.py                # leitura da planilha (Google Sheets ou .ods local)
data_processing.py           # limpeza, tipagem e regras de negócio
geo_utils.py                  # normalização de nomes de bairro + geojson
charts.py                     # gráficos (Sankey, mapa, evolução, Top 15)
ui.py                         # filtros, cards de KPI, barra de navegação
bairros.geojson               # malha geográfica dos bairros
logo.png                      # logo exibida na barra lateral (adicione o seu)
dados_locais_teste.ods        # cópia local da planilha, só para testes
requirements.txt
.streamlit/config.toml        # tema visual
.streamlit/secrets.toml.example
```

## 1. Testar agora, sem configurar nada (modo local)

Por padrão o projeto está configurado para ler a planilha online. Para
testar rapidamente com o arquivo `.ods` que você já tinha, sem precisar
criar credenciais do Google ainda:

1. Abra `config.py` e mude:
   ```python
   DATA_SOURCE = "local_ods"
   ```
2. Instale as dependências e rode:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

Quando quiser passar a usar a planilha online de verdade, volte
`DATA_SOURCE` para `"google_sheets"` e siga o passo 2 abaixo.

## 2. Configurar acesso à planilha online (conta de serviço do Google)

Como a planilha é privada, o dashboard acessa os dados por uma **conta de
serviço** do Google Cloud (sem precisar deixar a planilha pública).

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) e
   crie um projeto (ou use um existente).
2. Em "APIs e Serviços" → "Biblioteca", ative:
   - **Google Sheets API**
   - **Google Drive API**
3. Em "APIs e Serviços" → "Credenciais" → "Criar Credenciais" →
   "Conta de serviço". Dê um nome (ex.: `dashboard-eptran`) e conclua.
4. Abra a conta de serviço criada → aba "Chaves" → "Adicionar chave" →
   "Criar nova chave" → formato **JSON**. Um arquivo `.json` será
   baixado — guarde-o com cuidado, ele dá acesso de leitura à planilha.
5. Copie o e-mail da conta de serviço (campo `client_email` do JSON,
   algo como `dashboard-eptran@seu-projeto.iam.gserviceaccount.com`).
6. Na planilha do Google Sheets, clique em "Compartilhar" e adicione
   esse e-mail com permissão de **Leitor (Viewer)**.
7. Preencha o arquivo `.streamlit/secrets.toml.example` com os dados do
   JSON baixado e salve como `.streamlit/secrets.toml` (esse arquivo
   nunca deve ir para o GitHub — já está no `.gitignore`).

Depois disso, com `DATA_SOURCE = "google_sheets"` em `config.py`, rode
`streamlit run app.py` normalmente.

## 3. Deploy no Streamlit Community Cloud

1. Crie um repositório no GitHub e envie todos os arquivos deste projeto
   **exceto** `.streamlit/secrets.toml` (ele não deve ir para o Git).
2. Acesse [share.streamlit.io](https://share.streamlit.io), conecte sua
   conta do GitHub e escolha o repositório, com `app.py` como arquivo
   principal.
3. Antes (ou depois) de publicar, vá em "Settings" → "Secrets" do app no
   Streamlit Cloud e cole o mesmo conteúdo do seu
   `.streamlit/secrets.toml` (o bloco `[gcp_service_account]`).
4. Publique. O app vai instalar o `requirements.txt` automaticamente.

## Decisões de negócio aplicadas no processamento dos dados

Essas regras foram confirmadas durante o desenvolvimento e estão
implementadas em `data_processing.py` / `geo_utils.py` / `config.py`:

- **Linhas em branco/rodapé de totalização** de cada aba (sem "Programa"
  preenchido) são descartadas automaticamente.
- **Data**: a coluna "Data" da aba de 2022 vem quebrada na planilha
  (`#VALUE!`); por isso a data de **todas** as abas é reconstruída a
  partir de Dia + Mês + ano da aba (mais robusto e consistente).
- **Bairros que não existem no `bairros.geojson`** (ex.: "Garuva", que é
  outro município; "Distrito Industrial", "Palmeiras", "Morro do
  Amaral", "Zona Rural", entre outros) continuam entrando nos totais
  gerais e nos filtros, mas ficam de fora do mapa e do Top 15 bairros,
  agrupados como **"Não mapeado"**.
- **Erros de digitação claros** (ex.: "Aventreiro" → "Aventureiro",
  "Cubatão" → "Vila Cubatão") são corrigidos automaticamente — a lista
  completa está em `config.BAIRRO_CORRECOES`, editável a qualquer
  momento se aparecerem novos casos.
- **Linhas que citam mais de um bairro** na mesma célula (ex.: "Fátima;
  Glória") têm o valor **dividido igualmente** entre os bairros citados
  — mas só para o mapa e o Top 15; nos demais indicadores (KPIs, Sankey,
  evolução temporal) a linha conta inteira uma única vez, e o filtro de
  bairro reconhece a linha se qualquer um dos bairros citados estiver
  selecionado.
- O switch global **"Pessoas Impactadas" × "Programas"** controla a
  coluna interna `peso` (soma de "Total - Dia" ou contagem de linhas,
  respectivamente), usada de forma consistente em todos os gráficos e
  cards.

## Ajustes de layout e cores (última atualização)

- **Logo**: a barra lateral agora mostra `logo.png` (coloque o arquivo na
  raiz do repositório, junto de `app.py`). Se o arquivo não existir, o
  app cai de volta automaticamente para o título em texto, sem quebrar.
- **Filtros compactos**: Bairro, Programa e Ação agora são um botão
  (popover) que só abre a lista ao ser clicado, mostrando só a contagem
  de itens selecionados quando fechado (ex.: "Bairro · 3 selecionado(s)").
  Deixar um filtro **sem nenhum item marcado equivale a "todos"** — não
  precisa marcar tudo manualmente.
- **Menos rolagem**: o cabeçalho e o menu padrão do Streamlit foram
  ocultados (CSS em `ui.aplicar_estilo()`), e as alturas dos gráficos
  ficaram fixas em `config.py` (`ALTURA_SANKEY`, `ALTURA_MAPA`,
  `ALTURA_GRAFICO_SECUNDARIO`). Se ainda sobrar ou faltar espaço no seu
  monitor/TV, ajuste só esses três números — não precisa mexer em
  `charts.py`.
  - **Atenção**: como o cabeçalho do Streamlit ficou oculto, o botão
    "Manage app" não aparece mais dentro do próprio dashboard. Para ver
    logs ou gerenciar o app, acesse [share.streamlit.io](https://share.streamlit.io)
    diretamente. Para reverter isso, basta remover o bloco
    `header[data-testid="stHeader"]` do CSS em `ui.py`.
- **Cores dos gráficos**: Sankey, evolução mensal e Top 15 bairros agora
  usam a escala azul petróleo (`config.ESCALA_AZUL_PETROLEO`) em vez de
  uma cor única — quanto maior o valor, mais escuro/intenso o azul.

## Observações técnicas

- A biblioteca `streamlit-autorun` citada na especificação original não
  existe no PyPI; foi usada `streamlit-autorefresh`, que cumpre o mesmo
  papel (recarregar a tela automaticamente a cada 15 segundos).
- O mapa usa `plotly.express.choropleth_mapbox` com o estilo de base
  gratuito `carto-positron` (não precisa de token do Mapbox).
- Fase 2 do documento (empacotamento como executável desktop com
  PyInstaller/PyStand) foi marcada como "futurológica" na própria
  especificação e não foi implementada nesta entrega — o foco é a Fase 1
  (aplicação web via Streamlit).
