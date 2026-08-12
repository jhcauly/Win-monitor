from win_monitor.models import ScenarioType, SignalDirection
from win_monitor.technical import (
    Breakout,
    Cross,
    Position,
    Slope,
    TechnicalObservation,
    evaluate_observation,
    should_defensive_exit,
)


def make_buy_observation() -> TechnicalObservation:
    return TechnicalObservation(
        readable=True,
        current_price=130500,
        ma20_slope=Slope.UP,
        price_vs_ma20=Position.ABOVE,
        ma8_vs_ma20=Position.ABOVE,
        ma8_slope=Slope.UP,
        breakout=Breakout.UP,
        relevant_top=130450,
        relevant_bottom=130100,
        candle_closed=True,
        in_consolidation=False,
        swing_confirmed=True,
        target1=130900,
        target2=131200,
    )


def test_buy_entry_requires_trend_trigger_and_breakout() -> None:
    result = evaluate_observation(make_buy_observation())
    assert result.scenario_type is ScenarioType.ENTRY
    assert result.signal is SignalDirection.BUY
    assert result.suggested_stop == 130100
    assert result.suggested_target1 == 130900


def test_price_below_ma20_blocks_buy_bias() -> None:
    observation = make_buy_observation()
    observation.price_vs_ma20 = Position.BELOW
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.NO_SETUP
    assert result.missing_confirmation_code == "M60_FRACO"


def test_ma8_touch_without_cross_is_almost() -> None:
    observation = make_buy_observation()
    observation.ma8_vs_ma20 = Position.TOUCHING
    observation.ma8_cross = Cross.NONE
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.missing_confirmation_code == "MA8_SEM_CRUZAMENTO"


def test_missing_breakout_is_almost() -> None:
    observation = make_buy_observation()
    observation.breakout = Breakout.NONE
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.missing_confirmation_code == "ROMPIMENTO_AUSENTE"


def test_sell_uses_relevant_top_as_stop() -> None:
    observation = TechnicalObservation(
        readable=True,
        current_price=129500,
        ma20_slope=Slope.DOWN,
        price_vs_ma20=Position.BELOW,
        ma8_vs_ma20=Position.BELOW,
        ma8_slope=Slope.DOWN,
        breakout=Breakout.DOWN,
        relevant_top=129900,
        relevant_bottom=129550,
        candle_closed=True,
        in_consolidation=False,
        swing_confirmed=True,
        target1=129100,
    )
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ENTRY
    assert result.signal is SignalDirection.SELL
    assert result.suggested_stop == 129900


def test_ma20_violation_forces_defensive_exit() -> None:
    observation = make_buy_observation()
    observation.price_vs_ma20 = Position.BELOW
    assert should_defensive_exit(observation, SignalDirection.BUY)


def test_contrary_ma8_cross_exits_only_when_move_is_adverse() -> None:
    observation = make_buy_observation()
    observation.ma8_cross = Cross.DOWN
    observation.moving_against_position = False
    assert not should_defensive_exit(observation, SignalDirection.BUY)

    observation.moving_against_position = True
    assert should_defensive_exit(observation, SignalDirection.BUY)


def test_visual_mapping_is_conservative_and_parses_brazilian_price() -> None:
    observation = TechnicalObservation.from_mapping(
        {
            "legivel": True,
            "preco_atual": "128.450,5",
            "ma20_inclinacao_m60": "ALTA",
            "preco_vs_ma20_m60": "TOCANDO",
            "ma8_vs_ma20_m60": "ACIMA",
            "ma8_inclinacao_m5": "ALTA",
            "ma8_cruzamento_m5": "CRUZOU_CIMA",
            "rompimento_m5": "ROMPEU_CIMA",
            "candle_fechado": True,
            "consolidacao": False,
            "pivo_confirmado": True,
        }
    )
    assert observation.current_price == 128450.5
    assert observation.ma20_slope is Slope.UP
    assert observation.price_vs_ma20 is Position.TOUCHING
    assert observation.ma8_cross is Cross.UP
