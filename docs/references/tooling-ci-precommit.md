# Tooling: pre-commit y CI

> Nota personal para releer cuando el proyecto entre en fase de producción
> y toque decidir si activar CI. Fase actual: desarrollo temprano — CI
> retirado del template a propósito; pre-commit sigue activo.

---

## `.pre-commit-config.yaml`

### Qué es

Config del framework [pre-commit](https://pre-commit.com/) — orquesta
hooks de Git. Al hacer `git commit`, Git ejecuta hooks locales antes de
crear el commit. Si un hook falla, el commit no ocurre.

### Cómo funciona

1. `uv run pre-commit install` — una vez por clone. Escribe
   `.git/hooks/pre-commit` apuntando al framework.
2. Cada `git commit` → framework lee el yaml → corre los hooks listados
   sobre los archivos staged.
3. Hooks que **modifican** (ruff `--fix`, `ruff-format`,
   `end-of-file-fixer`) reescriben el archivo. El commit aborta con
   "files were modified" → re-stagear y recommitear ya limpio.
4. Hooks que **solo validan** (`check-yaml`, `check-toml`) fallan si el
   archivo está mal.

### Cuándo se usa

- Cada commit local, automático.
- Manual global: `uv run pre-commit run --all-files` (útil primera vez
  o tras cambiar config).

### Para qué sirve en este template

- Rechaza commits con trailing whitespace, EOF sin `\n`, yaml/toml mal
  formados, files >1MB (previene subir data por accidente).
- Ruff format + `--fix` uniformizan estilo antes de que el diff llegue
  al remoto → PRs limpios, revisor no discute formato.

### Alternativa si no lo querés

Borrar el file. Se pierde el autofix en commit — ruff/format solo
corren cuando los llames a mano o en CI.

---

## `.github/workflows/ci.yml`

### Qué es

GitHub Actions workflow. Cada push/PR, GitHub levanta un runner Linux,
ejecuta los steps del yaml. Verde ✅ / rojo ❌ en el PR.

### Qué haría este en concreto

1. Checkout del repo.
2. Instala `uv` con caché de dependencies.
3. Python 3.12.
4. `uv sync --group dev`.
5. `ruff check .` — lint.
6. `ruff format --check .` — verifica formato sin modificar.
7. `pytest` (con shim que tolera "no tests collected" mientras el
   template no traiga tests).

### ¿Es necesario en fase de desarrollo?

Depende del modo de trabajo:

| Escenario | CI aporta |
|---|---|
| Solo tú, un branch, sin PRs, iteración rápida en notebooks | Poco. Pre-commit local cubre el 90%. |
| Multi-agente escribiendo código (IMPLEMENTER, LEAD haciendo quick-fixes) | Sí — red de seguridad contra agente que salta pre-commit o commitea sin instalarlo. |
| PRs, revisor humano, o repos que otros van a clonar | Sí — señal objetiva antes del merge. |
| Template público / que otros forkean | Sí — demuestra que arranca en máquina limpia. |

### Argumentos contra CI en desarrollo temprano

- Feedback loop lento (minutos vs. segundos de pre-commit).
- Requiere cuenta GitHub Actions con minutos disponibles.
- En un proyecto DS puro-experimentación, ruff+pytest en CI no atrapa
  lo importante (leakage, métricas mal calculadas — eso lo hace
  REVIEWER, no CI).

### Argumentos a favor incluso en desarrollo

- El day-1 del template es cuando más barato es agregarlo. Agregarlo
  después = riesgo de que nunca ocurra.
- Los agentes pueden `--no-verify` o commitear sin pre-commit
  installed. CI es el enforcement real.
- Sirve como documentación ejecutable: "así se levanta el repo en
  máquina limpia".

### Recomendación pragmática

Dejarlo. Si molesta el ruido, comentar el trigger de `push` y dejar
solo `pull_request` — así solo corre cuando abras PR, cero costo en
commits al branch de trabajo.

---

## Cuándo revisar esto

Activar CI cuando ocurra cualquiera de:

- Primer código bajo `src/inference/` (producción → tests obligatorios
  por CONVENTIONS §13, y sin CI no hay enforcement remoto).
- Segunda persona colabora en el repo.
- Se abre el primer PR real (no commits directos a main).
- El proyecto se hace público / se comparte con stakeholders externos.

---

## Contenido del `ci.yml` retirado (para restaurar)

Guardar en `.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Sync dev dependencies
        run: uv sync --group dev

      - name: Ruff check
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Pytest
        # `|| code=5` trata "no tests collected" como éxito — el template
        # arranca sin tests. Quitar este fallback cuando ya existan tests.
        run: |
          uv run pytest || code=$?
          if [ "${code:-0}" = "5" ]; then exit 0; else exit ${code:-0}; fi
```

Antes de restaurar: revisar versiones de las actions (`checkout@v4`,
`setup-uv@v3`) — estarán desactualizadas para entonces.
