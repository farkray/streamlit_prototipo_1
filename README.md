# Marketing Analytics

Aplicación didáctica hecha con Python, pandas y Streamlit para recorrer un análisis de clientes y convertir los datos en una propuesta de marketing que se pueda explicar y medir.

La pregunta que guía el proyecto es:

> **¿Qué clientes muestran señales de interés y qué acción de marketing podríamos proponer para cada grupo?**

El proyecto está pensado para practicar análisis, no para automatizar campañas. El dataset es sintético: no representa clientes reales ni demuestra cómo se comportarán personas en una campaña futura.

## Qué aprenderás

- Inspeccionar datos antes de modificarlos.
- Investigar valores faltantes, duplicados y rangos inusuales.
- Calcular indicadores de marketing y explicar qué cuentan como numerador y denominador.
- Entender qué puede y qué no puede decir un modelo predictivo.
- Crear grupos con reglas transparentes y proponer una acción para cada grupo.
- Diseñar una prueba con grupo de control para medir si una acción realmente mejora resultados.

## Recorrido por la aplicación

La aplicación organiza el trabajo en seis pestañas. Avanza en orden: cada una prepara el análisis de la siguiente.

### 1. Entender

Muestra cuántas filas y variables hay, una vista previa, tipos de dato, valores únicos, faltantes y duplicados exactos. El explorador permite revisar estadísticas de una variable numérica o frecuencias de una variable de texto.

**Pregunta para el equipo:** ¿qué información tenemos y qué significa cada columna en el negocio? Un nombre de columna es una pista, no reemplaza un diccionario de datos.

### 2. Limpiar

Presenta un diagnóstico y deja decidir si se quitan duplicados exactos, se excluyen filas fuera de rangos definidos o se reemplazan ciertos faltantes. Los cambios se aplican a una **copia de trabajo**; el CSV original no se modifica.

En particular, puedes investigar si la falta de días y monto de la última compra coincide con `compras_12m = 0`. La aplicación no asume que un faltante significa cero: requiere que confirmes esa interpretación antes de reemplazarlo. También requiere confirmar los rangos antes de excluir filas.

La pestaña muestra una bitácora de las decisiones y permite descargar la copia como `clientes_limpios.csv`. Mientras la sesión de Streamlit siga activa, las pestañas posteriores usan la copia de trabajo. Si no aplicas cambios, usan los datos originales.

### 3. Descriptiva

Resume el conjunto actual con indicadores como clientes, compradores de los últimos 12 meses, compra en la última campaña, gasto, compras promedio e interacción con campañas. También permite comparar resultados por género, ciudad, canal de origen o categoría preferida.

Una tasa describe lo observado; no explica por qué ocurrió. Por ejemplo, una conversión mayor en una categoría no demuestra que pertenecer a esa categoría cause la compra.

Revisa los denominadores antes de interpretar una tasa. Las tasas de apertura y clic comparan eventos con campañas recibidas en registros válidos; el abandono compara carritos abandonados con carritos registrados. Confirma que estas definiciones coincidan con las del negocio antes de usarlas fuera del ejercicio.

### 4. Predictiva

Entrena un modelo de bosque aleatorio para reconocer patrones asociados con `compro_ultima_campana`. Separa aleatoriamente los datos: 75% para aprender y 25% para evaluar. La división es reproducible, por lo que el ejercicio puede repetirse con los mismos datos.

La pestaña traduce el resultado a una pregunta de capacidad: **¿qué porcentaje de la muestra histórica evaluada podría revisar el equipo?** Ordena esos registros por el score del modelo y compara el grupo elegido con el resto. Muestra cuántos compraron dentro del grupo, qué parte de los compradores se identificó y cuántos compradores quedaron fuera.

El grupo evaluado es histórico y ya conocemos su resultado. La pestaña sirve para revisar el ejercicio, no entrega una lista de contacto. El score ordena registros, pero no es una probabilidad calibrada ni una garantía de compra. La evaluación es aleatoria, no temporal, y el uso de variables debe validarse contra el momento en que se tomaría una decisión real.

### 5. Prescriptiva

Propone grupos mediante reglas visibles. Puedes ajustar los días para considerar una reactivación, el percentil de actividad digital y el canal candidato. Las reglas se aplican con esta prioridad:

