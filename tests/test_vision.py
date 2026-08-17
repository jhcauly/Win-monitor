from win_monitor.vision import parse_json_response


def test_parse_fenced_json() -> None:
    payload = parse_json_response('```json\n{"tipo_cenario":"SEM_SETUP"}\n```')
    assert payload["tipo_cenario"] == "SEM_SETUP"


def test_parse_json_with_extra_text() -> None:
    payload = parse_json_response('resultado: {"tipo_cenario":"QUASE"} fim')
    assert payload["tipo_cenario"] == "QUASE"
