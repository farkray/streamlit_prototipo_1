import pandas as pd
import streamlit as st


def _num(df: pd.DataFrame, columna: str, predeterminado: float = 0) -> pd.Series:
    if columna not in df:
        return pd.Series(predeterminado, index=df.index, dtype="float64")
    return pd.to_numeric(df[columna], errors="coerce")


def construir_recomendaciones(
    df: pd.DataFrame, dias_reactivacion: int = 90, percentil_intencion: int = 75,
    canal: str = "Email (validar consentimiento)",
) -> pd.DataFrame:
    """Aplica reglas transparentes y mutuamente excluyentes a una copia."""
    resultado = df.copy()
    compras = _num(resultado, "compras_12m")
    recencia = _num(resultado, "dias_desde_ultima_compra", float("nan"))
    carritos = _num(resultado, "carritos_30d")
    abandonos = _num(resultado, "abandono_carrito_30d")
    visitas = _num(resultado, "visitas_web_30d")
    productos = _num(resultado, "productos_vistos_30d")

    umbral_visitas = visitas.quantile(percentil_intencion / 100) if visitas.notna().any() else 0
    umbral_productos = productos.quantile(percentil_intencion / 100) if productos.notna().any() else 0
    es_carrito = carritos.gt(0) & abandonos.gt(0)
    es_reactivar = (~es_carrito) & compras.gt(0) & recencia.ge(dias_reactivacion)
    es_revision = (~es_carrito) & compras.gt(0) & recencia.isna()
    es_intencion = (
        (~es_carrito) & (~es_reactivar) & (~es_revision)
        & visitas.ge(umbral_visitas) & productos.ge(umbral_productos)
    )

    segmento = pd.Series("Nutrir y medir", index=resultado.index, dtype="object")
    segmento.loc[es_carrito] = "Recuperar carrito"
    segmento.loc[es_reactivar] = "Reactivar comprador"
    segmento.loc[es_revision] = "Revisar recencia"
    segmento.loc[es_intencion] = "Explorar categoría"

    evidencia = pd.Series("Sin señal reciente suficiente; probar contenido general y medir.", index=resultado.index)
    evidencia.loc[es_carrito] = "Tiene carrito y al menos un abandono registrado en 30 días."
    evidencia.loc[es_reactivar] = f"Compró en 12 meses y su recencia es de al menos {dias_reactivacion} días."
    evidencia.loc[es_revision] = "Tiene compras registradas, pero la recencia está vacía; revisar el dato."
    evidencia.loc[es_intencion] = (
        f"Visitas y productos vistos están en o sobre el percentil {percentil_intencion} "
        "del conjunto."
    )

    accion = pd.Series("Enviar contenido de valor y medir respuesta.", index=resultado.index)
    accion.loc[es_carrito] = "Recordatorio de carrito; no incluir precio ni descuento no disponibles."
    accion.loc[es_reactivar] = "Invitar a volver a explorar la categoría preferida."
    accion.loc[es_revision] = "No automatizar reactivación hasta validar la recencia."
    accion.loc[es_intencion] = "Mostrar productos de la categoría preferida y facilitar exploración."

    categoria = (
        resultado["categoria_preferida"].fillna("tu categoría de interés").astype(str)
        if "categoria_preferida" in resultado
        else pd.Series("tu categoría de interés", index=resultado.index)
    )
    cliente = (
        resultado["cliente_id"].fillna("cliente").astype(str)
        if "cliente_id" in resultado
        else pd.Series("cliente", index=resultado.index)
    )
    mensaje = pd.Series(
        "Hola. Explora las novedades de " + categoria + " y encuentra opciones que te interesen.",
        index=resultado.index,
    )
    mensaje.loc[es_carrito] = "Hola. Puedes retomar tu carrito cuando quieras. Revisa los artículos antes de continuar."
    mensaje.loc[es_revision] = "Hola. Descubre las novedades de " + categoria + " cuando tengas un momento."

    resultado["segmento_recomendado"] = segmento
    resultado["evidencia_regla"] = evidencia
    resultado["accion_recomendada"] = accion
    resultado["canal_a_validar"] = canal
    resultado["mensaje_borrador"] = mensaje
    resultado["responsable_sugerido"] = "Marketing CRM"
    resultado["siguiente_paso"] = "Validar consentimiento, exclusiones y frecuencia; ejecutar prueba con grupo de control."
    resultado["riesgo_medicion"] = "Regla heurística; medir conversión incremental frente a un grupo de control."
    resultado["cliente_id"] = cliente
    return resultado