1. **Recuperar carrito:** hay carritos y abandonos registrados en los últimos 30 días.
2. **Reactivar comprador:** hubo compras en los últimos 12 meses y la última compra fue hace al menos los días elegidos.
3. **Revisar recencia:** hay compras registradas, pero falta el dato de días desde la última compra.
4. **Explorar categoría:** visitas y productos vistos están en o sobre el percentil seleccionado.
5. **Nutrir y medir:** no se encontró una de las señales anteriores.

La pestaña enseña el tamaño de cada grupo, la evidencia de la regla y una acción y mensaje de ejemplo. Los ejemplos no inventan descuentos, urgencia ni beneficios. Las reglas organizan ideas para probar; no prueban causalidad ni sustituyen la validación de permisos y frecuencia de contacto.

### 6. Decisiones

Resume los grupos, su evidencia, acciones, responsables sugeridos y riesgos de medición. Permite elegir un grupo para armar un piloto y separar una parte como tratamiento y otra como control.

El plan propone comparar la tasa de compra entre ambos grupos usando la misma ventana de medición. La aplicación no envía mensajes. Para habilitar la descarga del plan, hay que confirmar que consentimiento, exclusiones y límites de frecuencia se validaron por fuera de este dataset. Esa confirmación es responsabilidad de quien usa la app; la aplicación no puede verificarla.

## Dataset

Archivo incluido: `data/dataset_clientes_sinteticos_segmentos_marketing.csv`.

El archivo de ejemplo contiene 1,468 registros y 22 columnas. Sus nombres sugieren estas familias de variables:

| Familia | Columnas |
|---|---|
| Identificación | `cliente_id` |
| Perfil | `edad`, `genero`, `ciudad`, `ingreso_mensual`, `fecha_alta` |
| Actividad digital reciente | `visitas_web_30d`, `productos_vistos_30d`, `carritos_30d`, `abandono_carrito_30d` |
| Historial de compra | `compras_12m`, `gasto_total_12m`, `dias_desde_ultima_compra`, `monto_ultima_compra` |
| Preferencias y origen | `categoria_preferida`, `canal_origen` |
| Interacción con campañas | `campanas_recibidas_30d`, `emails_abiertos_30d`, `clics_campanas_30d` |
| Promociones | `uso_cupon_12m`, `descuento_promedio` |
| Resultado de campaña | `compro_ultima_campana` |

En el objetivo del ejercicio, `compro_ultima_campana` indica si el registro compró (1) o no compró (0) en la última campaña. Verifica siempre el significado, la unidad y el periodo de cada variable; los nombres por sí solos no lo garantizan.

## Requisitos

- Python 3.10 o posterior recomendado.
- pip.
- Las dependencias incluidas en `requirements.txt`.

## Instalación y ejecución

Abre una terminal en la carpeta raíz del proyecto (la carpeta que contiene `app.py`) y ejecuta:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Si PowerShell no permite activar el entorno, puedes ejecutar la instalación y la app sin activarlo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

### macOS o Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará una dirección local en la terminal y normalmente abrirá el navegador. Mantén la terminal y el entorno activos mientras trabajas.

## Estructura del proyecto

```text
.
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── dataset_clientes_sinteticos_segmentos_marketing.csv
└── tabs/
    ├── entender.py
    ├── limpiar.py
    ├── descriptiva.py
    ├── predictiva.py
    ├── prescriptiva.py
    └── decisiones.py
```

`app.py` configura Streamlit, carga el CSV desde la carpeta del proyecto y organiza la navegación. Cada archivo dentro de `tabs/` contiene la lógica y presentación de una etapa; recibe el dataframe desde `app.py` mediante la función `mostrar(df)`.

## Recomendaciones para el análisis

- No elimines una fila o rellenes un faltante sin explicar por qué.
- Conserva el archivo original y registra cada transformación.
- Comprueba las definiciones y el momento de captura de las variables.
- No confundas una relación observada con una causa.
- Considera el modelo como apoyo para explorar, no como autorización para contactar clientes.
- Evalúa las acciones con un grupo de control y una métrica definida antes de lanzar el piloto.
- Antes de usar datos reales, valida permisos, privacidad, sesgos, seguridad y las reglas de contacto de tu organización.

## Dependencias

Las dependencias principales están declaradas en `requirements.txt`:

- **Streamlit:** interfaz web interactiva.
- **pandas:** lectura y análisis de tablas.
- **scikit-learn:** preparación de datos y modelo de clasificación para el ejercicio predictivo.
