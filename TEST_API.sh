#!/bin/bash

echo "=========================================="
echo "  PRUEBA DE API - RAILWAY DEPLOYMENT"
echo "=========================================="
echo ""
echo "Por favor ingresa tu URL de Railway:"
echo "(Ejemplo: https://cx-backend-production.up.railway.app)"
read -p "URL: " RAILWAY_URL

echo ""
echo "Probando health endpoint..."
echo ""

# Test 1: Health Check
echo "1. GET ${RAILWAY_URL}/api/v1/health"
curl -s "${RAILWAY_URL}/api/v1/health" | jq '.' || echo "No se pudo conectar o respuesta no es JSON"

echo ""
echo ""
echo "=========================================="
echo "¿La API respondió correctamente?"
echo "Si ves un error 404 o 502, revisa:"
echo "  - URL correcta"
echo "  - Servicio está running en Railway"
echo "=========================================="
