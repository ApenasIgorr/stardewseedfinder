# Stardew Seed Finder

Aplicação local para varrer e ranquear seeds (`GameID`) de Stardew Valley com base em **restrições obrigatórias** e **preferências com peso**.

## Decisão técnica (fonte de previsões)

**Estratégia escolhida: B (simulador determinístico próprio)**.

Motivo: para um projeto sustentável offline, evitamos scraping/UI automation e mantemos um núcleo modular plugável por versão. Nesta versão inicial, o simulador cobre um subconjunto de categorias com comportamento determinístico por seed e contexto.

> Observação de honestidade técnica: a implementação atual é um simulador compatível com a arquitetura pedida, mas **não replica 1:1 a lógica interna oficial do jogo em todas as categorias**. Itens não mapeados aparecem como `não suportado` no resultado.

## Arquitetura (diagrama textual)

```text
ui/
  app.py (Web UI local: editor config + execução + ranking + export)
main.py (CLI)

core/
  predictor_adapter/
    base.py (interface)
    v16_simulator.py (simulador versão 1.6.x)
  constraints/
    evaluator.py (Weather, Cart, Night Event, Train, Sequence, Multi)
  scoring/
    scorer.py (hard fail-fast + score soft + explicações)
  search/
    engine.py (range/random/mixed + multiprocessing + cache local)
  config.py (schema/validação)

tests/
  test_schema.py
  test_constraints.py
  test_determinism.py
examples/
  community_center_early.json
  traveling_cart_focus.json
  rain_skull_cavern.json
```

## Schema inicial (JSON/YAML)

```json
{
  "hard_constraints": [],
  "soft_preferences": [
    {
      "weight": 1.5,
      "tolerance": 0.3,
      "constraint": { "type": "weather", "season": "spring", "year": 1, "min_rain_days": 6 }
    }
  ],
  "search": {
    "mode": "range",
    "seed_min": 1,
    "seed_max": 5000,
    "random_count": 1000,
    "random_seed": 42,
    "workers": 4,
    "timeout_seconds": 20
  },
  "context": {
    "game_version": "1.6.x",
    "mode": "single",
    "days_played": 0,
    "daily_luck": 0,
    "luck_level": 0,
    "geode_counter": 0,
    "mystery_box_counter": 0,
    "prize_ticket_counter": 0,
    "progression_flags": {}
  },
  "output": {
    "top_n": 20,
    "export_formats": ["json", "csv"],
    "include_unsupported": true
  }
}
```

## Dois exemplos reais de config

- `examples/community_center_early.json`
- `examples/rain_skull_cavern.json`

## Cobertura atual

Suportado (simulado deterministicamente):
- Weather (inclui possibilidade de `green_rain`)
- Traveling Cart
- Night Events
- Train schedule
- Garbage cans
- Sequências: geode / mystery_box / golden_coconut

Ainda não suportado (marcado explicitamente):
- Prize tickets
- Raccoon requests
- Shop RNG avançado

## Instalação

```bash
python3.11 -m venv .venv
source .venv/bin/activate
# opcional para YAML: pip install pyyaml
```

## Rodar UI (Web local)

```bash
python ui/app.py
```

Acesse `http://127.0.0.1:8501`.

## Rodar via CLI

```bash
python main.py --config examples/community_center_early.json --out results.json
python main.py --config examples/community_center_early.json --out results.csv
```

## Busca e performance

- Modos: `range`, `random`, `mixed`
- Paralelismo: `ProcessPoolExecutor` (config `workers`)
- Otimização: fail-fast em hard constraints + cache por seed/query em `.seed_cache.json`

## Limitações / honestidade técnica

- YAML depende de PyYAML opcional; sem ele, use JSON.
- Versão-alvo atual: 1.6.x (subconjunto).
- Critérios não suportados não são “chutados”; aparecem como não suportados.

## Roadmap

1. Trocar simulador por adaptador fiel às regras reais (ou portar lógica open-source do predictor por versão).
2. Expandir regras de versão 1.5/1.6 e diferenças por modo.
3. Melhorar ranking com normalização por critério e confiança.
4. Export detalhado por critério para BI.
