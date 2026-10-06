import math

import pandas as pd
import streamlit as st


COLUMNAS_EXCLUIDAS = {
    "cliente_id",
    "compro_ultima_campana",
    "campanas_recibidas_30d",
    "emails_abiertos_30d",
    "clics_campanas_30d",
    "fecha_alta",
}


@st.cache_resource(show_spinner="Preparando el ejercicio con datos históricos...")
def _entrenar_evaluar(df: pd.DataFrame):
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    objetivo = pd.to_numeric(df["compro_ultima_campana"], errors="coerce")
    datos = df.loc[objetivo.isin([0, 1])].copy()
    y = objetivo.loc[datos.index].astype(int)
    columnas = [columna for columna in datos.columns if columna not in COLUMNAS_EXCLUIDAS]
    X = datos[columnas]
    numericas = X.select_dtypes(include="number").columns.tolist()
    categoricas = [columna for columna in X.columns if columna not in numericas]

    transformadores = []
    if numericas:
        transformadores.append(
            (
                "numericas",
                Pipeline([("completar", SimpleImputer(strategy="median", add_indicator=True))]),
                numericas,
            )
        )
    if categoricas:
        transformadores.append(
            (
                "categoricas",
                Pipeline(
                    [
                        ("completar", SimpleImputer(strategy="constant", fill_value="(sin dato)")),
                        ("codificar", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categoricas,
            )
        )

    preparar = ColumnTransformer(transformadores, remainder="drop")
    modelo = RandomForestClassifier(
        n_estimators=250,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    pipeline = Pipeline([("preparar", preparar), ("modelo", modelo)])
    X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipeline.fit(X_entrenamiento, y_entrenamiento)
    probabilidades = pipeline.predict_proba(X_prueba)[:, 1]
    prueba = pd.DataFrame(
        {"resultado_real": y_prueba.to_numpy(), "probabilidad": probabilidades},
        index=X_prueba.index,
    )
    return {
        "prueba": prueba.reset_index(drop=True),
        "clientes_entrenamiento": len(X_entrenamiento),
        "variables": columnas,
        "tasa_compra_total": float(y.mean()),
    }


def _porcentaje(valor: float) -> str:
    return f"{valor:.0%}" if pd.notna(valor) else "N/D"


def mostrar(df: pd.DataFrame) -> None:
    st.header("4. Predicción: a quién priorizar para una revisión")
    st.markdown(
        "Este ejercicio busca reconocer señales parecidas a las de clientes que compraron "
        "en la última campaña. Sirve para aprender a evaluar una priorización; no confirma "
        "quién comprará en la próxima campaña."
    )

    if df.empty:
        st.warning("No hay registros para analizar.")
        return
    if "compro_ultima_campana" not in df:
        st.error("Falta el dato que indica si cada cliente compró en la última campaña.")
        return

    objetivo = pd.to_numeric(df["compro_ultima_campana"], errors="coerce")
    clases = set(objetivo.dropna().unique())
    if not clases.issubset({0, 1}) or clases != {0, 1}:
        st.error("Para hacer este ejercicio, el resultado de campaña debe tener clientes que compraron y que no compraron (0/1).")
        return
    if int(objetivo.value_counts().min()) < 2:
        st.error("Se necesitan al menos dos clientes de cada tipo para separar datos de práctica y evaluación.")
        return

    st.info(
        "**Importante:** la evaluación usa una parte de clientes históricos cuyo resultado ya conocemos. "
        "No es una lista de personas para contactar. Antes de aplicar un modelo a una campaña futura, "
        "habría que validar datos disponibles, permisos de contacto y resultados en una prueba real."
    )

    try:
        resultado = _entrenar_evaluar(df)
    except ModuleNotFoundError:
        st.error("Falta scikit-learn. Instala las dependencias del proyecto para usar esta sección.")
        return
    except ValueError as error:
        st.error(f"No se pudo preparar la evaluación con estos datos: {error}")
        return

    prueba = resultado["prueba"].copy()
    capacidad = st.slider(
        "¿Qué porcentaje de la muestra histórica evaluada podría revisar el equipo?",
        min_value=10,
        max_value=50,
        value=25,
        step=5,
        format="%d%%",
        help="El modelo ordena los registros por su score y toma ese porcentaje superior. Es una capacidad de revisión para el ejercicio, no un umbral de compra.",
        key="capacidad_revision_predictiva",
    )

    total = len(prueba)
    cantidad_priorizada = max(1, min(total, math.ceil(total * capacidad / 100)))
    orden = prueba["probabilidad"].sort_values(ascending=False).index
    prueba["priorizado"] = False
    prueba.loc[orden[:cantidad_priorizada], "priorizado"] = True
    prueba["compro"] = prueba["resultado_real"].eq(1)

    priorizados = prueba[prueba["priorizado"]]
    resto = prueba[~prueba["priorizado"]]
    compradores_totales = int(prueba["compro"].sum())
    compradores_priorizados = int(priorizados["compro"].sum())
    no_compradores_priorizados = int((~priorizados["compro"]).sum())
    compradores_fuera = int(resto["compro"].sum())
    tasa_priorizados = float(priorizados["compro"].mean()) if len(priorizados) else 0.0
    tasa_general = float(prueba["compro"].mean()) if total else 0.0
    cobertura_compradores = compradores_priorizados / compradores_totales if compradores_totales else float("nan")
    comparacion = tasa_priorizados / tasa_general if tasa_general > 0 else float("nan")

    st.subheader("¿Qué habría pasado en el grupo evaluado?")
    k1, k2, k3 = st.columns(3)
    k1.metric(
        "Clientes en el grupo de revisión",
        f"{cantidad_priorizada:,} de {total:,}",
        help=f"Es el {capacidad}% de clientes con score más alto dentro de la muestra histórica de prueba.",
    )
    k2.metric(
        "Compraron dentro del grupo",
        f"{compradores_priorizados:,} ({_porcentaje(tasa_priorizados)})",
        help="Cantidad y proporción que realmente compró en la última campaña, entre los clientes priorizados.",
    )
    k3.metric(
        "Compradores detectados",
        _porcentaje(cobertura_compradores),
        help="Porcentaje de quienes compraron en la muestra histórica de prueba que quedaron dentro del grupo para revisar.",
    )

    st.caption(
        f"Se revisa el {capacidad}% con los scores más altos. Eso define el tamaño del grupo; "
        "no significa que ese porcentaje vaya a comprar."
    )

    st.markdown("#### Lectura para marketing")
    if pd.notna(comparacion) and comparacion > 1:
        st.write(
            f"En esta evaluación histórica, el grupo priorizado tuvo una proporción de compra "
            f"{comparacion:.1f} veces la del conjunto completo ({_porcentaje(tasa_priorizados)} "
            f"frente a {_porcentaje(tasa_general)}). De las {cantidad_priorizada:,} personas "
            f"que se revisarían, {no_compradores_priorizados:,} no compraron en esa campaña."
        )
    else:
        st.write(
            f"En esta evaluación, priorizar este grupo no concentró más compras que el promedio "
            f"del conjunto ({_porcentaje(tasa_priorizados)} frente a {_porcentaje(tasa_general)}). "
            "No hay evidencia aquí para recomendar que se use como filtro de campaña."
        )

    resumen = pd.DataFrame(
        {
            "Grupo de clientes": [f"Para revisar (mejores {capacidad}%)", "Resto de la muestra"],
            "Clientes": [len(priorizados), len(resto)],
            "Compraron": [compradores_priorizados, compradores_fuera],
            "Tasa de compra histórica": [
                float(priorizados["compro"].mean()) if len(priorizados) else 0.0,
                float(resto["compro"].mean()) if len(resto) else 0.0,
            ],
        }
    )
    st.subheader("Comparación simple: ¿dónde se concentraron más compradores?")
    grafica = resumen.set_index("Grupo de clientes")[["Tasa de compra histórica"]].mul(100)
    grafica = grafica.rename(columns={"Tasa de compra histórica": "Clientes que compraron (%)"})
    st.bar_chart(grafica)
    resumen_legible = resumen.copy()
    resumen_legible["Tasa de compra histórica"] = resumen_legible["Tasa de compra histórica"].map(_porcentaje)
    st.dataframe(resumen_legible, use_container_width=True, hide_index=True)
    st.caption(
        f"También quedaron {compradores_fuera:,} compradores fuera del grupo para revisar. "
        "Por eso, una priorización puede dejar oportunidades sin detectar. La tasa es descriptiva: "
        "no demuestra que contactar al grupo causaría más ventas."
    )

    with st.expander("Cómo se hizo esta evaluación"):
        st.markdown(
            f"- Se separó el **25%** de los registros ({total:,}) para comprobar el resultado; "
            f"el resto ({resultado['clientes_entrenamiento']:,}) se usó para aprender patrones.\n"
            "- Para evitar usar información posterior al momento de decisión, se excluyeron el "
            "identificador, la fecha de alta y las métricas de campañas, aperturas y clics de los "
            "últimos 30 días. Aun así, hay que confirmar cuándo se registraron las demás variables.\n"
            f"- La proporción de compra en el grupo completo fue **{_porcentaje(tasa_general)}**. "
            "La columna ‘Proporción que compró’ facilita compararla con el grupo priorizado.\n"
            "- El score solo ordena registros para este ejercicio. No es una probabilidad calibrada "
            "de compra, no demuestra que una campaña cause compras y no valida resultados futuros.\n"
            "- Los datos son sintéticos y la evaluación es aleatoria, no temporal. Valida el modelo "
            "con resultados reales y una prueba con grupo de control antes de tomar decisiones."
        )
        nombres = ", ".join(resultado["variables"])
        st.caption(f"Señales consideradas por el ejercicio: {nombres}.")
