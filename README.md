# PromptQA

**Systematisk test og kvalitetssikring af LLM-output.**

Definér testcases i YAML, kør dem mod en LLM og få strukturerede pass/fail-resultater.

---

## Overblik

| Koncept | Placering | Formål |
|---|---|---|
| **Strategy Pattern** | `providers/base.py` | Skift LLM-backend uden at røre evaluerings-logikken |
| **Test-Driven Development** | `tests/` | Hver feature starter med en fejlende test |
| **YAML-konfiguration** | `examples/` | Deklarative testdefinitioner — ingen kodeændringer nødvendige |
| **Typed dataclasses** | `providers/base.py`, `config.py` | Strukturerede resultat-objekter i stedet for løse dicts |
| **CI/CD** | `.github/workflows/ci.yml` | Automatisk kvalitetskontrol: pytest, ruff, mypy |

---

## Sådan virker det

### 1. Definér en testcase i YAML

```yaml
# mine_tests.yaml
name: "Mine tests"
provider: mock                          # eller: anthropic

tests:
  - name: "Tjek at svaret er på dansk"
    prompt: "Hvad er hovedstaden i Danmark?"
    system: "Svar på dansk i én sætning."
    criteria:
      - type: contains
        value: "København"
      - type: max_length
        value: 100

# Mock-svar (bruges når provider er 'mock' — gratis, ingen API)
mock_responses:
  "Hvad er hovedstaden i Danmark?": "Hovedstaden i Danmark er København."
```

**Kriterietyper:** `contains`, `not_contains`, `contains_any`, `max_length`

### 2. Kør testen

```bash
# Med mock-provider (gratis, foruddefinerede svar fra YAML)
promptqa run mine_tests.yaml

# Med Claude API (rigtige LLM-svar)
promptqa run mine_tests.yaml --provider anthropic

# Med detaljer per kriterie
promptqa run mine_tests.yaml --verbose
```

### 3. Læs resultatet

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PromptQA — 1 test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PASS  Tjek at svaret er på dansk (0.0ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1 passed (0ms)
```

### Vil du bruge en rigtig LLM?

```bash
cp .env.example .env       # Tilføj din ANTHROPIC_API_KEY
promptqa run mine_tests.yaml --provider anthropic
```

Gratis alternativ: [Ollama](https://ollama.com/) kører en lokal LLM uden API-nøgle.

---

## Arkitektur

```
                   promptqa run tests.yaml --provider anthropic
                                        |
                                        v
                  +-------------------------------------------+
                  | CLI (cli.py)                              |
                  | Parser argumenter, vælger provider        |
                  +---------------------+---------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Config Loader (config.py)                 |
                  | Læser YAML, validerer testdefinitioner    |
                  +---------------------+---------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Evaluator (evaluator.py)                  |
                  | For hver testcase:                        |
                  | 1. Send prompt til provider               |
                  | 2. Tjek svar mod kriterier                |
                  | 3. Saml resultater                        |
                  +---------------------+---------------------+
                                        |
                    provider.complete(prompt, system)
                                        |
                 +----------------------+--------------------------+
                 |                      |                          |
                 v                      v                          v
       +-------------------+  +-----------------------+  +-------------------+
       | MockProvider      |  | AnthropicProvider     |  | (OllamaProvider)  |
       |                   |  |                       |  |                   |
       | Returnerer for-   |  | Kalder Claude API     |  | Kører lokal LLM   |
       | definerede svar   |  | med din API-nøgle     |  | via Ollama        |
       | fra YAML          |  |                       |  |                   |
       +-------------------+  +-----------------------+  +-------------------+
          (gratis)              (kræver API-nøgle)         (gratis, lokal)
                 +----------------------+--------------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Reporter (reporter.py)                    |
                  | Formaterer: pass/fail, opsummering,       |
                  | tokenforbrug, timing                      |
                  +-------------------------------------------+
```

**Strategy Pattern:** Evaluator kender ikke den aktive provider — den kalder `provider.complete()`, og den konkrete provider håndterer resten. En ny provider kræver én ny klasse. Nul ændringer i evaluerings-logikken. Se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detaljer.

---

## Teknologier

| Værktøj | Rolle |
|---|---|
| Python 3.11+ | Sprog |
| Anthropic SDK | Claude API-integration |
| PyYAML | Testcase-konfiguration |
| pytest | Testframework |
| ruff | Linting |
| mypy | Statisk typetjek |
| GitHub Actions | CI/CD-pipeline |

---

## Kom i gang

```bash
git clone https://github.com/SMat777/PromptQA.git
cd PromptQA
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"

# Kør med mock-provider (gratis)
promptqa run examples/basic_test.yaml
```

---

## Eksempler

| Suite | Fil | Hvad den tester |
|---|---|---|
| **Grundlæggende** | `examples/basic_test.yaml` | Fakta, tone og sikkerhed — 3 tests |
| **Tone** | `examples/tone_check.yaml` | Professionel vs. uformel kommunikation |
| **Sikkerhed** | `examples/safety.yaml` | Afvisning af skadelige forespørgsler |
| **Faktuel** | `examples/factual.yaml` | Korrekte svar på kendte spørgsmål |

---

## Projektstruktur

```
src/promptqa/
├── __init__.py              # Pakke-version
├── __main__.py              # Indgang for python -m promptqa
├── cli.py                   # Argument-parsing og kommando-routing
├── config.py                # YAML → typed TestSuite/TestCase/Criterion dataclasses
├── providers/
│   ├── base.py              # BaseProvider ABC — Strategy-interfacet
│   ├── mock.py              # MockProvider — dict-baseret svar fra YAML
│   └── anthropic.py         # AnthropicProvider — Claude API
├── evaluator.py             # Kører testcases: provider → kriterietjek → TestResult
└── reporter.py              # Terminal-output med ANSI-farver

tests/                       # 65 tests — pytest
examples/                    # 4 YAML-suites med mock-svar
docs/
├── ARCHITECTURE.md          # Strategy Pattern dokumentation
└── LEARNING.md              # Udviklingsjournal
```

Ny provider? Implementér `BaseProvider` i `providers/`, tilføj til factory i `cli.py`.
Nyt kriterie? Skriv checker-funktionen, tilføj til dispatch-dict i `evaluator.py`.

---

## Udviklingsproces

1. **Issues** definerer scope med acceptkriterier
2. **Feature branches** isolerer arbejde (`feature/mock-provider`, `feature/evaluator`)
3. **TDD** driver implementation — test commites først, derefter kode
4. **Conventional commits** (`feat:`, `test:`, `docs:`)
5. **CI** validerer ved hvert push: pytest, ruff, mypy

```bash
pytest -v               # Kør alle tests
ruff check src/ tests/  # Lint
mypy src/               # Typetjek
```
