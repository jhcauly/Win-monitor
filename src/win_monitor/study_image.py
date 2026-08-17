from __future__ import annotations

import io
import textwrap
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from win_monitor.models import AnalysisResult, ScenarioType, SignalDirection, TradeRisk


class StudyImageComposer:
    """Compose an auditable study image without modifying the trading platform."""

    def compose(
        self,
        screenshot_bytes: bytes,
        analysis: AnalysisResult,
        risk: TradeRisk | None = None,
    ) -> bytes:
        original = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        annotated = original.copy()
        draw = ImageDraw.Draw(annotated)
        title_font, text_font = self._fonts()

        self._draw_markers(draw, annotated.size, analysis, title_font, text_font)
        self._draw_trade_levels(draw, annotated.size, analysis, title_font, text_font)
        self._draw_status_badge(draw, analysis, title_font, text_font)

        panel_height = 410 if risk else 350
        panel = Image.new("RGB", (original.width, panel_height), (18, 18, 18))
        panel_draw = ImageDraw.Draw(panel)
        self._draw_explanation(panel_draw, original.width, analysis, risk, title_font, text_font)

        final = Image.new(
            "RGB",
            (original.width, original.height + panel_height),
            (18, 18, 18),
        )
        final.paste(annotated, (0, 0))
        final.paste(panel, (0, original.height))
        buffer = io.BytesIO()
        final.save(buffer, format="PNG")
        return buffer.getvalue()

    def _draw_markers(self, draw, size, analysis, title_font, text_font) -> None:
        width, height = size
        palette = {
            "PIVO": (255, 200, 40),
            "CORRECAO": (80, 190, 255),
            "MM20": (90, 210, 255),
            "GATILHO": (80, 230, 120),
            "ENTRADA": (40, 230, 100),
            "STOP": (245, 75, 75),
            "ALVO": (80, 180, 255),
            "TOPO": (255, 200, 40),
            "FUNDO": (255, 200, 40),
        }
        for marker in analysis.visual_markers:
            x = int(width * float(marker["x"]) / 1000.0)
            y = int(height * float(marker["y"]) / 1000.0)
            kind = str(marker.get("tipo") or "PONTO").upper()
            label = str(marker.get("rotulo") or kind)
            timeframe = str(marker.get("timeframe") or "")
            color = palette.get(kind, (255, 215, 80))
            radius = max(7, width // 170)
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=4)
            end_y = max(20, y - 65)
            draw.line((x, y-radius, x, end_y), fill=color, width=3)
            caption = f"{timeframe} {label}".strip()
            box = draw.textbbox((0, 0), caption, font=text_font)
            tw = box[2] - box[0]
            th = box[3] - box[1]
            tx = max(4, min(width - tw - 12, x - tw // 2))
            ty = max(4, end_y - th - 10)
            draw.rounded_rectangle((tx-5, ty-4, tx+tw+5, ty+th+4), radius=5, fill=(10,10,10), outline=color, width=2)
            draw.text((tx, ty), caption, font=text_font, fill=color)

    def _draw_trade_levels(self, draw, size, analysis, title_font, text_font) -> None:
        width, height = size
        levels = []
        if analysis.suggested_entry is not None:
            levels.append(("ENTRADA", analysis.suggested_entry, (40, 230, 100)))
        if analysis.suggested_stop is not None:
            levels.append(("STOP", analysis.suggested_stop, (245, 75, 75)))
        if analysis.suggested_target1 is not None:
            levels.append(("ALVO 1", analysis.suggested_target1, (80, 180, 255)))
        if analysis.suggested_target2 is not None:
            levels.append(("ALVO 2", analysis.suggested_target2, (120, 205, 255)))
        if not levels:
            return

        prices = [value for _, value, _ in levels]
        if analysis.current_price is not None:
            prices.append(analysis.current_price)
        lo, hi = min(prices), max(prices)
        spread = max(hi - lo, 1.0)
        chart_top = int(height * 0.12)
        chart_bottom = int(height * 0.86)
        for label, price, color in levels:
            ratio = (hi - price) / spread
            y = int(chart_top + ratio * (chart_bottom - chart_top))
            draw.line((0, y, width, y), fill=color, width=3)
            caption = f"{label} {price:.0f}"
            bbox = draw.textbbox((0, 0), caption, font=title_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.rectangle((width-tw-22, y-th-9, width-4, y+5), fill=(8,8,8), outline=color, width=2)
            draw.text((width-tw-13, y-th-5), caption, font=title_font, fill=color)

    def _draw_status_badge(self, draw, analysis, title_font, text_font) -> None:
        colors = {
            "AGUARDAR": (150, 150, 150),
            "PREPARAR": (235, 190, 55),
            "ARMAR": (255, 150, 50),
            "ENTRAR": (60, 225, 105),
            "GERENCIAR": (80, 180, 255),
        }
        state = analysis.decision_state.value
        color = colors.get(state, (190, 190, 190))
        text = f"ESTADO: {state} | {analysis.signal.value}"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.rounded_rectangle((12, 12, tw+34, th+30), radius=8, fill=(8,8,8), outline=color, width=3)
        draw.text((23, 20), text, font=title_font, fill=color)

    def _draw_explanation(self, draw, width, analysis, risk, title_font, text_font) -> None:
        colors = {
            ScenarioType.ENTRY: (80, 220, 100),
            ScenarioType.ALMOST: (230, 190, 60),
            ScenarioType.NO_SETUP: (150, 150, 150),
            ScenarioType.RESULT: (120, 190, 255),
        }
        y = 12
        title = (
            f"{analysis.decision_state.value} | {analysis.scenario_type.value} - "
            f"{analysis.signal.value} ({analysis.confidence.value}) | "
            f"{datetime.now().strftime('%d/%m %H:%M')}"
        )
        draw.text((16, y), title, font=title_font, fill=colors.get(analysis.scenario_type, (200,200,200)))
        y += 38

        lines = [
            f"60 MIN - CONTEXTO: {analysis.bias_m60}",
            f"15 MIN - ESTRUTURA: {analysis.structure_m15}",
            f"5 MIN - GATILHO/CORRECAO: {analysis.fib_zone_m5}",
        ]
        if analysis.scenario_type is ScenarioType.ENTRY:
            lines.append(
                f"PLANO: entrada {analysis.suggested_entry} | stop {analysis.suggested_stop} | "
                f"alvo1 {analysis.suggested_target1} | alvo2 {analysis.suggested_target2}"
            )
        elif analysis.missing_confirmation:
            lines.append(
                f"O QUE FALTA: [{analysis.missing_confirmation_code or 'NA'}] "
                f"{analysis.missing_confirmation}"
            )

        if risk:
            lines.extend([
                f"RISCO: {risk.risk_points:.0f} pts | 1 contrato R${risk.risk_per_contract_brl:.2f} | 5 contratos R${risk.risk_five_contracts_brl:.2f}",
                f"GESTAO: quantidade recomendada {risk.recommended_contracts} | risco recomendado R${risk.recommended_risk_brl:.2f}",
            ])

        wrap_width = max(60, width // 11)
        for line in lines:
            for wrapped in textwrap.wrap(line, width=wrap_width) or [""]:
                draw.text((16, y), wrapped, font=text_font, fill=(230,230,230))
                y += 23

        y += 6
        draw.text((16, y), "LEITURA:", font=title_font, fill=(180,200,255))
        y += 30
        for wrapped in textwrap.wrap(analysis.rationale, width=wrap_width):
            draw.text((16, y), wrapped, font=text_font, fill=(180,200,255))
            y += 22

    @staticmethod
    def _fonts() -> tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
        candidates = [
            ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"),
            ("arialbd.ttf", "arial.ttf"),
        ]
        for title_name, text_name in candidates:
            try:
                return ImageFont.truetype(title_name, 22), ImageFont.truetype(text_name, 16)
            except OSError:
                continue
        return ImageFont.load_default(), ImageFont.load_default()
