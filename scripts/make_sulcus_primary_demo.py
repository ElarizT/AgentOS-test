"""Render the 56-second, product-first Sulcus public demo video."""

from __future__ import annotations

import io
import math
import shutil
import subprocess
import sys
import wave
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "showcase"
ASSETS = OUT / "assets"
try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

if imageio_ffmpeg is not None:
    FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
else:
    discovered_ffmpeg = shutil.which("ffmpeg")
    FFMPEG = Path(discovered_ffmpeg) if discovered_ffmpeg else ROOT / ".video_tools" / "imageio_ffmpeg" / "binaries" / "ffmpeg-win-x86_64-v7.1.exe"
DASHBOARD_PATH = ASSETS / "sulcus_dashboard_current.png"

W, H = 1920, 1080
FPS = 24
DURATION = 56.0
TOTAL_FRAMES = int(DURATION * FPS)

BG = (6, 10, 16)
PANEL = (13, 21, 32)
PANEL_2 = (18, 29, 43)
WHITE = (237, 244, 255)
MUTED = (145, 164, 188)
DIM = (92, 111, 136)
CYAN = (75, 213, 255)
BLUE = (75, 124, 255)
MINT = (73, 229, 173)
AMBER = (255, 186, 80)
RED = (255, 101, 124)

FONT_REG = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_SEMIBOLD = Path(r"C:\Windows\Fonts\seguisb.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
FONT_MONO = Path(r"C:\Windows\Fonts\CascadiaMono.ttf")
if not FONT_MONO.exists():
    FONT_MONO = Path(r"C:\Windows\Fonts\consola.ttf")


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REG)
    return ImageFont.truetype(str(path), size)


F18 = font(28)
F20 = font(32)
F24 = font(40, bold=True)
F30 = font(50, bold=True)
F38 = font(64, bold=True)
F52 = font(88, bold=True)
F70 = font(116, bold=True)
MONO15 = font(24, mono=True)
MONO18 = font(29, mono=True)
MONO22 = font(35, mono=True)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def scene_alpha(t: float, start: float, end: float, fade: float = 0.45) -> float:
    return min(ease((t - start) / fade), ease((end - t) / fade))


def rgba(color: tuple[int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (*color, alpha)


def text_width(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0]


def fitted_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    start_size: int,
    min_size: int,
    mono: bool = False,
    bold: bool = False,
) -> ImageFont.FreeTypeFont:
    """Return the largest readable font that fits a single-line region."""
    for size in range(start_size, min_size - 1, -1):
        candidate = font(size, mono=mono, bold=bold)
        if text_width(draw, text, candidate) <= max_width:
            return candidate
    return font(min_size, mono=mono, bold=bold)


def center_text(draw: ImageDraw.ImageDraw, y: int, text: str, face: ImageFont.FreeTypeFont, fill=WHITE) -> None:
    draw.text(((W - text_width(draw, text, face)) // 2, y), text, font=face, fill=fill)


def background(t: float) -> Image.Image:
    image = Image.new("RGBA", (W, H), rgba(BG))
    draw = ImageDraw.Draw(image, "RGBA")
    offset = int((t * 9) % 96)
    for x in range(-96 + offset, W + 96, 96):
        draw.line((x, 0, x, H), fill=(73, 119, 162, 14), width=1)
    for y in range(-96 + offset, H + 96, 96):
        draw.line((0, y, W, y), fill=(73, 119, 162, 14), width=1)
    for i in range(18):
        x = int((149 * i + t * (12 + i % 5)) % W)
        y = int((97 * i + 173 + math.sin(t * 0.45 + i) * 32) % H)
        alpha = int(28 + 32 * (0.5 + 0.5 * math.sin(t + i)))
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=rgba(CYAN, alpha))
    return image


def brand_mark(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0, alpha: int = 255) -> None:
    colors = [BLUE, CYAN, MINT, CYAN, BLUE]
    for index, color in enumerate(colors):
        radius = (76 - index * 11) * scale
        points = []
        for step in range(80):
            angle = math.pi * (0.18 + 1.64 * step / 79)
            wobble = math.sin(angle * 3 + index * 0.7) * 5 * scale
            points.append((
                cx + math.cos(angle) * (radius + wobble),
                cy + math.sin(angle) * radius * 0.72,
            ))
        draw.line(points, fill=rgba(color, max(55, alpha - index * 22)), width=max(2, int(5 * scale)))


def glass(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent=CYAN, radius: int = 24) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 9, y1 + 13, x2 + 9, y2 + 13), radius=radius, fill=(0, 0, 0, 95))
    draw.rounded_rectangle(box, radius=radius, fill=rgba(PANEL, 246), outline=rgba(accent, 82), width=2)


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color=CYAN, face=F18) -> int:
    width = text_width(draw, text, face) + 38
    draw.rounded_rectangle((x, y, x + width, y + 50), radius=25, fill=rgba(color, 26), outline=rgba(color, 105), width=2)
    draw.text((x + 19, y + 9), text, font=face, fill=rgba(color))
    return width