def mostrar(df: pd.DataFrame) -> None:
    st.header("5. Estadística prescriptiva")
    st.markdown(
        "Convierte señales observables en reglas explicables. Estas reglas "
        "organizan pruebas de marketing; no predicen causalidad ni sustituyen "
        "la validación de consentimiento y frecuencia de contacto."
    )
    if df.empty:
        st.warning("No hay clientes para segmentar.")
        return

    valores_recencia = pd.to_numeric(
        df.get("dias_desde_ultima_compra", pd.Series(dtype=float)), errors="coerce"
    ).dropna()
    max_recencia = max(60, min(365, int(valores_recencia.max()) if not valores_recencia.empty else 180))
    a, b, c = st.columns(3)
    dias = a.slider("Antigüedad para reactivación (días)", 30, max_recencia, min(90, max_recencia), 15, key="dias_reactivacion")
    percentil = b.slider("Percentil mínimo de intención digital", 50, 90, 75, 5, key="percentil_intencion")
    canal = c.selectbox("Canal candidato (validar permiso)", ["Email (validar consentimiento)", "Sitio web / espacio propio", "Otro canal autorizado"], key="canal_prescriptiva")

    recomendaciones = construir_recomendaciones(df, dias, percentil, canal)
    st.session_state.recomendaciones = recomendaciones
    st.session_state.parametros_prescriptiva = {
        "dias_reactivacion": dias,
        "percentil_intencion": percentil,
        "canal": canal,
    }

    conteos = (
        recomendaciones["segmento_recomendado"].value_counts()
        .rename_axis("Segmento").rename("Clientes").reset_index()
    )
    st.subheader("Tamaño de cada grupo")
    st.bar_chart(conteos.set_index("Segmento"))
    st.dataframe(conteos, use_container_width=True, hide_index=True)

    st.subheader("Reglas aplicadas (prioridad de arriba hacia abajo)")
    st.dataframe(pd.DataFrame([
        {"Prioridad": 1, "Regla": "Carritos > 0 y abandonos > 0", "Acción": "Recordatorio de carrito"},
        {"Prioridad": 2, "Regla": f"Compras > 0 y recencia ≥ {dias} días", "Acción": "Reactivación"},
        {"Prioridad": 3, "Regla": "Compras > 0 y recencia faltante", "Acción": "Revisión manual del dato"},
        {"Prioridad": 4, "Regla": f"Visitas y productos vistos ≥ percentil {percentil}", "Acción": "Explorar categoría preferida"},
        {"Prioridad": 5, "Regla": "Resto de clientes", "Acción": "Nutrir y medir"},
    ]), use_container_width=True, hide_index=True)

    st.subheader("Muestra de recomendaciones")
    segmento = st.selectbox("Ver segmento", conteos["Segmento"].tolist(), key="segmento_muestra_prescriptiva")
    muestra = recomendaciones.loc[
        recomendaciones["segmento_recomendado"].eq(segmento),
        ["cliente_id", "segmento_recomendado", "evidencia_regla", "accion_recomendada", "mensaje_borrador", "responsable_sugerido", "siguiente_paso", "riesgo_medicion"],
    ].head(25)
    st.dataframe(muestra, use_container_width=True, hide_index=True)
    st.caption("Los mensajes no prometen descuentos, urgencia ni beneficios que el dataset no documenta.")
