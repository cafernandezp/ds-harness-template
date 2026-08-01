> **Note:** example of `task-prompt-template.md` filled in with a real case (creating
> `df_features_raw.parquet` in bondora-interview). The original prompt mixed three things: this
> features-raw task (complete and well-scoped), an almost-empty stub for a "feature creation
> phase" (only `months_since_last_default` jotted down), and a separate bigger plan for
> advanced feature engineering asking for an ADVISOR review. Only the first one is filled in
> below — that's the whole point of the template being one task per prompt; the stub and the
> advanced feature engineering plan each deserve their own prompt with this same template,
> not merged into this one. The `Parameters`, `Reusability`, `Expected validation / logging`,
> and `Review` sections were left out below because the original prompt had nothing for them —
> this is what "fill in only what applies, delete the rest" looks like in practice.

---

## Task: Features raw para etapa posterior de feature engineering
## Location: `src/etl/features`

## Context
- Ya se hizo la fase de EDA; de ahí salieron los listados de variables clasificados en
  `vars_*.py`: `vars_candidate_feature`, `vars_empty_or_inapplicable`,
  `vars_existing_risk_model_output`, `vars_identifier`, `vars_origination_time_date`,
  `vars_platform_mechanics`, `vars_post_origination_leakage`, `vars_redundant`,
  `vars_target_source`.
- `target_definition.ipynb` ya define los meses considerados período covid (insumo para
  `flag_covid_period`).
- `Country` ya fue excluida antes como variable redundante en una fase previa.

## Objective
Tener una tabla inicial con features raw. La lógica avanzada de feature engineering (ratios,
evolutivos, agregaciones por ventana) se aborda en una fase posterior — acá solo dejamos la
base.

## Inputs
- `perimeter_w_target_12m.parquet`: muestra de clientes (a nivel `PartyId`) a los que se les
  van a pegar las features.
- `perimeter.parquet`: tabla de Loans (a nivel `LoanId`) que además contiene las features
  candidatas.

## Logic / Requirements
- Consolidar el input de variables a partir de los listados de EDA, decidiendo explícitamente
  qué se incluye y qué no:
  - Incluir tal cual: `vars_candidate_feature`, `vars_identifier`, `vars_origination_time_date`,
    `vars_target_source`.
  - `vars_platform_mechanics`: quedarse solo con `ReportAsOfEOD` (se usa para calcular
    `max_date`), el resto de esta familia se dropea.
  - `vars_empty_or_inapplicable`: se cargan igual en esta fase — se eliminarán después en el
    proceso formal de feature selection (% nulls, constantes, etc.), acá no se filtran todavía.
  - `vars_existing_risk_model_output`: **excluir**. No quiero hacerme responsable de meter al
    modelo outputs de modelos de riesgo anteriores que podrían estar deteriorados o cuya
    frecuencia de reestimación desconozco. Esta decisión debería quedar en un ADR.
  - `vars_redundant`: ya excluida (`Country` se dropeó antes).
- Crear `vars_key.py`: listado de variables identificadoras a nivel cliente (`LoanDate`,
  `LoanDateMonth`, `PartyId`).
- Crear variables higiénicas extra:
  - `flag_covid_period`: 1 si el mes cae dentro del período covid definido en
    `target_definition.ipynb`.
  - `flag_new_customer_12m` / `flag_new_customer_24m`: 1 si el cliente NO obtuvo ningún Loan en
    los 12 (o 24) meses previos al mes de referencia. **Caso borde**: si no hay suficiente
    historia hacia atrás para calcular el flag, dejar como `null` en vez de asumir 0. Ejemplo:
    parado en `2010-01-01`, con datos que arrancan en 2009, no se puede calcular el flag de
    24m. En la práctica esto no debería ocurrir porque `perimeter.parquet` arranca en 2009 y
    `perimeter_valid_customers` arranca en `2019-06-01`, dejando margen de sobra.
- Crear `vars_segment.py`: variables candidatas para mirar performance por segmentos más
  adelante — `flag_covid_period`, `flag_new_customer_12m`, `flag_new_customer_24m`, + alguna
  otra que el agente proponga si ve algo interesante.

## Naming conventions
Flags binarios con prefijo `flag_`. Ventanas temporales indicadas con sufijo `_12m` / `_24m`
(meses hacia atrás desde el mes de referencia).

## Explicitly out of scope
- Feature engineering avanzado (ratios, evolutivos, agregaciones por ventana) — va en una fase
  posterior aparte, con su propio prompt.
- Eliminación de columnas por nulls/constantes/redundancia — se hace formalmente en la fase de
  feature selection, no acá. `vars_empty_or_inapplicable` se deja cargada a propósito.

## Technical questions / open questions
- No entiendo por qué `NrOfScheduledPayments` está clasificada como
  `vars_post_origination_leakage`. ¿No debería corresponder a las cuotas por pagar al momento
  de originar el crédito? Podría ser un feature valioso — revisar antes de descartarla.
- ¿`MonthlyPaymentDay` es relevante como feature de un modelo?

## Expected output
- [ ] `df_features_raw.parquet`
- [ ] `vars_key.py`
- [ ] `features_raw.py` — listado de variables utilizables en la fase posterior de creación de
  features. No hay problema con que incluya, por ejemplo, fechas crudas que luego sirvan para
  calcular `n_meses_desde_eventoX` u otras derivadas.
