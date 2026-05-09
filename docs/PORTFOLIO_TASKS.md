# Coredeck API Portfolio Task Plan

## Objetivo

Convertir este backend en un proyecto de portafolio independiente, sin rastros de marcas, productos o colaboradores anteriores, manteniendo la estructura modular existente de FastAPI, routers, schemas, services, models y migraciones.

## Tareas realizadas en esta iteración

- [x] Eliminar referencias visibles a la identidad anterior y consolidar el nombre `Coredeck API`.
- [x] Reemplazar textos de la identidad anterior en plantillas HTML, Docker y documentación.
- [x] Quitar atribuciones personales del README para presentar el repo como proyecto independiente de portafolio.
- [x] Cambiar credenciales hardcodeadas del `docker-compose.yml` por variables de entorno con defaults locales no productivos.
- [x] Agregar `.env.example` para documentar configuración local sin subir secretos reales.
- [x] Ajustar endpoints públicos con nombres más genéricos orientados a agentes de plataforma (`agent`) en lugar de dominios de control de acceso físico.
- [x] Documentar el plan de transformación a portafolio para continuar el refactor sin romper todo de una vez.

## Tareas siguientes recomendadas

### 1. Dominio genérico

- [ ] Renombrar `companies` a `organizations`.
- [ ] Renombrar `locations` a `workspaces`.
- [ ] Renombrar `access_logs` a `activity_logs`.
- [ ] Renombrar `whitelists` a `allowlists`.
- [ ] Renombrar `blacklists` a `blocklists`.
- [ ] Revisar migraciones históricas del rol `AGENT` antes de conectar bases de datos existentes.

### 2. Contrato API de portafolio

- [ ] Exponer endpoints finales bajo `/api/v1/organizations`, `/api/v1/workspaces`, `/api/v1/projects`, `/api/v1/activity-logs`.
- [ ] Mantener aliases temporales para rutas legacy mientras el frontend migra.
- [ ] Publicar una colección OpenAPI/Postman para demo.

### 3. Seguridad y despliegue

- [ ] Validar `SECRET_KEY` obligatorio en runtime.
- [ ] Restringir CORS por `BACKEND_CORS_ORIGINS`.
- [ ] Documentar variables de entorno por ambiente.
- [ ] Añadir pipeline de lint/test.
- [ ] Crear Dockerfile de producción.

### 4. Presentación de portafolio

- [ ] Agregar capturas de Swagger/OpenAPI y arquitectura.
- [ ] Añadir sección “What this project demonstrates” al README.
- [ ] Añadir diagrama simple de módulos.
- [ ] Conectar demo frontend `dashboard-base` con este backend.

## Criterio de avance

El refactor debe hacerse por capas pequeñas para conservar estabilidad:

1. Rebrand visible y documentación.
2. Seguridad/configuración.
3. Rutas públicas.
4. Schemas y services.
5. Models y migraciones.
6. Frontend alignment.
