# Compilación de la Aplicación Angular en WSL

Dado que el workspace está en WSL (\\wsl.localhost\Ubuntu), necesitas ejecutar los comandos de npm dentro del entorno de WSL.

## Opción 1: Compilar dentro de WSL (Recomendado para desarrollo)

### Acceder a WSL
```powershell
# Desde PowerShell en Windows
wsl
```

### Compilar
```bash
cd /home/alejo/veeduria/IIP/Stats/angular-app

# Instalar dependencias
npm install

# Compilar para producción
npm run build:prod

# O ejecutar el script
bash build.sh
```

## Opción 2: Compilar con Docker (Recomendado para producción)

```bash
# Desde la raíz del proyecto IIP
docker build -f Dockerfile.angular -t iip-stats-angular .

# Ejecutar
docker run -p 3000:3000 iip-stats-angular
```

## Opción 3: Actualizar compose.yaml y compilar todo

```bash
# Desde la raíz del proyecto IIP
docker-compose up --build

# O solo la aplicación Stats
docker-compose up --build front_stats
```

## Verificación

Una vez compilado, deberías ver:
- Archivos en `dist/iip-stats/`
- La aplicación disponible en `http://localhost:3000` (desarrollo) o `https://localhost:8004` (producción via Nginx)

## Troubleshooting

### Problema: `npm install` no funciona desde PowerShell
❌ **No hagas esto:**
```powershell
cd Stats\angular-app
npm install  # Falla en ruta UNC
```

✅ **Haz esto en su lugar:**
```powershell
wsl
cd /home/alejo/veeduria/IIP/Stats/angular-app
npm install
```

### Problema: Permisos en archivos
Si obtienes errores de permisos al ejecutar bash scripts:
```bash
chmod +x ./Stats/angular-app/build.sh
```

### Problema: Node/npm no encontrado en WSL
```bash
# Verificar instalación
node --version
npm --version

# Si no está instalado
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

