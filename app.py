import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# Configuração da Página
# =========================
st.set_page_config(
    page_title="Dashboard de Salários na Área de Dados",
    layout="wide",
)

PLOTLY_TEMPLATE = "plotly_white"

# =========================
# Carregamento dos dados
# =========================
@st.cache_data(show_spinner=True)
def load_data() -> pd.DataFrame:
    url = "https://raw.githubusercontent.com/vqrca/dashboard_salarios_dados/refs/heads/main/dados-imersao-final.csv"
    df = pd.read_csv(url)
    return df

df = load_data()

# =========================
# Barra Lateral (Filtros)
# =========================
st.sidebar.header("Filtros")

anos_disponiveis = sorted(df["ano"].dropna().unique().tolist())
senioridades_disponiveis = sorted(df["senioridade"].dropna().unique().tolist())
contratos_disponiveis = sorted(df["contrato"].dropna().unique().tolist())
tamanhos_disponiveis = sorted(df["tamanho_empresa"].dropna().unique().tolist())

anos_selecionados = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)
senioridades_selecionadas = st.sidebar.multiselect("Senioridade", senioridades_disponiveis, default=senioridades_disponiveis)
contratos_selecionados = st.sidebar.multiselect("Tipo de contrato", contratos_disponiveis, default=contratos_disponiveis)
tamanhos_selecionados = st.sidebar.multiselect("Tamanho da empresa", tamanhos_disponiveis, default=tamanhos_disponiveis)

# =========================
# Filtragem do DataFrame
# =========================
df_filtrado = df[
    (df["ano"].isin(anos_selecionados)) &
    (df["senioridade"].isin(senioridades_selecionadas)) &
    (df["contrato"].isin(contratos_selecionados)) &
    (df["tamanho_empresa"].isin(tamanhos_selecionados))
].copy()

# =========================
# Conteúdo Principal
# =========================
st.title("Dashboard de Análise de Salários na Área de Dados")
st.markdown("Explore os dados salariais na área de dados nos últimos anos. Utilize os filtros à esquerda para refinar sua análise.")

# =========================
# Métricas (KPIs)
# =========================
st.subheader("Métricas gerais (salário anual em USD)")

if not df_filtrado.empty:
    salario_medio = float(df_filtrado["usd"].mean())
    salario_maximo = float(df_filtrado["usd"].max())
    total_registros = int(df_filtrado.shape[0])
    cargo_mais_frequente = (
        df_filtrado["cargo"].mode().iat[0]
        if "cargo" in df_filtrado.columns and not df_filtrado["cargo"].mode().empty
        else "N/D"
    )
else:
    salario_medio = 0.0
    salario_maximo = 0.0
    total_registros = 0
    cargo_mais_frequente = "N/D"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Salário médio", f"${salario_medio:,.0f}")
col2.metric("Salário máximo", f"${salario_maximo:,.0f}")
col3.metric("Total de registros", f"{total_registros:,}")
col4.metric("Cargo mais frequente", cargo_mais_frequente)

st.markdown("---")

