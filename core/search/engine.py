from __future__ import annotations

import heapq
import json
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from time import time
from typing import Any, Iterable

from core.predictor_adapter.v16_simulator import V16Simulator
from core.scoring.scorer import SeedEvaluation, evaluate_seed

_CACHE_PATH = Path('.seed_cache.json')


def _load_cache() -> dict[str, Any]:
    if _CACHE_PATH.exists():
        return json.loads(_CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict[str, Any]) -> None:
    _CACHE_PATH.write_text(json.dumps(cache))


def _evaluate(seed: int, context: dict[str, Any], hard: list[dict[str, Any]], soft: list[dict[str, Any]]) -> dict[str, Any]:
    pred = V16Simulator().predict(seed, context)
    result = evaluate_seed(seed, pred, hard, soft)
    return asdict(result)


def _seed_iter(search: dict[str, Any]) -> Iterable[int]:
    mode = search["mode"]
    if mode == "range":
        yield from range(search["seed_min"], search["seed_max"] + 1)
    elif mode == "random":
        rng = random.Random(search.get("random_seed", 42))
        for _ in range(search["random_count"]):
            yield rng.randint(1, 2_147_483_647)
    else:
        yield from range(search["seed_min"], search["seed_max"] + 1)
        rng = random.Random(search.get("random_seed", 42))
        for _ in range(search["random_count"]):
            yield rng.randint(search["seed_min"], search["seed_max"])


def search_best(requirements: dict[str, Any], progress_cb=None) -> list[dict[str, Any]]:
    hard = requirements["hard_constraints"]
    soft = [s if isinstance(s, dict) else s.model_dump() for s in requirements["soft_preferences"]]
    context = requirements["context"]
    search = requirements["search"]
    output = requirements["output"]

    timeout = search.get("timeout_seconds")
    start = time()
    top_n = output.get("top_n", 20)

    cache = _load_cache()
    heap: list[tuple[float, int, dict[str, Any]]] = []

    seeds = list(_seed_iter(search))
    total = len(seeds)
    done = 0

    with ProcessPoolExecutor(max_workers=search.get("workers", 4)) as ex:
        futures = {}
        for seed in seeds:
            key = json.dumps([seed, context, hard, soft], sort_keys=True)
            if key in cache:
                result = cache[key]
                done += 1
                if progress_cb:
                    progress_cb(done, total)
                if result["hard_passed"]:
                    heapq.heappush(heap, (result["score"], result["seed"], result))
                    if len(heap) > top_n:
                        heapq.heappop(heap)
                continue
            futures[ex.submit(_evaluate, seed, context, hard, soft)] = key

        for fut in as_completed(futures):
            if timeout and time() - start > timeout:
                break
            result = fut.result()
            key = futures[fut]
            cache[key] = result
            done += 1
            if progress_cb:
                progress_cb(done, total)
            if result["hard_passed"]:
                heapq.heappush(heap, (result["score"], result["seed"], result))
                if len(heap) > top_n:
                    heapq.heappop(heap)

    _save_cache(cache)
    return [x[2] for x in sorted(heap, key=lambda y: y[0], reverse=True)]
