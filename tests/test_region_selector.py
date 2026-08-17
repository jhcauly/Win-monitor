from win_monitor.region_selector import normalize_bbox


def test_normalize_bbox_forward_drag() -> None:
    assert normalize_bbox((10, 20), (110, 220)) == (10, 20, 110, 220)


def test_normalize_bbox_reverse_drag() -> None:
    assert normalize_bbox((110, 220), (10, 20)) == (10, 20, 110, 220)
