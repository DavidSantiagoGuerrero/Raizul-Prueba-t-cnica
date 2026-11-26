# Dockerfile de la web: construye la aplicación React con Vite y la sirve usando Nginx.
# Primero instala las dependencias y genera la versión de producción.
# Al finalizar copia los archivos compilados y la configuración de Nginx a la imagen final.

# Etapa de construcción
FROM node:22-alpine AS builder

WORKDIR /app

# Copia los archivos de dependencias e instala los paquetes.
COPY package*.json ./
RUN npm ci

# Copia el código fuente y construye la aplicación.
COPY . .
RUN npm run build

# Etapa de producción
FROM nginx:alpine

# Copia los archivos compilados de Vite al directorio público de Nginx.
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia la configuración del servidor y el script de inicio.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh

# Da permisos de ejecución al entrypoint.
RUN chmod +x /entrypoint.sh

# Expone el puerto HTTP de Nginx.
EXPOSE 80

# Al iniciar ejecuta entrypoint.sh para levantar Nginx.
ENTRYPOINT ["/entrypoint.sh"]
