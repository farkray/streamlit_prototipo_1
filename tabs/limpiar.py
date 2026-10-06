import pandas as pd
import streamlit as st

RANGOS_VALIDACION = {
    "edad": (0, 120),
    "ingreso_mensual": (0, None),
    "visitas_web_30d": (0, None),
    "productos_vistos_30d": (0, None),
    "carritos_30d": (0, None),
    "compras_12m": (0, None),
    "gasto_total_12m": (0, None),
    "campanas_recibidas_30d": (0, None),
    "emails_abiertos_30d": (0, None),
    "clics_campanas_30d": (0, None),
    "uso_cupon_12m": (0, None),
    "descuento_promedio": (0, 100),
    "abandono_carrito_30d": (0, None),
    "monto_ultima_compra": (0, None),
    "compro_ultima_campana": (0, 1),
}


def _mascara_fuera_de_rango(df: pd.DataFrame) -> pd.Series:
    mascara = pd.Series(False, index=df.index)
    for columna, (minimo, maximo) in RANGOS_VALIDACION.items():
        if columna not in df:
            continue
        valores = pd.to_numeric(df[columna], errors="coerce")
        fuera = valores.lt(minimo)
        if maximo is not None:
            fuera |= valores.gt(maximo)
        mascara |= fuera.fillna(False)
    return mascara


