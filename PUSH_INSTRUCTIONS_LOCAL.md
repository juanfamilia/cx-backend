# Instrucciones para Push Local

## En tu máquina local (NO en Emergent):

```bash
# 1. Clona o actualiza el repo
git clone https://github.com/juanfamilia/cx-backend.git
cd cx-backend

# 2. Cambia al branch
git checkout phase0-4-enhancements1

# 3. Pull los cambios que hicimos
git pull origin phase0-4-enhancements1

# 4. Verifica que tienes el commit ae2d3e2
git log --oneline -3

# Deberías ver:
# ae2d3e2 fix: resolve Railway deployment - async engine and port config

# 5. Si no lo ves, los cambios están solo en Emergent
# En ese caso, necesitas usar "Save to GitHub" de Emergent
```

## Si ya tienes el repo localmente:

```bash
cd /ruta/a/tu/cx-backend
git checkout phase0-4-enhancements1
git pull origin phase0-4-enhancements1
git push origin phase0-4-enhancements1
```
