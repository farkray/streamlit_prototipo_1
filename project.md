# Project guide: Marketing Analytics with Streamlit

## Purpose

This is a teaching project for a two-hour marketing/data-science class. Students use a synthetic customer dataset to move from inspecting data to proposing a justified marketing action. The app is built incrementally in Python with Streamlit and pandas, in VS Code.

The guiding question is:

> **Which customers show purchase intent, and what marketing action should we take for each type of customer?**

The learning evidence is that students can inspect and assess a dataset, calculate and interpret marketing KPIs, form defensible customer segments, and recommend an action and advertising message based on evidence. The goal is not simply to produce charts or a model.

## Teaching principles

- Work in stages: **Understand → Clean → Describe → Predict → Prescribe → Decide**.
- Each stage belongs in its own Streamlit tab and, as it is implemented, its own Python module.
- Teach students to inspect and interpret data before changing it. Missing values are not automatically errors; never drop or impute them without understanding their meaning and stating the reason.
- Distinguish descriptive summaries from business conclusions. Association or a model score does not establish causation.
- Treat model outputs as decision support. Students must explain assumptions, errors, limitations, and human review.
- Keep code readable for intermediate beginners. Use Spanish labels/comments and explicit function names.

## Current project state

The application now implements the full six-stage classroom flow. The intended root layout is:

```text
marketing_streamlit/
├── stream_train/                 # local virtual environment; do not commit
├── data/
│   └── dataset_clientes_sinteticos_segmentos_marketing.csv
├── tabs/
│   ├── __init__.py
│   ├── entender.py
│   ├── limpiar.py
│   ├── descriptiva.py
│   ├── predictiva.py
│   ├── prescriptiva.py
│   └── decisiones.py
├── app.py                        # app setup, data loading, navigation/orchestration
├── requirements.txt
└── project.md                    # this guide
```

The user's actual VS Code screenshot showed a project folder named `ejem_streamlit_2026`. Prefer the actual existing folder and filenames over renaming it to match this illustrative tree. The earlier screenshot showed `AttributeError: module 'tabs.entender' has no attribute 'mostrar'`; the app now imports each `mostrar` function explicitly. Resolve CSV paths relative to `app.py` so launch location does not affect loading.

Each stage is a module receiving a dataframe explicitly. The cleaned dataframe is stored separately from the raw input in Streamlit session state. The predictive module requires scikit-learn, listed in `requirements.txt`.

## Dataset

Input file: `data/dataset_clientes_sinteticos_segmentos_marketing.csv`.

Observed dataset facts (from the provided CSV):

- 1,468 records and 22 columns.
- No exact duplicate rows in the supplied version.
- 378 missing values in `dias_desde_ultima_compra` and 378 in `monto_ultima_compra`.
- The two missing-value columns are expected to be investigated. They may correspond to customers with no purchase history, but verify this against `compras_12m` before encoding or imputing anything.
- `fecha_alta` is currently read as text by default; parse it to a date only when a later exercise needs it.
- `compro_ultima_campana` is a 0/1 outcome field and may serve as a classroom classification target.

Columns:

| Column | Likely role / teaching use |
|---|---|
| `cliente_id` | Customer identifier; exclude from model features unless there is a clearly justified reason. |
| `edad`, `genero`, `ciudad`, `ingreso_mensual` | Customer profile / demographic and economic descriptors. |
| `fecha_alta` | Customer tenure; requires date parsing to derive duration. |
| `visitas_web_30d`, `productos_vistos_30d`, `carritos_30d`, `abandono_carrito_30d` | Recent digital behavior and funnel signals. |
| `compras_12m`, `gasto_total_12m`, `dias_desde_ultima_compra`, `monto_ultima_compra` | Purchase history / recency, frequency, and value (RFM-like exploration). |
| `categoria_preferida`, `canal_origen` | Preference and acquisition channel. |
| `campanas_recibidas_30d`, `emails_abiertos_30d`, `clics_campanas_30d` | Campaign exposure and engagement. |
| `uso_cupon_12m`, `descuento_promedio` | Promotion and discount behavior. |
| `compro_ultima_campana` | Candidate binary target: 0 = did not buy, 1 = bought in the last campaign. |

These are interpretations based on column names and sample values, not a verified business data dictionary. Ask students to validate meanings and units rather than assume them.

## Application architecture

`app.py` should stay an orchestrator. It configures Streamlit, loads the CSV, defines all six tabs, and calls one display function per implemented module. Each tab module receives data explicitly as a function argument; it should not reload the dataset or depend on hidden global state.