def _reporte_calidad(df: pd.DataFrame) -> pd.DataFrame:
    """Resume faltantes, duplicados e invalidaciones conocidas."""
    filas = []
    for columna in df.columns:
        filas.append(
            {
                "Variable": columna,
                "Tipo": str(df[columna].dtype),
                "Faltantes": int(df[columna].isna().sum()),
                "Valores únicos": int(df[columna].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(filas)


def mostrar(df: pd.DataFrame) -> None:
    st.header("2. Limpiar los datos")
    st.markdown(
        "Inspecciona primero los problemas y decide cada tratamiento. "
        "El archivo original permanece intacto; los cambios se aplican a "
        "una copia de trabajo y se pueden rehacer."
    )

    columnas_faltantes = [
        c for c in ["dias_desde_ultima_compra", "monto_ultima_compra"] if c in df
    ]
    if "df_limpio" not in st.session_state:
        st.session_state.df_limpio = df.copy()
        st.session_state.limpieza_acciones = ["Se creó una copia de trabajo sin cambios."]

    st.subheader("Diagnóstico antes del tratamiento")
    c1, c2, c3 = st.columns(3)
    c1.metric("Filas originales", f"{len(df):,}")
    c2.metric("Duplicados exactos", f"{int(df.duplicated().sum()):,}")
    c3.metric("Celdas faltantes", f"{int(df.isna().sum().sum()):,}")
    st.dataframe(_reporte_calidad(df), use_container_width=True, hide_index=True)

    st.subheader("Investigar faltantes de compras")
    if columnas_faltantes and "compras_12m" in df:
        sin_historial = df["compras_12m"].eq(0)
        filas_revision = []
        for columna in columnas_faltantes:
            faltan = df[columna].isna()
            filas_revision.append(
                {
                    "Variable": columna,
                    "Faltantes": int(faltan.sum()),
                    "Faltantes con compras_12m = 0": int((faltan & sin_historial).sum()),
                    "Faltantes con compras_12m > 0": int(
                        (faltan & df["compras_12m"].gt(0)).sum()
                    ),
                    "Porcentaje alineado a cero compras": (
                        100 * (faltan & sin_historial).sum() / faltan.sum()
                        if faltan.sum()
                        else 0.0
                    ),
                }
            )
        st.dataframe(
            pd.DataFrame(filas_revision).style.format(
                {"Porcentaje alineado a cero compras": "{:.1f}%"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "La coincidencia con cero compras aporta contexto, pero no prueba "
            "por sí sola que cada faltante signifique cero."
        )
    else:
        st.info("No se encontraron todas las columnas requeridas para esta revisión.")

    with st.expander("Revisar valores fuera de rangos esperados"):
        hallazgos = []
        for columna, (minimo, maximo) in RANGOS_VALIDACION.items():
            if columna not in df:
                continue
            valores = pd.to_numeric(df[columna], errors="coerce")
            fuera = valores.lt(minimo)
            if maximo is not None:
                fuera |= valores.gt(maximo)
            hallazgos.append(
                {"Variable": columna, "Rango esperado": f"{minimo} a {maximo or 'sin límite'}", "Fuera de rango": int(fuera.sum())}
            )
        st.dataframe(pd.DataFrame(hallazgos), use_container_width=True, hide_index=True)
        st.caption("Los extremos estadísticos no se eliminan automáticamente.")

    st.subheader("Aplicar decisiones a la copia de trabajo")
    with st.form("formulario_limpieza"):
        quitar_duplicados = st.checkbox(
            "Quitar filas duplicadas exactas", value=False, key="quitar_duplicados"
        )
        excluir_fuera_rango = st.checkbox(
            "Excluir filas con valores fuera de los rangos mostrados arriba",
            value=False,
            key="excluir_fuera_rango",
        )
        confirmar_rangos = st.checkbox(
            "Confirmo que los rangos indicados son válidos para este ejercicio.",
            value=False,
            key="confirmar_rangos",
        )
        reemplazar_sin_compra = st.checkbox(
            "Reemplazar faltantes de recencia y monto por 0 solo cuando compras_12m = 0",
            value=False,
            disabled=not (columnas_faltantes and "compras_12m" in df),
            key="reemplazar_sin_compra",
        )
        confirmar_semantica = st.checkbox(
            "Confirmo que en este ejercicio 'sin compra en 12 meses' se representa como 0 para estas dos variables.",
            value=False,
            key="confirmar_semantica_compras",
        )
        aplicar = st.form_submit_button("Aplicar limpieza seleccionada")

    if aplicar:
        limpio = df.copy()
        acciones = []
        if quitar_duplicados:
            antes = len(limpio)
            limpio = limpio.drop_duplicates().copy()
            acciones.append(f"Se quitaron {antes - len(limpio)} filas duplicadas exactas.")
        if excluir_fuera_rango and confirmar_rangos:
            mascara_rango = _mascara_fuera_de_rango(limpio)
            cantidad = int(mascara_rango.sum())
            limpio = limpio.loc[~mascara_rango].copy()
            acciones.append(f"Se excluyeron {cantidad} filas fuera de los rangos confirmados.")
        elif excluir_fuera_rango:
            st.warning("Confirma los rangos antes de excluir filas.")
        if reemplazar_sin_compra and confirmar_semantica:
            mascara = limpio["compras_12m"].eq(0)
            for columna in columnas_faltantes:
                cantidad = int((mascara & limpio[columna].isna()).sum())
                limpio.loc[mascara, columna] = limpio.loc[mascara, columna].fillna(0)
                acciones.append(
                    f"Se reemplazaron {cantidad} faltantes de {columna} por 0 donde compras_12m = 0."
                )
        elif reemplazar_sin_compra:
            st.warning("Confirma la semántica antes de aplicar el reemplazo.")
        if not acciones:
            acciones.append("No se hicieron cambios; se conservaron faltantes y duplicados.")
        st.session_state.df_limpio = limpio
        st.session_state.limpieza_acciones = acciones
        st.success("Se actualizó la copia de trabajo.")

    df_limpio = st.session_state.df_limpio
    st.subheader("Resultado y bitácora")
    c1, c2, c3 = st.columns(3)
    c1.metric("Filas de trabajo", f"{len(df_limpio):,}")
    c2.metric("Faltantes restantes", f"{int(df_limpio.isna().sum().sum()):,}")
    c3.metric("Duplicados restantes", f"{int(df_limpio.duplicated().sum()):,}")
    for accion in st.session_state.limpieza_acciones:
        st.write(f"- {accion}")

    csv = df_limpio.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar copia de trabajo (CSV)",
        data=csv,
        file_name="clientes_limpios.csv",
        mime="text/csv",
        key="descargar_limpieza",
    )
