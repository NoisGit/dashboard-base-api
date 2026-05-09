# GitHub workflow para Coredeck API

Este repo ya está preparado para trabajar con ramas, commits y pull requests. Para llevar cambios a tu GitHub necesitas que el repo local tenga un remoto configurado.

## 1. Configurar el remoto una sola vez

```bash
git remote add origin git@github.com:<tu-usuario>/dashboard-base-api.git
```

Si ya existe `origin`, actualízalo:

```bash
git remote set-url origin git@github.com:<tu-usuario>/dashboard-base-api.git
```

## 2. Crear una rama de trabajo

```bash
git checkout -b portfolio/rebrand-coredeck
```

## 3. Revisar cambios antes de guardar

```bash
git status
git diff
```

## 4. Ejecutar checks locales

```bash
python -m compileall src
```

Cuando el entorno tenga dependencias instaladas y variables `.env`, también puedes ejecutar:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

## 5. Crear commit

```bash
git add .
git commit -m "Rebrand API for Coredeck portfolio"
```

## 6. Subir rama al GitHub

```bash
git push -u origin portfolio/rebrand-coredeck
```

## 7. Crear Pull Request

Desde GitHub:

1. Abre el repositorio.
2. Entra a **Pull requests**.
3. Selecciona **New pull request**.
4. Base: `main` o `develop`.
5. Compare: `portfolio/rebrand-coredeck`.
6. Describe el objetivo, cambios y checks ejecutados.
7. Crea el PR.

## Nota para trabajo asistido

En este entorno puedo modificar archivos, ejecutar checks, crear commits y generar el contenido del PR. Para que pueda subir directamente a GitHub en una sesión real, el repo debe tener configurado un remoto `origin` con credenciales disponibles en el entorno.
