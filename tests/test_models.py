from win_monitor.models import AnalysisResult, ScenarioType


def test_incomplete_entry_is_downgraded_to_almost() -> None:
    result = AnalysisResult.from_mapping(
        {
            "tipo_cenario": "ENTRADA",
            "sinal": "COMPRA",
            "confianca": "ALTA",
            "entrada_sugerida": 130000,
            "stop_sugerido": None,
            "alvo1_sugerido": 130500,
            "justificativa": "Setup visual.",
        }
    )
    assert result.scenario_type is ScenarioType.ALMOST
    assert result.missing_confirmation_code == "PLANO_INCOMPLETO"


def test_brazilian_thousands_separator_is_parsed() -> None:
    result = AnalysisResult.from_mapping(
        {
            "tipo_cenario": "SEM_SETUP",
            "sinal": "NENHUM",
            "confianca": "MEDIA",
            "preco_atual": "128.450",
        }
    )
    assert result.current_price == 128450.0


def test_brazilian_decimal_format_is_parsed() -> None:
    result = AnalysisResult.from_mapping(
        {
            "tipo_cenario": "SEM_SETUP",
            "sinal": "NENHUM",
            "confianca": "MEDIA",
            "preco_atual": "128.450,5",
        }
    )
    assert result.current_price == 128450.5
