from __future__ import annotations

from win_monitor.models import AnalysisResult, ScenarioType, TradeRisk


def telegram_caption(analysis: AnalysisResult, risk: TradeRisk | None = None) -> str:
    emoji = {ScenarioType.ENTRY: "🟢", ScenarioType.ALMOST: "🟡", ScenarioType.NO_SETUP: "⚪", ScenarioType.RESULT: "🔵"}.get(analysis.scenario_type, "⚪")
    lines = [f"{emoji} <b>{analysis.scenario_type.value}</b> — {analysis.signal.value} ({analysis.confidence.value})"]
    if analysis.scenario_type is ScenarioType.ALMOST:
        code = analysis.missing_confirmation_code or "NAO_INFORMADO"
        lines.append(f"❓ <b>{code}</b>: {analysis.missing_confirmation or '-'}")
    if risk:
        lines.append(f"🛡 Risco: {risk.risk_points:.0f} pts | {risk.recommended_contracts} contrato(s) | R${risk.recommended_risk_brl:.2f}")
    lines.append(f"💬 {analysis.rationale}")
    return "\n".join(lines)
