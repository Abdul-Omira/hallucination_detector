# Hallucination Detector

A lightweight, production‑oriented detector for AI agent hallucinations. Three layers: syntactic guards, semantic verifiers, and policy/remediation. Ships with CLI, Python SDK, CI, and a public metrics dashboard scaffold.

## Quickstart
```bash
pip install -e .
hd detect --text '{"answer":"Paris","confidence":0.99}'
```

## Roadmap
- v0.1: Syntactic guards + CLI + dashboard
- v0.2: RAG + NLI entailment checks
- v0.3: Shadow‑mode evaluation harness
