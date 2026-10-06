import pandas as pd
import streamlit as st


def _formato_tasa(valores: pd.Series) -> str:
    tasa = pd.to_numeric(valores, errors="coerce").mean()
    return f"{tasa:.1%}" if pd.notna(tasa) else "N/D"


def _crear_plan(segmento: pd.DataFrame, porcentaje_piloto: int, porcentaje_control: int) -> pd.DataFrame:
    """Selecciona un piloto reproducible y separa control de tratamiento."""
    if segmento.empty:
        return segmento.copy()
    n_piloto = max(1, round(len(segmento) * porcentaje_piloto / 100))
    piloto = segmento.sample(n=n_piloto, random_state=42).copy()
    n_control = (
        min(len(piloto) - 1, max(1, round(len(piloto) * porcentaje_control / 100)))
        if len(piloto) >= 2
        else 0
    )
    grupos = pd.Series("Tratamiento", index=piloto.index)
    if n_control:
        indices_control = piloto.sample(n=n_control, random_state=43).index
        grupos.loc[indices_control] = "Control (sin mensaje)"
    piloto["grupo_experimento"] = grupos
    piloto["kpi_primario"] = "Tasa de compra posterior al envío vs. grupo de control"
    piloto["ventana_medicion"] = "Definir antes del lanzamiento; aplicar igual a ambos grupos"
    return piloto


def mostrar(df: pd.DataFrame) -> None:
    st.header("6. Toma de decisiones")
    st.markdown(
        "Conecta un KPI, un grupo, la evidencia, una acción y un plan de "
        "medición. Esta pantalla prepara una propuesta revisable; no envía mensajes."
    )

    recomendaciones = st.session_state.get("recomendaciones")
    if recomendaciones is None or recomendaciones.empty:
        st.info("No hay recomendaciones aún. Revisa primero la pestaña Prescriptiva.")
        return

    objetivo = "compro_ultima_campana"
    filas = []
    for nombre, grupo in recomendaciones.groupby("segmento_recomendado", dropna=False):
        fila = {
            "Segmento": nombre,
            "Clientes": len(grupo),
            "Participación": len(grupo) / len(recomendaciones),
            "Acción": grupo["accion_recomendada"].mode().iat[0],
            "Evidencia ejemplo": grupo["evidencia_regla"].iat[0],
            "Responsable": grupo["responsable_sugerido"].iat[0],
            "Riesgo / medición": grupo["riesgo_medicion"].iat[0],
        }
        if objetivo in grupo:
            observado = pd.to_numeric(grupo[objetivo], errors="coerce")
            fila["Compra histórica última campaña"] = _formato_tasa(observado)
        filas.append(fila)
    resumen = pd.DataFrame(filas).sort_values("Clientes", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes en análisis", f"{len(recomendaciones):,}")
    c2.metric("Grupos de acción", f"{recomendaciones['segmento_recomendado'].nunique():,}")
    compradores = pd.to_numeric(recomendaciones.get(objetivo), errors="coerce") if objetivo in recomendaciones else pd.Series(dtype=float)
    c3.metric("Compra observada última campaña", _formato_tasa(compradores))

    st.subheader("Resumen para revisión")
    st.dataframe(
        resumen.style.format({"Participación": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "La compra histórica por grupo es descriptiva: no estima el efecto de "
        "la recomendación. Para medir incremento, compara tratamiento y control."
    )

    st.subheader("Diseñar un piloto")
    segmentos = resumen["Segmento"].tolist()
    segmento_elegido = st.selectbox("Grupo prioritario", segmentos, key="segmento_decisiones")
    c4, c5 = st.columns(2)
    porcentaje_piloto = c4.slider("Porcentaje del grupo para el piloto", 10, 100, 100, 5, key="porcentaje_piloto")
    porcentaje_control = c5.slider("Porcentaje del piloto reservado como control", 5, 40, 20, 5, key="porcentaje_control")
    confirmar_permiso = st.checkbox(
        "Confirmo que consentimiento, exclusiones y límites de frecuencia se validaron por fuera de este dataset.",
        key="confirmar_permiso_decisiones",
    )

    grupo = recomendaciones.loc[recomendaciones["segmento_recomendado"].eq(segmento_elegido)].copy()
    plan = _crear_plan(grupo, porcentaje_piloto, porcentaje_control)
    tratamiento = plan[plan["grupo_experimento"].eq("Tratamiento")]
    control = plan[plan["grupo_experimento"].eq("Control (sin mensaje)")]
    c6, c7, c8 = st.columns(3)
    c6.metric("Tamaño del grupo elegido", f"{len(grupo):,}")
    c7.metric("Tratamiento", f"{len(tratamiento):,}")
    c8.metric("Control", f"{len(control):,}")
    if len(plan) < 2 or control.empty or tratamiento.empty:
        st.warning(
            "Este grupo es demasiado pequeño para formar tratamiento y control. "
            "Amplía el grupo o no interpretes el piloto como medición de incremento."
        )

    st.subheader("Mensaje de ejemplo")
    if not tratamiento.empty:
        st.info(tratamiento.iloc[0]["mensaje_borrador"])
    st.write(f"**Acción:** {grupo.iloc[0]['accion_recomendada']}")
    st.write(f"**Canal candidato:** {grupo.iloc[0]['canal_a_validar']}")
    st.write("**Dueño sugerido:** Marketing CRM")

    st.subheader("Medición propuesta")
    st.markdown(
        "1. Definir la ventana posterior a la intervención y el KPI primario antes de iniciar.\n"
        "2. Asignar el mensaje solo al grupo tratamiento; mantener el control sin esa intervención.\n"
        "3. Comparar tasa de compra entre grupos con la misma ventana y documentar tamaño de muestra.\n"
        "4. Revisar quejas, bajas y frecuencia de contacto; detener si aparecen señales de daño."
    )
    st.caption(
        "Esta aplicación no envía comunicaciones. El CSV es un plan de trabajo; "
        "la autorización marcada aquí representa una revisión del usuario, no "
        "un dato verificado por la aplicación."
    )

    columnas_exportacion = [
        c for c in [
            "cliente_id", "segmento_recomendado", "evidencia_regla", "accion_recomendada",
            "canal_a_validar", "mensaje_borrador", "responsable_sugerido", "siguiente_paso",
            "riesgo_medicion", "grupo_experimento", "kpi_primario", "ventana_medicion",
        ] if c in plan.columns
    ]
    st.download_button(
        "Descargar plan de piloto (CSV)",
        data=plan[columnas_exportacion].to_csv(index=False).encode("utf-8-sig"),
        file_name="plan_piloto_marketing.csv",
        mime="text/csv",
        disabled=(not confirmar_permiso) or len(plan) < 2 or control.empty or tratamiento.empty,
        help="Confirma permisos y asegúrate de que el piloto tenga tratamiento y control para habilitar la descarga.",
        key="descargar_plan_decisiones",
    )