Module API:

```python
# tabs/entender.py
def mostrar(df): ...

# tabs/limpiar.py, tabs/descriptiva.py, tabs/predictiva.py,
# tabs/prescriptiva.py, tabs/decisiones.py
def mostrar(df): ...
```

Planned navigation labels:

1. Entender
2. Limpiar
3. Descriptiva
4. Predictiva
5. Prescriptiva
6. Decisiones

The first module, `tabs/entender.py`, should show the central question, row/column counts, a small preview, a schema/quality table (dtype, unique values, missing values), exact duplicate count, and a variable explorer. The explorer should show descriptive statistics for numeric columns and frequency counts for categorical columns, including missing values. Give Streamlit widgets stable unique keys such as `variable_entender`.

Keep each stage in its own module; do not put analysis logic back into `app.py`.

## End-to-end learning roadmap

### 1. Entender los datos

Students answer: What information is present? Which fields describe a customer, behavior, purchase history, or marketing interaction? What types and quality issues are visible? At this stage, do not prescribe a campaign.

### 2. Limpiar los datos

Show missingness, duplicates, data types, invalid ranges, and potential outliers. Have students state a reason for each treatment. Investigate whether missing purchase recency/value aligns with `compras_12m == 0`; preserve a raw dataframe and create a separate cleaned dataframe so decisions are reversible and auditable. Do not silently replace missing purchase values with zero unless the semantics are established and the transformation is documented. Do not delete outliers just because they are extreme.

### 3. Estadística descriptiva

Build interpretable marketing/business KPIs, for example customer count, buyers, campaign purchase rate, average order value where defined, revenue/customer, purchase frequency, email open rate, campaign CTR, cart abandonment, and segment distributions. Specify denominators and handle zero denominators/missing fields. Use the correct denominator for rates (e.g. opens / received campaigns only if records support that interpretation).

### 4. Estadística predictiva

Optionally train a simple classification model to estimate `compro_ultima_campana`. Split train/test data, use a reproducible random seed, build preprocessing for numeric/categorical variables, and report metrics suited to the class balance (confusion matrix, precision, recall, F1, ROC-AUC where meaningful). Avoid `cliente_id` and any variables that directly encode the campaign outcome or would not be available at prediction time. Check for leakage: `campanas_recibidas_30d`, opens, and clicks may be legitimate only if they are known before the decision moment; define that moment first. Make clear that synthetic-data results are instructional and not a validated production forecast.

### 5. Estadística prescriptiva

Combine observed behavior, segment definitions, and (if implemented) estimated probability into transparent rules for recommended actions. Examples include cart recovery, cross-sell, or reactivation, but only when supported by the available fields. Show the rule and evidence behind each recommendation; do not present a model score as a guaranteed outcome.

### 6. Toma de decisiones

Create a final view connecting KPI, segment, evidence, recommendation, owner/next action, and risk or measurement plan. Generate an example message grounded in known fields (e.g. `categoria_preferida`), without inventing discounts, inventory, urgency, or benefits not in the dataset.

## Environment and run commands

Create the environment from the project root:

```bash
python -m venv stream_train
```

Activate it:

```powershell
# Windows PowerShell
stream_train\Scripts\Activate.ps1
```

```bat
REM Windows CMD
stream_train\Scripts\activate.bat
```

```bash
# macOS (zsh/bash)
source stream_train/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Run from the folder containing `app.py`:

```bash
streamlit run app.py
```

The active terminal should show `(stream_train)`. The app resolves the CSV path relative to `app.py`, so it can be launched from another working directory.

## Guidance for an AI coding agent

1. Read this file first and preserve the staged teaching flow.
2. Before changing code, inspect the actual project tree and current file contents; do not assume the sample code in this guide has already been implemented.
3. Keep the stages understandable; implement later tabs when requested and keep each stage in its module.
4. Preserve the original input CSV. Keep cleaning/transformed data in separate variables or modules and document transformations.
5. Use explicit imports, descriptive Spanish naming in the UI, and unique Streamlit widget keys.
6. When providing code instructions, give complete file contents when that reduces copy/paste ambiguity, and state exactly which file each block belongs to.
7. Verify syntax/imports and run a meaningful local check when files are available. If Streamlit is unavailable, say so and provide the exact command the user can run.
8. Do not claim predictive validity from this synthetic classroom dataset. Surface assumptions and data leakage risks in modeling guidance.

