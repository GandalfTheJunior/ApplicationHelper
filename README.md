# Career Application Agent

A small Python foundation for a personal job application agent. This first
milestone loads a local career profile and structured job posting, analyzes
requirements, matches evidenced facts, and builds a deterministic application
context. It makes no model calls, discovers no jobs, and sends no applications.

## Architecture

```text
career.yaml + structured job YAML
    -> validated Career and JobPosting models
    -> structured job analysis
    -> deterministic matching + relevant evidence
    -> minimal application context (JSON)
```

The `src/career_agent/` package has small modules for `domain/` (Pydantic models),
`profile/` (separate loaders and evidence selection), `jobs/` (parser and analyzer),
`matching/` (coverage and alignment), and `application/` (context and verifier).
`config.py` resolves storage; `loading.py` validates YAML; `cli.py` uses argparse.

The public repository contains code, future prompts in `prompts/`, generated
JSON schemas in `schemas/`, fictional `examples/`, executable scenarios in
`evals/`, and `tests/`. `AGENTS.md` establishes the evidence and privacy rules.
There are no orchestration frameworks, databases or hidden provider dependencies.

## Privacy model and local data

Real candidate files belong outside the public repository:

```text
~/.career-agent/
├── identity.yaml
├── career.yaml
├── preferences.yaml
├── documents/
└── application-history/
```

Set `CAREER_AGENT_HOME` to change this location. A blank or unset value uses
`~/.career-agent`; `~` expands to your home and relative overrides resolve from
the current working directory. Configuration reads do not create directories.
The history and documents directories are reserved for future features.

`identity.yaml` holds optional name, email, phone and address. Matching never
loads it: matching needs career facts, not contact details. Preferences are
loaded only when explicitly passed. The context builder excludes identity by
default; its Python API permits an explicit `identity=Identity(...)` for a future
final renderer. The CLI does not offer identity inclusion in generation contexts.

**Local storage does not automatically mean local processing.** The current
implementation performs no network I/O. If a future cloud LLM receives candidate
information, that information leaves the local machine for inference. The
intended boundary is:

```text
local candidate data
    -> local evidence selection
    -> minimal relevant candidate context
    -> remote or local LLM
```

Only local inference can keep the inference step local. Selected evidence can
still contain sensitive descriptions or employer names; selection is not
anonymization. Write focused evidence entries and review any future outbound
context. No encryption or credential storage is implemented.

`.gitignore` excludes common private directories, exact personal profile names,
PDFs and Word files. Fictional `*.example.yaml` files remain tracked. Ignore
patterns are defense in depth, not a guarantee: they do not protect existing
tracked files or arbitrary filenames. Review diffs before committing. Do not
redirect private CLI JSON output into this repository or shared logs.

## Setup

Requires Python 3.12 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# For development and tests:
pip install -e '.[dev]'
```

No API keys are required. `.env.example` documents configuration; the CLI does
not automatically load `.env`. Set the variable in your shell:

```sh
export CAREER_AGENT_HOME="$HOME/.career-agent"
```

To start a real local profile, copy the fictional templates outside the repo,
then replace them with your own accurate data:

```sh
mkdir -p "$CAREER_AGENT_HOME/documents" "$CAREER_AGENT_HOME/application-history"
cp examples/career.example.yaml "$CAREER_AGENT_HOME/career.yaml"
cp examples/identity.example.yaml "$CAREER_AGENT_HOME/identity.yaml"
cp examples/preferences.example.yaml "$CAREER_AGENT_HOME/preferences.yaml"
```

The examples below require neither this copy step nor any personal files.

## Profile formats and evidence

`examples/career.example.yaml` shows skills, work experience, projects, education,
languages and certifications. Skills support optional level and years. Each
declared skill and language requires at least one structured evidence entry:

```yaml
skills:
  - name: Python
    level: advanced
    years: 4
    evidence:
      - id: python-api
        type: project
        reference: example-analytics-platform
        description: Built backend APIs using Python for Example Analytics Platform.
