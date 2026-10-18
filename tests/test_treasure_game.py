import treasure_game as game


def _set_game_data(tmp_path, monkeypatch, *, spawn_time, ordinary_item="نحاس"):
    monkeypatch.setattr(game, "DATA_PATH", tmp_path / "treasures.json")
    monkeypatch.setattr(game.random, "uniform", lambda low, high: spawn_time(low, high))

    def choose(population, weights, k):
        if "الماس_ملكي" in population:
            return ["الماس_ملكي"]
        return [ordinary_item]

    monkeypatch.setattr(game.random, "choices", choose)


def test_mining_cooldown_is_30_seconds_and_inventory_persists(tmp_path, monkeypatch):
    _set_game_data(tmp_path, monkeypatch, spawn_time=lambda low, high: high)
    first = game.mine("user-1", "Player", now=10000)
    assert first["ok"] and first["found"] and first["item"] == "نحاس"
    assert game.inventory("user-1", "Player")["نحاس"] == 1

    too_soon = game.mine("user-1", "Player", now=10001)
    assert not too_soon["ok"] and too_soon["remaining"] == 29

    ready = game.mine("user-1", "Player", now=10030)
    assert ready["ok"]
    assert game.inventory("user-1", "Player")["نحاس"] == 2


def test_first_miner_after_random_spawn_gets_diamond(tmp_path, monkeypatch):
    _set_game_data(tmp_path, monkeypatch, spawn_time=lambda low, high: low)
    result = game.mine("user-2", "Player Two", now=20000)
    assert result["ok"] and result["diamond"] and result["item"] == "الماس_ملكي"
    assert game.leaderboard()[0] == (1, "Player Two")

    redeemed = game.begin_redemption("user-2", "Player Two", "الماس الملكي")
    assert redeemed["ok"] and redeemed["quantity"] == 1 and redeemed["points"] == 5000
    game.finish_redemption(redeemed["txid"], True)
    assert game.inventory("user-2")["الماس_ملكي"] == 0
    assert game.leaderboard()[0] == (1, "Player Two")


def test_only_15_diamonds_spawn_in_each_24_hour_cycle(tmp_path, monkeypatch):
    _set_game_data(tmp_path, monkeypatch, spawn_time=lambda low, high: low)
    results = [game.mine(f"miner-{i}", f"Miner {i}", now=30000) for i in range(15)]
    assert sum(bool(result.get("diamond")) for result in results) == game.DAILY_DIAMOND_SPAWNS

    next_result = game.mine("miner-extra", "Extra Miner", now=30000)
    assert next_result["ok"] and not next_result.get("diamond")


def test_failed_redemption_restores_inventory(tmp_path, monkeypatch):
    _set_game_data(tmp_path, monkeypatch, spawn_time=lambda low, high: high, ordinary_item="حديد")
    game.mine("user-3", "Player Three", now=40000)
    redeemed = game.begin_redemption("user-3", "Player Three", "حديد")
    game.finish_redemption(redeemed["txid"], False)
    assert game.inventory("user-3")["حديد"] == 1


def test_format_cooldown_shows_seconds():
    assert game.format_cooldown(30) == "30 ثانية"
    assert game.format_cooldown(61) == "1 دقيقة و1 ثانية"


def test_test_diamond_grant_cycles_types_and_persists_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(game, "DATA_PATH", tmp_path / "treasures.json")
    first_cycle = [game.give_test_diamond("master", "Master") for _ in game.DIAMOND_KEYS]
    assert [result["item"] for result in first_cycle] == game.DIAMOND_KEYS

    next_result = game.give_test_diamond("master", "Master")
    assert next_result["item"] == game.DIAMOND_KEYS[0]
    inventory = game.inventory("master", "Master")
    assert inventory[game.DIAMOND_KEYS[0]] == 2
    assert game.leaderboard()[0] == (len(game.DIAMOND_KEYS) + 1, "Master")
