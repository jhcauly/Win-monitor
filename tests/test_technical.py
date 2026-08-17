from win_monitor.models import DecisionState, ScenarioType, SignalDirection
from win_monitor.technical import (
    Breakout,
    Position,
    SetupMode,
    Slope,
    TechnicalObservation,
    evaluate_observation,
    should_defensive_exit,
)


def make_trend_buy_observation() -> TechnicalObservation:
    return TechnicalObservation(
        readable=True,
        current_price=170500,
        ma20_slope=Slope.UP,
        price_vs_ma20=Position.ABOVE,
        ma8_vs_ma20=Position.ABOVE,
        ma20_slope_m15=Slope.UP,
        price_vs_ma20_m15=Position.ABOVE,
        context_m15=Slope.UP,
        ma20_slope_m5=Slope.UP,
        price_vs_ma20_m5=Position.ABOVE,
        ma8_slope=Slope.UP,
        breakout=Breakout.UP,
        relevant_top=170450,
        relevant_bottom=170100,
        candle_closed=True,
        in_consolidation=False,
        swing_confirmed=True,
        pullback_to_ma20_m5=True,
        resumption_after_pullback_m5=True,
        setup_mode=SetupMode.TREND,
        target1=170900,
        target2=171200,
    )


def test_trend_buy_entry_requires_m5_pullback_and_higher_timeframes() -> None:
    result = evaluate_observation(make_trend_buy_observation())
    assert result.scenario_type is ScenarioType.ENTRY
    assert result.signal is SignalDirection.BUY
    assert result.decision_state is DecisionState.ENTER
    assert result.suggested_stop == 170100


def test_missing_pullback_prepares_instead_of_chasing_price() -> None:
    observation = make_trend_buy_observation()
    observation.pullback_to_ma20_m5 = False
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.decision_state is DecisionState.PREPARE
    assert result.missing_confirmation_code == "AGUARDAR_PULLBACK_MA20_M5"


def test_pullback_without_resumption_arms_but_does_not_enter() -> None:
    observation = make_trend_buy_observation()
    observation.resumption_after_pullback_m5 = False
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.decision_state is DecisionState.ARM
    assert result.missing_confirmation_code == "AGUARDAR_RETOMADA_M5"


def test_recovery_requires_minimum_space_to_ma20_m60() -> None:
    observation = make_trend_buy_observation()
    observation.setup_mode = SetupMode.RECOVERY
    observation.ma20_slope = Slope.DOWN
    observation.price_vs_ma20 = Position.BELOW
    observation.context_m15 = Slope.UP
    observation.closed_beyond_ma8_m60 = True
    observation.distance_to_ma20_m60_points = 350

    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.missing_confirmation_code == "CONTEXTO_MAIOR_NAO_CONFIRMA"


def test_recovery_is_allowed_with_space_and_m15_confirmation() -> None:
    observation = make_trend_buy_observation()
    observation.setup_mode = SetupMode.RECOVERY
    observation.ma20_slope = Slope.DOWN
    observation.price_vs_ma20 = Position.BELOW
    observation.context_m15 = Slope.UP
    observation.closed_beyond_ma8_m60 = True
    observation.distance_to_ma20_m60_points = 700

    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ENTRY
    assert result.signal is SignalDirection.BUY


def test_sell_uses_relevant_top_as_stop() -> None:
    observation = TechnicalObservation(
        readable=True,
        current_price=169500,
        ma20_slope=Slope.DOWN,
        price_vs_ma20=Position.BELOW,
        ma8_vs_ma20=Position.BELOW,
        ma20_slope_m15=Slope.DOWN,
        price_vs_ma20_m15=Position.BELOW,
        context_m15=Slope.DOWN,
        ma20_slope_m5=Slope.DOWN,
        price_vs_ma20_m5=Position.BELOW,
        ma8_slope=Slope.DOWN,
        breakout=Breakout.DOWN,
        relevant_top=169900,
        relevant_bottom=169450,
        candle_closed=True,
        in_consolidation=False,
        swing_confirmed=True,
        pullback_to_ma20_m5=True,
        resumption_after_pullback_m5=True,
        setup_mode=SetupMode.TREND,
        target1=169100,
    )
    result = evaluate_observation(observation)
    assert result.scenario_type is ScenarioType.ENTRY
    assert result.signal is SignalDirection.SELL
    assert result.suggested_stop == 169900


def test_ma20_m5_violation_forces_defensive_exit() -> None:
    observation = make_trend_buy_observation()
    observation.price_vs_ma20_m5 = Position.BELOW
    assert should_defensive_exit(observation, SignalDirection.BUY)


def test_visual_mapping_parses_projected_timeframes() -> None:
    observation = TechnicalObservation.from_mapping(
        {
            "legivel": True,
            "preco_atual": "170.450,5",
            "ma20_inclinacao_m60": "BAIXA",
            "preco_vs_ma20_m60": "ABAIXO",
            "ma8_vs_ma20_m60": "ABAIXO",
            "fechou_alem_ma8_m60": True,
            "distancia_ma20_m60_pontos": 620,
            "ma20_inclinacao_m15": "ALTA",
            "preco_vs_ma20_m15": "ACIMA",
            "contexto_m15": "ALTA",
            "ma20_inclinacao_m5": "ALTA",
            "preco_vs_ma20_m5": "ACIMA",
            "ma8_inclinacao_m5": "ALTA",
            "rompimento_m5": "ROMPEU_CIMA",
            "retorno_ma20_m5": True,
            "retomada_apos_correcao_m5": True,
            "candle_fechado": True,
            "consolidacao": False,
            "pivo_confirmado": True,
            "modo_setup": "RECOVERY",
        }
    )
    assert observation.current_price == 170450.5
    assert observation.context_m15 is Slope.UP
    assert observation.setup_mode is SetupMode.RECOVERY
    assert observation.distance_to_ma20_m60_points == 620