projects:
  - id: example-analytics-platform
    name: Example Analytics Platform
    description: A fictional analytics backend.
```

Evidence types are `work_experience`, `project`, `education`, `certification`, or
`self_report`. The first four reference an existing record ID in the respective
career collection. Self-reports use a descriptive reference label and are not
independently certified facts. Evidence IDs must consistently identify the same
entry; names must be unique after case and whitespace normalization.

Matching trusts the explicit association between a declared skill/language and
its evidence. It does not verify the truth of user data or infer skill names from
prose, projects or certificates. Unsupported skills must never be inferred.

Work experience also supports optional `start_period` and `end_period` text
fields plus an `achievements` list. Periods preserve the candidate's supplied
precision: use quoted strings such as `"2020"`, `"2020-01"` or `"2020-01-15"`.
They are stored as text, not parsed or used to calculate tenure. An omitted end
period means unspecified; it does not establish that employment is current.
Existing work records remain valid without these new fields.

Each achievement has an `id`, `description`, and optional `skill_names` and
`tags` lists. IDs must be unique within a work record. The fictional example
shows a reporting achievement linked to PostgreSQL. Achievements and their tags
are stored data only: they do not create skill matches, establish additional
evidence, or enter the application context automatically.

`examples/identity.example.yaml` demonstrates the separate optional identity
fields; `{}` is a valid identity. `examples/preferences.example.yaml` contains
target roles, locations, remote preference, employment types, optional salary
range/currency/period, industries and excluded companies. Only location and
remote preferences currently affect matching; the remaining preferences are
stored for later use, not enforced as application filters.

The job example contains company, title, location, remote status, source URL,
description, responsibilities, required/preferred skills, language requirements,
seniority and employment type. Omitted fields stay unknown, null or empty.
Inputs reject unknown fields, blank names, invalid URLs and malformed YAML.
Errors identify files and validation fields without echoing candidate values.

## Run the complete sample flow

```sh
career-agent check-profile --career examples/career.example.yaml \
  --identity examples/identity.example.yaml \
  --preferences examples/preferences.example.yaml
career-agent analyze examples/job.example.yaml
career-agent match examples/job.example.yaml --career examples/career.example.yaml \
  --preferences examples/preferences.example.yaml
