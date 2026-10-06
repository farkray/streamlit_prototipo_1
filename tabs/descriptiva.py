import pandas as pd
import streamlit as st


def _numero(df: pd.DataFrame, columna: str) -> pd.Series:
    if columna not in df:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[columna], errors="coerce")


def _tasa(numerador: float, denominador: float) -> str:
    return f"{numerador / denominador:.1%}" if denominador > 0 else "N/D"


def mostrar(df: pd.DataFrame) -> None:
    st.header("3. Estadística descriptiva")
    st.markdown(
        "Resume lo observado en el conjunto actual. Las tasas muestran su "
        "denominador y describen asociaciones; no explican causalidad."
    )

    if df.empty:
        st.warning("No hay registros para resumir.")
        return

    compras = _numero(df, "compras_12m").fillna(0)
    gasto = _numero(df, "gasto_total_12m").fillna(0)
    compradores = compras.gt(0)
    compradores_campana = _numero(df, "compro_ultima_campana")
    clientes = len(df)
    ingresos = _numero(df, "ingreso_mensual")
    gasto_positivo = gasto.where(gasto.ge(0), 0)
    ordenes_validas = compras.gt(0) & gasto.ge(0)
    valor_orden = (
        gasto[ordenes_validas].sum() / compras[ordenes_validas].sum()
        if compras[ordenes_validas].sum() > 0
        else float("nan")
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clientes", f"{clientes:,}")
    m2.metric(
        "Compradores 12 meses",
        f"{int(compradores.sum()):,} ({_tasa(compradores.sum(), clientes)} de clientes)",
    )
    m3.metric(
        "Compra en última campaña",
        _tasa(compradores_campana.eq(1).sum(), compradores_campana.isin([0, 1]).sum()),
    )
    m4.metric("Ingreso mensual promedio", f"${ingresos.mean():,.0f}" if ingresos.notna().any() else "N/D")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Gasto acumulado 12 meses", f"${gasto_positivo.sum():,.0f}")
    m6.metric("Gasto por cliente", f"${gasto_positivo.sum() / clientes:,.0f}" if clientes else "N/D")
    m7.metric("Valor promedio por compra", f"${valor_orden:,.0f}" if pd.notna(valor_orden) else "N/D")
    m8.metric("Compras por comprador", f"{compras[compradores].mean():.2f}" if compradores.any() else "N/D")

    st.subheader("Interacción con campañas")
    recibidas = _numero(df, "campanas_recibidas_30d")
    abiertas = _numero(df, "emails_abiertos_30d")
    clics = _numero(df, "clics_campanas_30d")
    validos_email = recibidas.gt(0) & abiertas.ge(0) & abiertas.le(recibidas)
    validos_clic = recibidas.gt(0) & clics.ge(0) & clics.le(recibidas)
    total_recibidas_abiertas = recibidas[validos_email].sum()
    total_recibidas_clic = recibidas[validos_clic].sum()
    tasa_apertura = (
        abiertas[validos_email].sum() / total_recibidas_abiertas
        if total_recibidas_abiertas > 0 else float("nan")
    )
    tasa_clic = (
        clics[validos_clic].sum() / total_recibidas_clic
        if total_recibidas_clic > 0 else float("nan")
    )
    carritos = _numero(df, "carritos_30d")
    abandonos = _numero(df, "abandono_carrito_30d")
    validos_carrito = carritos.gt(0) & abandonos.ge(0) & abandonos.le(carritos)
    tasa_abandono = (
        abandonos[validos_carrito].sum() / carritos[validos_carrito].sum()
        if carritos[validos_carrito].sum() > 0 else float("nan")
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Aperturas / campañas recibidas", f"{tasa_apertura:.1%}" if pd.notna(tasa_apertura) else "N/D")
    c2.metric("Clics / campañas recibidas", f"{tasa_clic:.1%}" if pd.notna(tasa_clic) else "N/D")
    c3.metric("Carritos abandonados / carritos", f"{tasa_abandono:.1%}" if pd.notna(tasa_abandono) else "N/D")
    st.caption(
        "Las tasas de apertura y clic usan la suma de eventos dividida entre "
        "campañas recibidas en registros con numeradores dentro de rango. "
        "Abandono usa eventos abandonados entre carritos en registros válidos. "
        "Valida estas definiciones con el diccionario del negocio."
    )

    st.subheader("Distribución por categoría")
    if "categoria_preferida" in df:
        categorias = (
            df["categoria_preferida"].fillna("(sin dato)")
            .value_counts().rename_axis("Categoría").rename("Clientes").reset_index()
        )
        st.bar_chart(categorias.set_index("Categoría"))
        st.dataframe(categorias, use_container_width=True, hide_index=True)
    else:
        st.info("El dataset no contiene `categoria_preferida`.")

    st.subheader("Exploración segmentada")
    opciones = [c for c in ["genero", "ciudad", "canal_origen", "categoria_preferida"] if c in df]
    if opciones:
        grupo = st.selectbox("Agrupar por", opciones, key="grupo_descriptiva")
        temporal = df[[grupo]].copy()
        temporal["compras_12m"] = compras
        temporal["gasto_total_12m"] = gasto
        temporal["compro_ultima_campana"] = compradores_campana
        resumen = temporal.groupby(grupo, dropna=False).agg(
            clientes=(grupo, "size"),
            compradores_12m=("compras_12m", lambda x: int(x.gt(0).sum())),
            gasto_total=("gasto_total_12m", "sum"),
            compras_ultima_campana=("compro_ultima_campana", "mean"),
        ).reset_index()
        resumen["conversion_ultima_campana"] = resumen["compras_ultima_campana"].map(
            lambda x: f"{x:.1%}" if pd.notna(x) else "N/D"
        )
        st.dataframe(
            resumen.drop(columns="compras_ultima_campana").style.format({"gasto_total": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("La conversión agrupada es descriptiva y no demuestra que el grupo cause la compra.")
