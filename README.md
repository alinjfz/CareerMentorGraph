# CareerGraph

CareerGraph is a graph-first AI career mentor demo. It turns a learner profile
into a structured career graph, recommends a next skill, selects a portfolio
project, and generates an HTML career map.

## Quick Demo

```bash
.venv/bin/python careergraph.py demo --demo-fast
```

The default path is deterministic and does not require API keys or Neo4j.

## Local Installation

The project is set up with a local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The current local `.env` contains:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=CareerGraphPass123
NEO4J_DATABASE=neo4j
```

`OPENAI_API_KEY` is intentionally blank. Add your key only when you want live
LLM extraction.

## Optional LLM Extraction

Set `OPENAI_API_KEY` in `.env`, then run:

```bash
.venv/bin/python careergraph.py demo --use-llm
```

If the LLM output fails validation, CareerGraph retries once and then falls
back to the built-in Full-stack Developer graph.

## Optional Neo4j Persistence

Start Neo4j with Docker:

```bash
scripts/start_neo4j.sh
```

Neo4j Browser opens at:

```text
http://localhost:7474
```

Use:

```text
Username: neo4j
Password: CareerGraphPass123
```

Then write/query the graph:

```bash
.venv/bin/python careergraph.py demo --demo-fast --write-neo4j --query-neo4j
```

Stop Neo4j with:

```bash
scripts/stop_neo4j.sh
```

## Tests

```bash
.venv/bin/python -m unittest discover -s tests
```

## Post-MVP Expansion

After the sponsor demo is stable, the next useful additions are multiple target
career comparisons, resume ingestion, GitHub evidence ingestion, skill
confidence scoring, timeline planning, and a web UI over the same graph layer.