career-agent context examples/job.example.yaml --career examples/career.example.yaml
```

Each command writes JSON to stdout. Invalid input returns exit code 2 with an
error on stderr. `python -m career_agent` supports the same commands. Omit
`--career` to use `$CAREER_AGENT_HOME/career.yaml`; identity and preferences are
never loaded implicitly. `check-profile` without optional file arguments only
validates career data.

Expected sample results:

| Requirement | Result |
| --- | --- |
| Python, PostgreSQL (required) | Matched; required coverage **2/2 = 1.0** |
| Docker (preferred) | Matched |
| Kubernetes, AWS (preferred) | Unsupported; preferred coverage **1/3** |
| English B2 | Matched; language coverage **1/1 = 1.0** |
| Experience alignment | Unknown; not assessed by this baseline |
| Location with example preferences | Aligned by exact location and remote status |

The match includes the actual matched, partial and unsupported requirements,
reasons and evidence IDs. Selected candidate evidence includes Python,
PostgreSQL, Docker and English; it excludes unrelated FastAPI evidence,
education, certifications and identity. `context` returns the selected facts,
structured job, unsupported/partial requirements and explicit limitations.
It excludes the original job description and source URL as unnecessary context.
Selected skills retain their recorded `level` and `years` when supplied: Python
includes `"level": "advanced"` and `"years": 4.0`. Missing metadata is omitted
from the context, and unrelated skills and their metadata remain excluded.

## Job provenance

Every `MatchResult` carries a required `job_fingerprint`: SHA-256 of the complete
validated `JobPosting` serialized as UTF-8 JSON with sorted object keys, compact
separators, and all default/null fields included. Normalization comes from model
validation (including trimmed strings and deduplicated skills); validated text
and list order are preserved. Input mapping order and omitted versus explicit
defaults do not change the fingerprint. No candidate data or Python `hash()` is
used, so results are stable across processes.

The context builder verifies this fingerprint before using the match. A changed
company, title, description, source URL or other job field is rejected even when
the structured requirements are identical. Existing requirement consistency
checks also remain in place. Old serialized matches without a fingerprint must
be regenerated. This detects accidental job/result mix-ups; it is not a digital
signature or protection against deliberate modification of both objects.

## Deterministic rules

- Required/preferred skill coverage is `exact_matches / distinct_requirements`
  within that category. Language coverage uses the same formula. With no
  requirements in a category, coverage is `null` (not applicable).
- Case and whitespace are normalized. Punctuation is preserved, so C and C++
  remain different. Duplicate job skills are counted once, with required skills
  taking precedence: their normalized duplicates are removed from preferred
  skills before analysis or matching. Each category retains its first occurrence
  order and spelling. If all preferred skills overlap with required skills,
  preferred coverage is `null`. There is no synonym expansion, adjacency
  inference or aggregate score.
- Docker does not count as Kubernetes. A missing preferred skill does not reject
  the job; there is no automatic pass/fail hiring decision.
- Languages match by name and, when supplied, exact proficiency label. A known
  language with a missing/different level is partial and requires review. There
  is no CEFR ranking or inferred equivalence; even B2 versus C1 needs review.
- Experience alignment is explicitly unknown. Location compares exact supplied
  location and work-arrangement preferences, reports missing facts as unknown,
  and never treats remote status as permission to work from anywhere.
- Evidence retrieval returns only declared facts whose names match structured
  requirements. Evidence descriptions are retained verbatim; keep them focused.
  Selected skill levels and years are copied as supplied, never inferred from
  work periods, achievement text, or tags.

## Tests, evaluations and schemas

```sh
pytest
ruff check .
ruff format --check .
python scripts/generate_schemas.py
# After committing intended schema changes, this must show no schema drift:
git diff --exit-code -- schemas/
```

Tests isolate profile storage in temporary directories. They never need or read
your actual `~/.career-agent`. `evals/matching_cases.yaml` is executed by pytest,
including exact support, missing skills, Docker/Kubernetes separation, optional
skill gaps, absent identity, relevant-only selection and zero requirements.

JSON schemas are generated from Pydantic models and tested for drift.
`candidate.schema.json` describes **career data only**, not identity. Cross-record
evidence consistency checks live in Pydantic validators and cannot all be
expressed in JSON Schema; use Python loading for full validation.

GitHub Actions runs on pushes and pull requests using Python 3.12. The workflow
installs `.[dev]`, runs pytest and both Ruff checks, regenerates schemas, and
requires the entire working tree to remain unchanged (including no new untracked
files). It uses read-only repository permissions, pinned action revisions, and
no external secrets or package publishing. Commit regenerated schemas alongside
model changes so CI can check for drift. Additional regression tests cover job
provenance, selected metadata, category precedence and the new career fields.

## Limitations and next steps

This milestone has no job discovery, scraping, free-text extraction, LLM calls,
cover-letter generation/rendering, automatic submission, or history persistence.
The prompts specify future behavior; nothing executes them yet. The parser
protocol and evidence-selector callable define small replacement boundaries.

The verifier accepts a claim plus supplied evidence and returns supported,
unsupported or uncertain. Only an exact copy of a cited evidence description is
marked supported. Missing/unknown citations are unsupported; all other text is
uncertain. This is a provenance baseline, **not a production-ready semantic or
natural-language verifier**. It cannot establish whether a paraphrase is true,
detect all contradictions, or independently validate a candidate's history.

Three next implementation steps:

1. Add a provider adapter with an explicit local/cloud choice and a preview of
   the minimal context before any remote inference.
2. Generate a draft with per-claim evidence IDs, extend verification evaluations,
   and require human review of unsupported or uncertain claims.
3. Render approved artifacts with identity only at that boundary and record a
   local application history outside Git.
