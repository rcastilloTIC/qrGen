# QR Studio

Servicio Docker con FastAPI para generar códigos QR a partir de una URL.

## Arranque

```bash
docker compose up --build
```

Abre `http://localhost:8000`.

## API

Ejemplo:

```text
GET /api/qr?url=https://example.com&format=png&box_size=10&border=4&error=M&foreground=%23111827&background=%23ffffff
```

Opciones:
- `format`: `png` o `svg`
- `box_size`: 2-40
- `border`: 0-20
- `error`: `L`, `M`, `Q`, `H`
- `foreground`: color hexadecimal
- `background`: color hexadecimal

Healthcheck:

```text
GET /health
```
# qrGen
