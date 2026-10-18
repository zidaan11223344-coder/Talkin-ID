import treasure_game as game


def test_mining_cooldown_and_inventory_are_persistent(tmp_path, monkeypatch):
    monkeypatch.setattr(game, 'DATA_PATH', tmp_path / 'treasures.json')
    monkeypatch.setattr(game.random, 'choices', lambda population, weights, k: ['نحاس'])
    first = game.mine('user-1', 'Player', now=10000)
    assert first['ok'] and first['found'] and first['item'] == 'نحاس'
    assert game.inventory('user-1', 'Player')['نحاس'] == 1
    again = game.mine('user-1', 'Player', now=10001)
    assert not again['ok'] and again['remaining'] == game.COOLDOWN_SECONDS - 1


def test_diamond_leaderboard_tracks_found_even_after_redemption(tmp_path, monkeypatch):
    monkeypatch.setattr(game, 'DATA_PATH', tmp_path / 'treasures.json')
    monkeypatch.setattr(game.random, 'choices', lambda population, weights, k: ['الماس_ملكي'])
    result = game.mine('user-2', 'Player Two', now=20000)
    assert result['diamond']
    assert game.leaderboard()[0] == (1, 'Player Two')
    redeemed = game.begin_redemption('user-2', 'Player Two', 'الماس الملكي')
    assert redeemed['ok'] and redeemed['quantity'] == 1 and redeemed['points'] == 5000
    game.finish_redemption(redeemed['txid'], True)
    assert game.inventory('user-2')['الماس_ملكي'] == 0
    assert game.leaderboard()[0] == (1, 'Player Two')


def test_failed_redemption_restores_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(game, 'DATA_PATH', tmp_path / 'treasures.json')
    monkeypatch.setattr(game.random, 'choices', lambda population, weights, k: ['حديد'])
    game.mine('user-3', 'Player Three', now=30000)
    redeemed = game.begin_redemption('user-3', 'Player Three', 'حديد')
    game.finish_redemption(redeemed['txid'], False)
    assert game.inventory('user-3')['حديد'] == 1
