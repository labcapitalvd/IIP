#!/bin/bash

# Script para compilar la aplicación Angular

set -e

echo "📦 Instalando dependencias..."
npm install

echo "🔨 Compilando aplicación para producción..."
npm run build:prod

echo ""
echo "✅ Compilación completada exitosamente"
echo "📁 Archivos compilados en: dist/iip-stats"
echo ""
echo "💡 Para ejecutar localmente (desarrollo):"
echo "   npm start"
echo ""
echo "🐳 Para usar Docker:"
echo "   docker build -f ../../Dockerfile.angular -t iip-stats-angular ."
echo "   docker run -p 3000:3000 iip-stats-angular"
