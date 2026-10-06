import pandas as pd
import streamlit as st


def mostrar(df: pd.DataFrame) -> None:
    """Presenta una primera inspección sin transformar el dataset."""
    st.header("1. Entender los datos")
    st.markdown(
        "### Pregunta guía\n\n"
        "**¿Qué clientes muestran intención de compra y qué acción de "
        "marketing podríamos proponer para cada tipo de cliente?**\n\n"
        "Primero identifiquemos qué información tenemos y qué tan completa "
        "es. En esta etapa solo exploramos; todavía no limpiamos los datos "
        "ni recomendamos una campaña."
    )

    col_clientes, col_variables = st.columns(2)
    col_clientes.metric("Número de registros", f"{len(df):,}")
    col_variables.metric("Número de variables", f"{len(df.columns):,}")

    st.subheader("Vista previa del dataset")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    st.subheader("Diagnóstico del dataset")
    diagnostico = pd.DataFrame(
        {
            "Variable": df.columns,
            "Tipo de dato": df.dtypes.astype(str).to_numpy(),
            "Valores únicos": df.nunique(dropna=True).to_numpy(),
            "Valores faltantes": df.isna().sum().to_numpy(),
        }
    )
    st.dataframe(diagnostico, use_container_width=True, hide_index=True)
    st.caption(
        "Los valores faltantes se muestran para investigarlos; su presencia "
        "no significa automáticamente que deban eliminarse o reemplazarse."
    )

    st.subheader("Registros duplicados exactos")
    duplicados = int(df.duplicated().sum())
    st.metric("Filas duplicadas", f"{duplicados:,}")

    st.subheader("Explorar una variable")
    variable = st.selectbox(
        "Selecciona una variable:",
        options=df.columns.tolist(),
        key="variable_entender",
    )
    serie = df[variable]

    if pd.api.types.is_numeric_dtype(serie):
        st.write("**Tipo:** variable numérica")
        st.dataframe(
            serie.describe().to_frame(name="Estadístico"),
            use_container_width=True,
        )
        st.metric("Valores faltantes en esta variable", f"{serie.isna().sum():,}")
    else:
        st.write("**Tipo:** variable categórica o de texto")
        frecuencias = (
            serie.value_counts(dropna=False)
            .rename_axis("Valor")
            .rename("Frecuencia")
            .reset_index()
        )
        frecuencias["Valor"] = frecuencias["Valor"].where(
            frecuencias["Valor"].notna(), "(sin dato)"
        )
        st.dataframe(frecuencias, use_container_width=True, hide_index=True)
