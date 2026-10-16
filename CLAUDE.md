# methodic · repo rules

**Public** repo. Anyone can read everything that goes in here.

## Hard rules

1. **Zero real data.** No tax ID (RUT), company name, client, supplier, person, license plate, real
   price nor local path. Examples and tests use fictitious cases (company "Ferretería Andes",
   "Constructora Sur", suppliers "Supplier A/B/C"). Real data lives in
   `methodic-data/` (legacy `ingeniero-agentico-datos/`), outside the repo.
2. **One skill per method, not per course.** The course is a source, not a structure.
3. **Every number comes from a script.** The skill decides; the script calculates. No figure the
   user will use is calculated "from memory".
4. **Each method carries a test that adds up.** `tests/` has a fictitious case with the expected
   result, and `python scripts/<script>.py --test` ends in `OK` or fails.
5. **Traceable.** Each output says which input each number came from (file, line, assumption). An
   assumption that did not come from the user is marked `SUPUESTO` (`language: es`) or
   `ASSUMPTION` (`language: en`) in the output.
6. **Course material is not reproduced.** It is cited in `SOURCES.md` (author, title, edition,
   chapter). No slides, answer keys nor exams.
7. **The profile rules.** Currency, taxes, rates, criteria and output language of the company are
   read from the profile (`profiles/_template.yaml` defines the fields). No company value is written
   inside a skill.
8. **Never touch the operator's files outside the cycle.** Any script that writes outside the
   manual's work folder goes through `intervene` (scope check, backup, logbook). No script deletes
   an operator's file, installs software, uses the network or sends anything; a script may only
   remove what it created itself (its temporary folders, the installer's own copies).

## Mold of a method

```
skills/<method>/
├── SKILL.md      frontmatter name (= the folder name) + description (English, conditions of use;
│                 at most 1,024 characters, the limit of the Agent Skills standard and of
│                 claude.ai); English body: when, what the agent decides, what the script
│                 calculates, how to read the output, typical errors
├── GUIDE.md      the same method for a person, step by step, with the sample case (English)
├── GUIA.md       the same guide in Spanish
├── templates/    empty inputs (YAML or JSON) and, if it applies, the output Excel
├── scripts/      Python 3.11+, standard library + openpyxl only; `--test` runs the test
├── tests/        sample-case.(yaml|json) + expected.json
└── SOURCES.md    courses and bibliography the method comes from
```

The documenter (`skills/interview/`, `skills/manual/`, `skills/intervene/`) and the orchestration
layer (`skills/orchestrate/`, `skills/map-context/`, `skills/research/`, `skills/audit/`, the
workers in `agents/`) follow the same mold. Contracts: `ARCHITECTURE.md` (stages) and
`docs/MANUAL-FORMAT.md` (the manual, the scope, the logbook); a skill that differs from a contract
is the one that gets fixed.

Compatibility: every script keeps the pre-v1.1 Spanish flags as hidden aliases and accepts Spanish
keys in its inputs (and the Spanish `contexto/` file names), so the private cases written before
v1.1 still run unchanged.

## Writing

Direct English. An aside goes in parentheses; the dash only separates.

Spanish versions: `README.es.md` and `GUIA.md` per skill; outputs follow profile `language`.
