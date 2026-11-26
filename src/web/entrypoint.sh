#!/bin/sh
# entrypoint.sh — arranque del contenedor `web`: inicia el servidor Nginx.
# Nginx sirve los archivos estáticos generados por la compilación de Vite.
# También gestiona las peticiones /api mediante el proxy configurado en nginx.conf.

set -e

echo "Iniciando frontend..."

# Mantiene Nginx en primer plano para que Docker supervise el proceso.
exec nginx -g "daemon off;"
