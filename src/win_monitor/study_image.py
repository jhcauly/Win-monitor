from __future__ import annotations

import io
import textwrap
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from win_monitor.models import AnalysisResult, ScenarioType, TradeRisk


class StudyImageComposer:
    def compose(self, screenshot_bytes: bytes, analysis: AnalysisResult, risk: TradeRisk | None = None) -> bytes:
        original = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        panel_height = 330 if risk else 285
        panel = Image.new("RGB", (original.width, panel_height), (18, 18, 18))
        draw = ImageDraw.Draw(panel)
        title_font, text_font = self._fonts()
        colors = {ScenarioType.ENTRY:(80,220,100), ScenarioType.ALMOST:(230,190,60), ScenarioType.NO_SETUP:(150,150,150), ScenarioType.RESULT:(120,190,255)}
        y = 12
        draw.text((16,y), f"{analysis.scenario_type.value} - {analysis.signal.value} ({analysis.confidence.value}) | {datetime.now().strftime('%d/%m %H:%M')}", font=title_font, fill=colors.get(analysis.scenario_type,(200,200,200)))
        y += 38
        lines = [f"Vies M60: {analysis.bias_m60}", f"Estrutura M15: {analysis.structure_m15}", f"Zona Fibo M5: {analysis.fib_zone_m5}"]
        if analysis.scenario_type is ScenarioType.ENTRY:
            lines.append(f"Entrada: {analysis.suggested_entry} | Stop: {analysis.suggested_stop} | Alvo1: {analysis.suggested_target1} | Alvo2: {analysis.suggested_target2}")
        elif analysis.scenario_type is ScenarioType.ALMOST:
            lines.append(f"Faltou [{analysis.missing_confirmation_code or 'NAO_INFORMADO'}]: {analysis.missing_confirmation or '-'}")
        if risk:
            lines.append(f"Risco: {risk.risk_points:.0f} pts | 1 contrato: R${risk.risk_per_contract_brl:.2f} | 5 contratos: R${risk.risk_five_contracts_brl:.2f}")
            lines.append(f"Quantidade recomendada: {risk.recommended_contracts} | Risco recomendado: R${risk.recommended_risk_brl:.2f}")
        for line in lines:
            for wrapped in textwrap.wrap(line, width=130) or [""]:
                draw.text((16,y), wrapped, font=text_font, fill=(230,230,230)); y += 23
        y += 5
        for wrapped in textwrap.wrap(analysis.rationale, width=115):
            draw.text((16,y), wrapped, font=text_font, fill=(180,200,255)); y += 22
        final = Image.new("RGB", (original.width, original.height + panel_height), (18,18,18))
        final.paste(original, (0,0)); final.paste(panel, (0, original.height))
        buffer = io.BytesIO(); final.save(buffer, format="PNG"); return buffer.getvalue()

    @staticmethod
    def _fonts() -> tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
        for title_name, text_name in [("DejaVuSans-Bold.ttf","DejaVuSans.ttf"),("arialbd.ttf","arial.ttf")]:
            try:
                return ImageFont.truetype(title_name,22), ImageFont.truetype(text_name,16)
            except OSError:
                continue
        return ImageFont.load_default(), ImageFont.load_default()
