from html import escape
from io import BytesIO
import re
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageColor, ImageDraw
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

app = FastAPI(title="QR Studio", version="1.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_url(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="La URL debe empezar por http:// o https://")
    return value


def validate_color(value: str, field: str) -> str:
    if not HEX_COLOR.fullmatch(value):
        raise HTTPException(status_code=400, detail=f"Color inválido en {field}. Usa formato #RRGGBB")
    return value.lower()


def build_qr(data: str, box_size: int, border: int, error: str):
    if error not in ERROR_LEVELS:
        raise HTTPException(status_code=400, detail="Nivel de corrección inválido")
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_LEVELS[error],
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def render_png(qr, box_size: int, foreground: str, background: str, transparent: bool) -> bytes:
    matrix = qr.get_matrix()
    modules = len(matrix)
    size = modules * box_size

    fg = ImageColor.getrgb(foreground) + (255,)
    bg = (0, 0, 0, 0) if transparent else ImageColor.getrgb(background) + (255,)

    image = Image.new("RGBA", (size, size), bg)
    draw = ImageDraw.Draw(image)

    for row_index, row in enumerate(matrix):
        y0 = row_index * box_size
        for col_index, dark in enumerate(row):
            if dark:
                x0 = col_index * box_size
                draw.rectangle(
                    (x0, y0, x0 + box_size - 1, y0 + box_size - 1),
                    fill=fg,
                )

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def render_svg(qr, box_size: int, foreground: str, background: str, transparent: bool) -> bytes:
    matrix = qr.get_matrix()
    modules = len(matrix)
    size = modules * box_size

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 {size} {size}" shape-rendering="crispEdges">'
        ),
    ]

    if not transparent:
        parts.append(f'<rect width="100%" height="100%" fill="{escape(background)}"/>')

    parts.append(f'<g fill="{escape(foreground)}">')
    for row_index, row in enumerate(matrix):
        y = row_index * box_size
        for col_index, dark in enumerate(row):
            if dark:
                x = col_index * box_size
                parts.append(f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}"/>')
    parts.append("</g></svg>")
    return "".join(parts).encode("utf-8")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/qr")
def qr_api(
    url: str = Query(..., description="URL a codificar"),
    format: str = Query("png", pattern="^(png|svg)$"),
    box_size: int = Query(10, ge=2, le=40),
    border: int = Query(4, ge=0, le=20),
    error: str = Query("M", pattern="^[LMQH]$"),
    foreground: str = Query("#111827"),
    background: str = Query("#ffffff"),
    transparent: bool = Query(False),
):
    url = validate_url(url)
    foreground = validate_color(foreground, "foreground")
    background = validate_color(background, "background")
    qr = build_qr(url, box_size, border, error)

    if format == "svg":
        content = render_svg(qr, box_size, foreground, background, transparent)
        return Response(content, media_type="image/svg+xml")

    content = render_png(qr, box_size, foreground, background, transparent)
    return Response(content, media_type="image/png")


@app.post("/generate")
def generate(
    url: str = Form(...),
    format: str = Form("png"),
    box_size: int = Form(10),
    border: int = Form(4),
    error: str = Form("M"),
    foreground: str = Form("#111827"),
    background: str = Form("#ffffff"),
    transparent: bool = Form(False),
):
    return qr_api(url, format, box_size, border, error, foreground, background, transparent)
