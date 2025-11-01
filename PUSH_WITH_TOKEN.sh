#!/bin/bash

# Este script se ejecutará cuando me des el token

TOKEN="$1"

if [ -z "$TOKEN" ]; then
    echo "Error: Necesito el token como argumento"
    echo "Uso: ./PUSH_WITH_TOKEN.sh <tu-github-token>"
    exit 1
fi

cd /app/cx-backend

# Configurar git temporal con el token
git remote set-url origin https://oauth2:${TOKEN}@github.com/juanfamilia/cx-backend.git

# Hacer push
echo "Haciendo push a GitHub..."
git push origin phase0-4-enhancements1

# Resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ PUSH EXITOSO!"
    echo ""
    echo "Ahora Railway debería auto-desplegar."
    echo "Ve a Railway y verifica el nuevo deployment."
    echo ""
else
    echo ""
    echo "❌ PUSH FALLÓ"
    echo "Verifica que el token tenga permisos 'repo'"
    echo ""
fi

# Limpiar (remover token de la URL)
git remote set-url origin https://github.com/juanfamilia/cx-backend.git

echo "Token removido de la configuración de git."