# =========================
# Gráficos (originais)
# =========================
st.subheader("Gráficos")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado.groupby("cargo")["usd"]
            .mean()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )
        grafico_cargos = px.bar(
            top_cargos,
            x="usd",
            y="cargo",
            orientation="h",
            title="Top 10 cargos por salário médio",
            labels={"usd": "Média salarial anual (USD)", "cargo": ""},
            template=PLOTLY_TEMPLATE,
        )
        grafico_cargos.update_layout(title_x=0.05, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(grafico_cargos, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")

with col_graf2:
    if not df_filtrado.empty:
        grafico_hist = px.histogram(
            df_filtrado,
            x="usd",
            nbins=30,
            title="Distribuição de salários anuais",
            labels={"usd": "Faixa salarial (USD)"},
            template=PLOTLY_TEMPLATE,
        )
        grafico_hist.update_layout(title_x=0.05)
        st.plotly_chart(grafico_hist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de distribuição.")

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    if not df_filtrado.empty:
        remoto_contagem = df_filtrado["remoto"].value_counts(dropna=False).reset_index()
        remoto_contagem.columns = ["tipo_trabalho", "quantidade"]
        grafico_remoto = px.pie(
            remoto_contagem,
            names="tipo_trabalho",
            values="quantidade",
            title="Proporção dos tipos de trabalho",
            hole=0.5,
            template=PLOTLY_TEMPLATE,
        )
        grafico_remoto.update_traces(textinfo="percent+label")
        grafico_remoto.update_layout(title_x=0.05)
        st.plotly_chart(grafico_remoto, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico dos tipos de trabalho.")

with col_graf4:
    if not df_filtrado.empty:
        df_ds = df_filtrado[df_filtrado["cargo"] == "Data Scientist"].copy()
        if not df_ds.empty:
            media_ds_pais = df_ds.groupby("residencia_iso3")["usd"].mean().reset_index()
            grafico_paises = px.choropleth(
                media_ds_pais,
                locations="residencia_iso3",
                color="usd",
                color_continuous_scale="RdYlGn",
                title="Salário médio de Cientista de Dados por país",
                labels={"usd": "Salário médio (USD)", "residencia_iso3": "País"},
                template=PLOTLY_TEMPLATE,
            )
            grafico_paises.update_layout(title_x=0.05)
            st.plotly_chart(grafico_paises, use_container_width=True)
        else:
            st.info("Sem registros de 'Data Scientist' após os filtros.")
    else:
        st.warning("Nenhum dado para exibir no gráfico de países.")

# =========================
# Modelos adicionais (abas)
# =========================
st.markdown("---")
st.subheader("Modelos adicionais de gráficos")

if df_filtrado.empty:
    st.info("Nenhum dado com os filtros atuais para exibir nos modelos adicionais.")
else:
    aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
        "Boxplot por cargo (Top 10)",
        "Violino por senioridade",
        "Treemap país → cargo (média USD)",
        "Sunburst senioridade → contrato",
        "Heatmap senioridade × contrato (média USD)",
        "Linha por cargo ao longo do tempo (Top 5)",
        "Mapa animado por ano (cargo selecionável)"
    ])

    # Aba 1 — Boxplot por cargo (Top 10)
    with aba1:
        top10_cargos = (
            df_filtrado.groupby("cargo")["usd"].mean()
            .nlargest(10)
            .index.tolist()
        )
        df_box = df_filtrado[df_filtrado["cargo"].isin(top10_cargos)].copy()
        fig_box = px.box(
            df_box,
            x="cargo",
            y="usd",
            points="all",
            labels={"cargo": "Cargo", "usd": "Salário anual (USD)"},
            title="Distribuição salarial por cargo (Top 10 por média)",
            template=PLOTLY_TEMPLATE,
        )
        fig_box.update_layout(xaxis_title="", height=560, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_box, use_container_width=True)

    # Aba 2 — Violino por senioridade
    with aba2:
        fig_vio = px.violin(
            df_filtrado,
            x="senioridade",
            y="usd",
            box=True,
            points="all",
            labels={"senioridade": "Senioridade", "usd": "Salário anual (USD)"},
            title="Distribuição salarial por senioridade (violino + box)",
            template=PLOTLY_TEMPLATE,
        )
        fig_vio.update_layout(xaxis_title="", height=560, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_vio, use_container_width=True)

    # Aba 3 — Treemap país → cargo por média salarial
    with aba3:
        coluna_pais = "residencia" if "residencia" in df_filtrado.columns else "residencia_iso3"
        df_treemap = (
            df_filtrado
            .groupby([coluna_pais, "cargo"], as_index=False)["usd"]
            .mean()
            .rename(columns={"usd": "media_usd"})
        )
        fig_tree = px.treemap(
            df_treemap,
            path=[coluna_pais, "cargo"],
            values="media_usd",
            color="media_usd",
            color_continuous_scale="Viridis",
            title="Média salarial por país e cargo (treemap)",
            template=PLOTLY_TEMPLATE,
        )
        fig_tree.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=620)
        st.plotly_chart(fig_tree, use_container_width=True)

    # Aba 4 — Sunburst senioridade → contrato (contagem)
    with aba4:
        df_sun = (
            df_filtrado
            .groupby(["senioridade", "contrato"], as_index=False)
            .size()
            .rename(columns={"size": "qtd"})
        )
        fig_sun = px.sunburst(
            df_sun,
            path=["senioridade", "contrato"],
            values="qtd",
            color="qtd",
            color_continuous_scale="Blues",
            title="Distribuição de registros por senioridade e tipo de contrato",
            template=PLOTLY_TEMPLATE,
        )
        fig_sun.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=620)
        st.plotly_chart(fig_sun, use_container_width=True)

    # Aba 5 — Heatmap senioridade × contrato (média USD)
    with aba5:
        piv = (
            df_filtrado
            .groupby(["senioridade", "contrato"], as_index=False)["usd"]
            .mean()
            .pivot(index="senioridade", columns="contrato", values="usd")
        )
        fig_heat = px.imshow(
            piv,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale="RdYlGn",
            labels=dict(color="Média USD"),
            title="Média salarial por senioridade × tipo de contrato",
            template=PLOTLY_TEMPLATE,
        )
        fig_heat.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=560)
        st.plotly_chart(fig_heat, use_container_width=True)

    # Aba 6 — Linha por cargo ao longo do tempo (Top 5 por volume)
    with aba6:
        top5_cargos = (
            df_filtrado["cargo"].value_counts()
            .nlargest(5)
            .index.tolist()
        )
        df_linha = (
            df_filtrado[df_filtrado["cargo"].isin(top5_cargos)]
            .groupby(["ano", "cargo"], as_index=False)["usd"]
            .median()
        )
        fig_line = px.line(
            df_linha,
            x="ano",
            y="usd",
            color="cargo",
            markers=True,
            labels={"ano": "Ano", "usd": "Mediana salarial (USD)", "cargo": "Cargo"},
            title="Evolução da mediana salarial por cargo (Top 5 por quantidade de registros)",
            template=PLOTLY_TEMPLATE,
        )
        fig_line.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=560, legend_title_text="")
        st.plotly_chart(fig_line, use_container_width=True)

    # Aba 7 — Mapa animado por ano (cargo selecionável)
    with aba7:
        cargos_disp = sorted(df_filtrado["cargo"].dropna().unique().tolist())
        if not cargos_disp:
            st.warning("Não há cargos disponíveis após os filtros.")
        else:
            cargo_sel = st.selectbox("Selecione o cargo para animação no mapa", cargos_disp, index=0)
            df_anim = (
                df_filtrado[df_filtrado["cargo"] == cargo_sel]
                .groupby(["ano", "residencia_iso3"], as_index=False)["usd"]
                .mean()
                .rename(columns={"usd": "media_usd"})
                .sort_values(["ano", "residencia_iso3"])
            )
            if df_anim.empty:
                st.warning("Não há dados suficientes para o cargo selecionado.")
            else:
                fig_choro_anim = px.choropleth(
                    df_anim,
                    locations="residencia_iso3",
                    color="media_usd",
                    animation_frame="ano",
                    color_continuous_scale="Viridis",
                    labels={"media_usd": "Média salarial (USD)", "residencia_iso3": "País"},
                    title=f"Média salarial por país ao longo dos anos — {cargo_sel}",
                    template=PLOTLY_TEMPLATE,
                )
                fig_choro_anim.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=620)
                st.plotly_chart(fig_choro_anim, use_container_width=True)

# =========================
# Tabela
# =========================
st.markdown("---")
st.subheader("Dados detalhados")
st.dataframe(df_filtrado, use_container_width=True)
