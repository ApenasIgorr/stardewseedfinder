from __future__ import annotations

import random
from typing import Any

from core.predictor_adapter.base import PredictionBundle, PredictorAdapter

SEASONS = ["spring", "summer", "fall", "winter"]
TRAVELING_ITEMS = [
    "Red Cabbage Seed",
    "Rare Seed",
    "Coffee Bean",
    "Battery Pack",
    "Pufferfish",
    "Rabbit's Foot",
    "Dino Egg",
    "Truffle Oil",
]
EVENTS = ["fairy", "witch", "meteor", "owl", "none"]
GEODE_ITEMS = ["Clay", "Copper Ore", "Iron Ore", "Dino Egg", "Prismatic Shard", "Coal"]
BOX_ITEMS = ["Bait", "Coffee", "Bomb", "Iridium Bar", "Pearl"]
COCONUT_ITEMS = ["Golden Coconut", "Mango Sapling", "Banana Sapling", "Taro Tuber"]


class V16Simulator(PredictorAdapter):
    def predict(self, seed: int, context: dict[str, Any]) -> PredictionBundle:
        weather = {}
        cart = []
        events = []
        trains = []
        garbage = []

        for year in range(1, 3):
            for season_idx, season in enumerate(SEASONS):
                for day in range(1, 29):
                    key = f"Y{year}-{season}-{day}"
                    r = random.Random(seed * 97 + year * 7919 + season_idx * 379 + day)
                    if context.get("game_version", "1.6.x").startswith("1.6") and season == "summer" and day == 5 and r.random() < 0.2:
                        weather[key] = "green_rain"
                    else:
                        weather[key] = "rain" if r.random() < 0.24 else "sunny"

                    if day % 2 == 0:
                        item_rng = random.Random(seed * 31 + year * 47 + season_idx * 89 + day)
                        item = item_rng.choice(TRAVELING_ITEMS)
                        cart.append(
                            {
                                "year": year,
                                "season": season,
                                "day": day,
                                "item": item,
                                "price": 100 + item_rng.randint(0, 2500),
                            }
                        )

                    ev_rng = random.Random(seed * 101 + year * 733 + season_idx * 59 + day)
                    ev = ev_rng.choice(EVENTS)
                    if ev != "none" and ev_rng.random() < 0.09:
                        events.append({"year": year, "season": season, "day": day, "event": ev})

                    train_rng = random.Random(seed * 13 + year * 17 + season_idx * 19 + day)
                    if train_rng.random() < 0.15:
                        trains.append(
                            {
                                "year": year,
                                "season": season,
                                "day": day,
                                "time": f"{9 + train_rng.randint(0, 11)}:{train_rng.choice(['00','10','20','30','40','50'])}",
                            }
                        )

                    garbage_rng = random.Random(seed * 211 + year * 23 + season_idx * 31 + day)
                    garbage.append(
                        {
                            "year": year,
                            "season": season,
                            "day": day,
                            "drop": garbage_rng.choice(["none", "bread", "dish o' the sea", "cookie", "coal"]),
                        }
                    )

        seq_geode = [random.Random(seed + i * 11).choice(GEODE_ITEMS) for i in range(1, 301)]
        seq_box = [random.Random(seed + i * 17).choice(BOX_ITEMS) for i in range(1, 301)]
        seq_coconut = [random.Random(seed + i * 23).choice(COCONUT_ITEMS) for i in range(1, 301)]

        return PredictionBundle(
            supported_features={
                "weather": True,
                "traveling_cart": True,
                "night_events": True,
                "train": True,
                "garbage_cans": True,
                "geodes": True,
                "mystery_boxes": True,
                "golden_coconuts": True,
                "prize_tickets": False,
                "raccoon_requests": False,
                "shop_rng": False,
            },
            weather=weather,
            traveling_cart=cart,
            night_events=events,
            trains=trains,
            garbage_cans=garbage,
            sequences={"geode": seq_geode, "mystery_box": seq_box, "golden_coconut": seq_coconut},
        )
