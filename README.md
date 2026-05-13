# CareerGraph

CareerGraph is a graph-first AI career mentor demo. It turns a learner profile
into a structured career graph, recommends a next skill, selects a portfolio
project, and generates an HTML career map.

## Quick Demo

```bash
python3 careergraph.py demo --demo-fast
```

The default path is deterministic and does not require API keys or Neo4j.

## Optional LLM Extraction

Set `OPENAI_API_KEY` in `.env`, then run:

```bash
python3 careergraph.py demo --use-llm
```

If the LLM output fails validation, CareerGraph retries once and then falls
back to the built-in Full-stack Developer graph.

## Optional Neo4j Persistence

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Set the Neo4j values in `.env`, then run:

```bash
python3 careergraph.py demo --demo-fast --write-neo4j --query-neo4j
```

## Tests

```bash
python3 -m unittest discover -s tests
```

## Post-MVP Expansion

After the sponsor demo is stable, the next useful additions are multiple target
career comparisons, resume ingestion, GitHub evidence ingestion, skill
confidence scoring, timeline planning, and a web UI over the same graph layer.
