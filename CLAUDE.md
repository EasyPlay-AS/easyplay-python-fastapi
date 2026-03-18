# EasyPlay Python FastAPI

Stateless FastAPI optimaliseringstjeneste for baneplanlegging. Bruker AMPL/SCIP for constraint-basert optimering. Deployed på Railway (Docker).

## EasyPlay Ecosystem

Dette er en spesialisert beregningsmotor som KUN konsumeres av easyplay-api-nestjs:

- **easyplay-api-nestjs** — NestJS backend-API. Kaller dette API-et for baneoptimering. Sender payload, mottar optimert plan. Eneste konsument.
- **easyplay-no** — Next.js web-frontend. Ingen direkte kontakt med dette API-et.
- **easyplay-app** — React Native mobilapp. Ingen direkte kontakt med dette API-et.

VIKTIG: Dette API-et er stateless — ingen database, ingen state mellom requests. Mottar komplett payload, returnerer optimert resultat.

## Architecture

### Entry Point
`main.py` — FastAPI app med 5 endepunkter:
- `/` — Health check (GET, offentlig)
- `/solve-a-b` — Test-endepunkt (POST)
- `/solve-example` — Eksempel-solver (POST)
- `/solve-field-optimizer` — Hovedoptimering (POST)
- `/solve-field-optimizer-stream` — Sanntids SSE-streaming av optimering (POST)

### Directory Structure
- `services/` — Forretningslogikk (field_optimizer_service.py er hoved-tjenesten)
- `models/` — Pydantic v2 input/output-modeller, organisert per domene
- `utils/` — Konverteringsfunksjoner (payload→AMPL input, AMPL output→allokeringer)
- `ampl/` — AMPL-modellfiler (.mod) for constraint-definering
- `auth.py` — Token-verifisering (`API_SECRET` env var)
- `mocks/` — Test-data
- `tests/` — Pytest test suite

### Optimization Flow
1. NestJS API sender payload med aktiviteter, baner, tidsluker, constraints
2. `utils/` konverterer payload til AMPL-format
3. `services/` kjører AMPL-solver med iterative tidsbegrensninger (15s → 90s)
4. SSE-endepunkt streamer mellomresultater tilbake i sanntid
5. `utils/` konverterer AMPL-output til API-respons

## Conventions

- snake_case for filnavn, funksjoner og variabler
- PascalCase for klasser og Pydantic-modeller
- Google-style docstrings på funksjoner
- Moderne Python typing: `list[T]`, `T | None` (ikke `List[T]`, `Optional[T]`)
- Pydantic v2 for alle modeller
- Statiske metoder i service-klasser der det gir mening
- `verify_token` dependency injection for autentisering

## Key Commands

```bash
source .venv/bin/activate   # Aktiver virtuelt miljø
fastapi dev main.py         # Dev server med hot reload
pytest                      # Kjør tester
docker build -t easyplay .  # Bygg Docker-image
```

## Common Mistakes

- AMPL-lisens MÅ aktiveres via `AMPL_LICENSE_UUID` env var — uten denne feiler alle solver-endepunkter
- IKKE legg til database eller persistent state — dette API-et er designet stateless
- Solver-timeouts (15s initiell, 90s total) — IKKE øk uten å forstå minnebruk på Railway
- Auth bruker `API_SECRET` env var (ikke JWT) — enkel token-matching
- AMPL .mod-filer i `ampl/` definerer constraints — endringer her påvirker alle optimeringer
- Python 3.11+ påkrevd — libgfortran5 trengs for AMPL (installert i Dockerfile)
- SSE streaming-endepunktet krever at klienten håndterer Server-Sent Events korrekt