def terminal(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str = "sulcus") -> None:
    x1, y1, x2, y2 = box
    glass(draw, box, accent=CYAN, radius=24)
    draw.rounded_rectangle((x1, y1, x2, y1 + 58), radius=24, fill=(20, 29, 42, 255))
    draw.rectangle((x1, y1 + 34, x2, y1 + 58), fill=(20, 29, 42, 255))
    for index, color in enumerate((RED, AMBER, MINT)):
        x = x1 + 28 + index * 28
        draw.ellipse((x, y1 + 21, x + 12, y1 + 33), fill=rgba(color))
    draw.text((x1 + 118, y1 + 15), title, font=MONO15, fill=MUTED)


def paste_dashboard(base: Image.Image, *, zoom: float = 1.0, pan_x: float = 0.5, pan_y: float = 0.5, dim: float = 0.0) -> None:
    source = DASHBOARD.copy()
    source = ImageEnhance.Contrast(source).enhance(1.08)
    source = ImageEnhance.Sharpness(source).enhance(1.25)
    source = ImageOps.fit(source, (W, H), Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    target_w = int(W * zoom)
    target_h = int(H * zoom)
    fitted = source.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = -int((target_w - W) * clamp(pan_x))
    y = -int((target_h - H) * clamp(pan_y))
    base.alpha_composite(fitted.convert("RGBA"), (x, y))
    if dim:
        shade = Image.new("RGBA", (W, H), (2, 5, 9, int(255 * dim)))
        base.alpha_composite(shade)


def safe_event_rows() -> list[tuple[str, str, str, tuple[int, int, int]]]:
    desired = [
        ("tool_execution_started", "read_source"),
        ("tool_execution_failed", "read_source"),
        ("llm_followup_request_started", None),
        ("tool_execution_completed", "read_source"),
        ("tool_call_resource_denied", "search_sources"),
        ("agent_tool_loop_completed", None),
    ]
    rows = []
    used = set()
    colors = {
        "tool_execution_failed": RED,
        "tool_call_resource_denied": AMBER,
        "tool_execution_completed": MINT,
        "agent_tool_loop_completed": CYAN,
    }
    for event_type, subject in desired:
        for index, event in enumerate(WORKFLOW.timeline):
            if index in used or event.event_type != event_type:
                continue
            if subject is not None and event.metadata.get("tool_name") != subject:
                continue
            if event_type == "agent_tool_loop_completed" and event.metadata.get("round_index") != 3:
                continue
            used.add(index)
            mode = str(event.metadata.get("effective_execution_mode") or event.metadata.get("execution_mode") or "")
            detail = str(event.metadata.get("tool_name") or event.message)
            detail += f"  mode={mode}" if mode else ""
            if event_type == "tool_execution_failed":
                detail += "  error=KeyError"
            elif event_type == "tool_call_resource_denied":
                detail = "search_sources  limit=2"
            elif event_type == "llm_followup_request_started":
                detail = "tool_results=2  failed=1"
            elif event_type == "agent_tool_loop_completed":
                detail = "research loop  round=3"
            rows.append((f"[{len(rows) + 1:02d}]", event_type, detail, colors.get(event_type, BLUE)))
            break
    return rows


def approval_rows() -> list[tuple[str, str, str, tuple[int, int, int]]]:
    desired = [
        "tool_approval_requested",
        "agent_tool_loop_paused",
        "agent_tool_loop_resumed",
        "tool_approval_denied",
        "agent_tool_loop_completed",
    ]
    colors = [AMBER, AMBER, CYAN, RED, MINT]
    rows = []
    start = next(index for index, event in enumerate(WORKFLOW.timeline) if event.event_type == "tool_approval_requested")
    for event_type, color in zip(desired, colors):
        event = next(event for event in WORKFLOW.timeline[start:] if event.event_type == event_type)
        detail = event.message
        if event_type == "tool_approval_requested":
            detail = "publish_report  call=publish-final"
        elif event_type == "tool_approval_denied":
            detail = "publish_report  side_effect_executed=false"
        rows.append((f"[{len(rows) + 1:02d}]", event_type, detail, color))
    return rows


def scene_hook(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste_dashboard(layer, zoom=1.05 + 0.035 * ease(t / 4.5), pan_x=0.58, pan_y=0.40, dim=0.34)
    gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient, "RGBA")
    for x in range(0, 1250, 10):
        alpha = int(225 * (1 - x / 1250) ** 1.7)
        gd.rectangle((x, 0, x + 10, H), fill=(4, 8, 14, alpha))
    layer.alpha_composite(gradient)
    draw = ImageDraw.Draw(layer, "RGBA")
    enter = ease(t / 0.65)
    draw.text((118, 235 + int((1 - enter) * 34)), "AGENTS SHOULDN'T", font=F52, fill=WHITE)
    draw.text((118, 335 + int((1 - enter) * 34)), "RUN UNMANAGED.", font=F52, fill=WHITE)
    draw.line((122, 476, 590, 476), fill=rgba(CYAN, 185), width=4)
    draw.text((120, 525), "Processes, not scripts.", font=F30, fill=CYAN)
    pill(draw, 120, 640, "SULCUS RUNTIME", MINT)
    return layer


def scene_launch(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.text((110, 70), "LAUNCH A REAL WORKLOAD", font=F38, fill=WHITE)
    draw.text((115, 145), "Flagship Supervised Research Team", font=F20, fill=MUTED)
    box = (105, 230, 1815, 920)
    terminal(draw, box, "Sulcus | PowerShell")
    command = "sulcus demo research-team --parallel --tight-limits --show-timeline --deny-publish"
    visible = int(len(command) * ease((t - 4.7) / 1.45))
    draw.text((150, 330), "PS> ", font=MONO22, fill=CYAN)
    command_face = fitted_font(draw, command, max_width=1525, start_size=32, min_size=25, mono=True)
    draw.text((235, 334), command[:visible], font=command_face, fill=WHITE)
    counts = Counter(event.event_type for event in WORKFLOW.timeline)
    lines = [
        ("Supervised Research Team", CYAN),
        ("execution_mode=parallel   source_set=bundled-local", WHITE),
        (f"events={sum(counts.values())}   tool_requests={counts['tool_call_requested']}   tool_failures={counts['tool_execution_failed']}", WHITE),
        (f"approvals={counts['tool_approval_requested']}   resource_denials={WORKFLOW.resource_denials}", AMBER),
        ("Publication: DENIED (report kept local)", MINT),
    ]
    local = t - 6.4
    for index, (line, color) in enumerate(lines):
        alpha = int(255 * ease((local - index * 0.55) / 0.35))
        if alpha <= 0:
            continue
        line_face = fitted_font(draw, line, max_width=1605, start_size=29, min_size=23, mono=True)
        draw.text((150, 445 + index * 72), line, font=line_face, fill=rgba(color, alpha))
    x = 114
    for label, color in (("OFFLINE", MINT), ("DETERMINISTIC", CYAN), ("NO API KEY", BLUE)):
        x += pill(draw, x, 958, label, color) + 14
    return layer


def scene_dashboard(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    local = t - 11.5
    if local < 2.8:
        zoom, focus_x, focus_y = 1.03, 0.5, 0.5
    elif local < 6.0:
        progress = ease((local - 2.8) / 0.65)
        zoom = 1.03 + 0.15 * progress
        focus_x = 0.5 + (0.12 - 0.5) * progress
        focus_y = 0.5 + (0.16 - 0.5) * progress
    elif local < 9.2:
        progress = ease((local - 6.0) / 0.65)
        zoom = 1.18
        focus_x = 0.12 + (0.88 - 0.12) * progress
        focus_y = 0.16
    else:
        progress = ease((local - 9.2) / 0.65)
        zoom = 1.18
        focus_x = 0.88 + (0.16 - 0.88) * progress
        focus_y = 0.16 + (0.84 - 0.16) * progress
    paste_dashboard(layer, zoom=zoom, pan_x=focus_x, pan_y=focus_y, dim=0.06)
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((88, 70, 759, 194), radius=24, fill=(6, 10, 16, 232), outline=rgba(CYAN, 85), width=2)
    draw.text((118, 92), "ONE RUNTIME", font=F30, fill=WHITE)
    draw.text((120, 148), "Every boundary visible.", font=F18, fill=CYAN)
    labels = [
        ("AGENT TREE", CYAN),
        ("RUNTIME TIMELINE", BLUE),
        ("PROCESSES / IPC", MINT),
        ("TOOL / LLM ACTIVITY", AMBER),
    ]
    x = 92
    for label, color in labels:
        x += pill(draw, x, 930, label, color, F18) + 12
    draw.text((1490, 1000), "BUNDLED RESEARCH TEAM", font=MONO15, fill=MUTED)
    return layer


def draw_event_rows(draw: ImageDraw.ImageDraw, rows, *, start_y: int, visible_count: float, x: int = 128) -> None:
    for index, (seq, event_type, detail, color) in enumerate(rows):
        alpha = int(255 * ease(visible_count - index))
        if alpha <= 0:
            continue
        y = start_y + index * 92
        draw.rounded_rectangle((x, y, 1305, y + 70), radius=14, fill=(17, 27, 40, min(242, alpha)), outline=rgba(color, min(100, alpha)), width=2)
        draw.text((x + 18, y + 18), seq, font=MONO15, fill=rgba(DIM, alpha))
        event_face = fitted_font(draw, event_type, max_width=420, start_size=24, min_size=20, mono=True)
        detail_face = fitted_font(draw, detail, max_width=705, start_size=24, min_size=20, mono=True)
        draw.text((x + 85, y + 19), event_type, font=event_face, fill=rgba(color, alpha))
        draw.text((x + 535, y + 19), detail, font=detail_face, fill=rgba(WHITE, alpha))


def scene_control(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.text((105, 66), "CONTROL IS PART OF EXECUTION", font=F38, fill=WHITE)
    draw.text((110, 142), "Safe runtime timeline | captured from the flagship run", font=F20, fill=MUTED)
    box = (96, 220, 1340, 945)
    terminal(draw, box, "Sulcus | Safe Runtime Timeline")
    rows = SAFE_ROWS
    draw_event_rows(draw, rows, start_y=310, visible_count=(t - 23.2) * 1.05)

    glass(draw, (1395, 260, 1818, 540), accent=RED)
    draw.text((1440, 305), "FAILURE", font=F24, fill=RED)
    draw.text((1440, 370), "recorded", font=F30, fill=WHITE)
    draw.text((1440, 430), "workflow continues", font=F18, fill=MUTED)
    draw.line((1440, 490, 1768, 490), fill=rgba(RED, 75), width=2)
    draw.text((1440, 505), "read_source -> recovery", font=MONO15, fill=RED)

    glass(draw, (1395, 600, 1818, 880), accent=AMBER)
    draw.text((1440, 645), "RESOURCE LIMIT", font=F24, fill=AMBER)
    draw.text((1440, 710), "enforced", font=F30, fill=WHITE)
    draw.text((1440, 770), "before execution", font=F18, fill=MUTED)
    draw.text((1440, 830), "search_sources <= 2", font=MONO15, fill=AMBER)
    return layer


def scene_approval(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.text((105, 66), "SIDE EFFECTS PAUSE HERE", font=F38, fill=WHITE)
    draw.text((110, 142), "Approval is an explicit pause / resume boundary.", font=F20, fill=MUTED)
    terminal(draw, (100, 230, 1815, 930), "Sulcus | Approval Boundary")
    draw_event_rows(draw, APPROVAL_ROWS, start_y=315, visible_count=(t - 34.2) * 1.08, x=130)
    local = t - 38.5
    alpha = int(255 * ease(local / 0.55))
    if alpha > 0:
        draw.rounded_rectangle((1390, 330, 1768, 695), radius=25, fill=(13, 21, 32, min(245, alpha)), outline=rgba(AMBER, min(140, alpha)), width=3)
        draw.text((1440, 385), "PUBLISH REPORT", font=F24, fill=rgba(WHITE, alpha))
        draw.text((1440, 480), "DENIED", font=F52, fill=rgba(RED, alpha))
        draw.text((1440, 600), "Report kept local", font=F20, fill=rgba(MUTED, alpha))
    draw.text((134, 854), "No pending callable executes before a complete decision set.", font=F18, fill=MUTED)
    return layer


def scene_checkpoint(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.text((105, 70), "RESTART-SAFE APPROVAL STATE", font=F38, fill=WHITE)
    draw.text((110, 146), "A fresh process resumes the saved checkpoint.", font=F20, fill=MUTED)
    terminal(draw, (100, 245, 1815, 895), "Sulcus | Persistent Checkpoint Demo")
    command = "python -m examples.agent_tool_loop_persistent_checkpoint_demo"
    draw.text((145, 345), "PS> ", font=MONO22, fill=CYAN)
    command_face = fitted_font(draw, command, max_width=1515, start_size=32, min_size=25, mono=True)
    draw.text((230, 349), command, font=command_face, fill=WHITE)
    for index, line in enumerate(CHECKPOINT_LINES[:4]):
        alpha = int(255 * ease((t - 45.0 - index * 0.62) / 0.35))
        if alpha > 0:
            color = MINT if index in (1, 3) else WHITE
            line_face = fitted_font(draw, line, max_width=1585, start_size=29, min_size=23, mono=True)
            draw.text((145, 465 + index * 77), line, font=line_face, fill=rgba(color, alpha))
    pill(draw, 112, 952, "ORIGINAL PROVIDER REQUEST NOT REPEATED", MINT)
    return layer


def scene_final(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste_dashboard(layer, zoom=1.08, pan_x=0.62, pan_y=0.46, dim=0.74)
    draw = ImageDraw.Draw(layer, "RGBA")
    local = t - 50.0
    enter = ease(local / 0.9)
    brand_mark(draw, W // 2, 290, 1.45 * enter, int(255 * enter))
    center_text(draw, 435, "SULCUS", F70, WHITE)
    center_text(draw, 585, "An operating layer for AI agents.", F30, CYAN)
    x = (W - 820) // 2
    draw.rounded_rectangle((x, 705, x + 820, 795), radius=45, fill=rgba(PANEL_2, 246), outline=rgba(CYAN, 125), width=2)
    draw.text((x + 54, 728), "github.com/ElarizT/Sulcus", font=MONO22, fill=CYAN)
    center_text(draw, 875, "RELEASE CANDIDATE | OFFLINE FLAGSHIP DEMO", F18, MUTED)
    return layer


SCENES = [
    (0.0, 4.5, scene_hook),
    (4.5, 11.5, scene_launch),
    (11.5, 23.5, scene_dashboard),
    (23.5, 34.5, scene_control),
    (34.5, 44.5, scene_approval),
    (44.5, 50.5, scene_checkpoint),
    (50.5, 56.0, scene_final),
]


def render_frame(t: float) -> Image.Image:
    frame = background(t)
    for index, (start, end, function) in enumerate(SCENES):
        is_last = index == len(SCENES) - 1
        if start <= t < end or (is_last and t <= end):
            frame = Image.alpha_composite(frame, function(t))
            break
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade, "RGBA")
    sd.rectangle((0, 0, W, 24), fill=(0, 0, 0, 75))
    sd.rectangle((0, H - 24, W, H), fill=(0, 0, 0, 80))
    return Image.alpha_composite(frame, shade).convert("RGB")


def make_music(path: Path) -> None:
    sample_rate = 48_000
    count = int(DURATION * sample_rate)
    time_axis = np.arange(count, dtype=np.float64) / sample_rate
    audio = np.zeros(count, dtype=np.float64)
    chords = [
        (65.41, 98.00, 155.56),
        (51.91, 103.83, 155.56),
        (77.78, 116.54, 174.61),
        (58.27, 87.31, 130.81),
    ]
    for index, start in enumerate(np.arange(0, DURATION, 7.0)):
        end = min(DURATION, start + 7.0)
        mask = (time_axis >= start) & (time_axis < end)
        local = time_axis[mask] - start
        envelope = np.minimum(1.0, local / 1.1) * np.minimum(1.0, (end - start - local) / 1.2)
        chord = chords[index % len(chords)]
        pad = sum(np.sin(2 * np.pi * frequency * local + offset * 0.6) for offset, frequency in enumerate(chord)) / len(chord)
        audio[mask] += envelope * 0.115 * pad
    for beat in np.arange(0.8, DURATION, 1.6):
        mask = (time_axis >= beat) & (time_axis < beat + 0.25)
        local = time_axis[mask] - beat
        audio[mask] += 0.035 * np.sin(2 * np.pi * 56 * local) * np.exp(-local * 12)
    for hit in [4.5, 11.5, 23.5, 34.5, 44.5, 50.5]:
        mask = (time_axis >= hit) & (time_axis < hit + 0.9)
        local = time_axis[mask] - hit
        audio[mask] += 0.026 * np.sin(2 * np.pi * 680 * local) * np.exp(-local * 4.2)
    audio *= np.minimum(1.0, time_axis / 1.4) * np.minimum(1.0, (DURATION - time_axis) / 2.2)
    stereo = np.stack((audio * 0.96, audio), axis=1)
    pcm = np.clip(np.tanh(stereo * 1.35) * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def render_video(silent_path: Path) -> None:
    command = [
        str(FFMPEG), "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for index in range(TOTAL_FRAMES):
            process.stdin.write(render_frame(index / FPS).tobytes())
            if index % (FPS * 5) == 0:
                print(f"Rendered {index / FPS:4.0f}s / {DURATION:.0f}s", flush=True)
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
        if return_code:
            raise RuntimeError(stderr[-5000:])
    finally:
        if process.poll() is None:
            process.kill()


def mux_audio(silent_path: Path, music_path: Path, final_path: Path) -> None:
    command = [
        str(FFMPEG), "-y", "-i", str(silent_path), "-i", str(music_path),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])


def checkpoint_output() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "examples.agent_tool_loop_persistent_checkpoint_demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def write_companion() -> None:
    (OUT / "NARRATION_AND_TIMELINE.md").write_text(
        """# Sulcus primary demo narration and timeline

## Narration script

Most agents still run as scripts: hard to inspect, constrain, or recover.

Sulcus gives agent workloads a runtime.

This offline research team plans, gathers evidence, critiques, and synthesizes through registered tools. Every model step and tool call becomes a structured runtime event.

One source read fails; the loop records it, recovers, and continues. A per-tool budget blocks an extra search before execution.

Publication pauses at an explicit approval boundary and stays local when denied.

That paused state can be saved and resumed by a fresh process without repeating the original model request.

Sulcus - an operating layer for agent systems.

The delivered video is caption-first and uses a subtle music bed without spoken narration so it remains equally effective when embedded muted. This script is timed for an optional approximately 52-second voiceover.

## Scene timeline

| Time | Scene | On-screen proof |
| --- | --- | --- |
| 0:00-0:04.5 | Hook | Current Sulcus dashboard; "Processes, not scripts." |
| 0:04.5-0:11.5 | Launch | Public sulcus demo research-team command and real run summary |
| 0:11.5-0:23.5 | Runtime | Current Agent Tree, Runtime Timeline, Processes / IPC, and Tool / LLM Activity |
| 0:23.5-0:34.5 | Control | Real failure recovery and resource-limit event rows |
| 0:34.5-0:44.5 | Approval | Real approval request, pause, denial, and completion sequence |
| 0:44.5-0:50.5 | Persistence | Real persistent-checkpoint example output |
| 0:50.5-0:56.0 | Payoff | Sulcus identity and GitHub URL |
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not FFMPEG.exists():
        raise FileNotFoundError(f"ffmpeg was not found at {FFMPEG}")
    if not DASHBOARD_PATH.exists():
        raise FileNotFoundError(f"dashboard image was not found at {DASHBOARD_PATH}")
    write_companion()
    make_music(OUT / "sulcus_primary_demo_music.wav")
    render_frame(2.2).save(OUT / "sulcus_primary_demo_thumbnail.png")
    silent = OUT / "sulcus_primary_demo_silent.mp4"
    final = OUT / "sulcus_primary_demo_polished.mp4"
    render_video(silent)
    mux_audio(silent, OUT / "sulcus_primary_demo_music.wav", final)
    print(f"Final video: {final}")


if __name__ == "__main__":
    from examples.supervised_research_team.demo import run_workflow

    WORKFLOW = run_workflow(execution_mode="parallel", tight_limits=True, approve_publish=False)
    SAFE_ROWS = safe_event_rows()
    APPROVAL_ROWS = approval_rows()
    CHECKPOINT_LINES = checkpoint_output()
    DASHBOARD = Image.open(DASHBOARD_PATH).convert("RGB")
    main()


