# QR Studio

Servicio web en Python/FastAPI para generar códigos QR configurables desde una URL.

## Arranque

```bash
docker compose up --build
```

Abre `http://localhost:8000`.

## Opciones

- PNG o SVG
- Tamaño de módulo y margen
- Corrección de errores L/M/Q/H
- Color del QR y del fondo
- **Fondo transparente real en PNG (RGBA) y SVG**

## API

```text
GET /api/qr?url=https://example.com&format=png&box_size=10&border=4&error=M&foreground=%23111827&background=%23ffffff&transparent=true
```

`transparent=true` elimina el fondo. En PNG genera un canal alfa real; en SVG no se dibuja ningún fondo.
