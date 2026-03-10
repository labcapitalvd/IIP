# Checklist: Migración Angular - IIP Stats

## ✅ Completado

- [x] Crear proyecto Angular 18 con estructura completa
- [x] Crear componentes: Root, Dashboard, Login
- [x] Configurar routing (lazy loading)
- [x] Configurar HttpClient para API calls
- [x] Crear Dockerfile para compilación multi-stage
- [x] Actualizar compose.yaml para usar Angular
- [x] Documentación (README, ANGULAR_BUILD.md)
- [x] Archivos de configuración (.env.example, build.sh)

## 🔄 Próximos Pasos (Orden de ejecución)

### Paso 1: Compilar la aplicación Angular
**Ubicación:** Dentro de WSL
```bash
# Opción A: Compilación local (para verificar rápido)
cd /home/alejo/veeduria/IIP/Stats/angular-app
npm install
npm run build:prod

# Opción B: Usar Docker (recomendado para producción)
cd /home/alejo/veeduria/IIP
docker build -f Dockerfile.angular -t iip-stats-angular .
```
**Duración aproximada:** 3-5 minutos
**Verificar:** Archivos en `dist/iip-stats/`

### Paso 2: Iniciar docker-compose completo
**Ubicación:** Raíz del proyecto
```bash
cd /home/alejo/veeduria/IIP

# Opción A: Compilar e iniciar todo de una vez
docker-compose up --build

# Opción B: Si ya compilaste, solo iniciar
docker-compose up
```
**Esperar a que:** Todos los servicios estén en estado "running"

### Paso 3: Verificar que funciona
**Acceso a la aplicación:**
- 🌐 Aplicación: https://localhost:8004
- 🔐 Login: usa credenciales en `Secrets/users.toml`
  - Usuario: `admin`
  - Contraseña: `AdminPassword123!`
- 📊 Dashboard: debe mostrar cards después de login
- 📚 Swagger (Core): https://localhost:8002/docs

### Paso 4: Commit a Git (si es necesario)
```bash
# Crear rama para esta migración
git checkout -b feat/angular-migration

# Agregar cambios
git add .

# Commit
git commit -m "feat: Migrate Stats frontend from SvelteKit to Angular 18

- Creates Angular 18 project with modules and routing
- Implements Dashboard and Login components
- Configures API communication with Auth service
- Updates Docker and compose.yaml for Angular build
- Maintains same functionality with better maintainability"

# Push (si lo requiere tu workflow)
git push origin feat/angular-migration
```

## ⚠️ Consideraciones Importantes

### 1. Rutas WSL desde PowerShell
Si eres usuario de Windows con VS Code en WSL:
- ✅ Haz: `wsl npm install`
- ❌ No hagas: `npm install` desde PowerShell en ruta UNC

### 2. Cambios en compose.yaml
Si tenías una versión anterior de Stats (SvelteKit):
- El nuevo servicio `front_stats` compila Angular
- Puerto sigue siendo 8004 (externo)
- Interno ahora es 3000 en lugar de 5173

### 3. Variables de entorno de Angular
Las variables de build están en `Stats/angular-app/.env.example`
- Copiar a `.env` si necesitas valores específicos
- Angular las usa en tiempo de compilación

### 4. HTTPS y Certificados
- Los certificados en `Secrets/` están en .gitignore
- En desarrollo, usa `https://localhost:8004`
- Acepta certificado autofirmado cuando te lo pida el navegador

## 🛠️ Troubleshooting

### Error: `npm command not found` en WSL
```bash
# Instalar Node 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Error: Port 8004 already in use
```bash
# Ver qué está usando el puerto
sudo lsof -i :8004
# O con netstat
netstat -tulpn | grep 8004

# Matar el proceso si es necesario
kill -9 <PID>
```

### Angular no compila
```bash
# Limpiar node_modules y package-lock.json
rm -rf node_modules package-lock.json
npm install

# Luego intentar compilar
npm run build:prod
```

### Docker build falla
```bash
# Ver logs detallados
docker build -f Dockerfile.angular -t iip-stats-angular . --progress=plain

# Limpiar caché
docker builder prune -a
```

## 📝 Notas de Desarrollo

- **Framework**: Angular 18 con TypeScript 5.5
- **Estilos**: SCSS global + por componente
- **HTTP Client**: Configurado con HttpClientModule
- **Routing**: Lazy loading para Dashboard y Auth
- **Login**: Conecta con API en `https://localhost:8001/auth/login`
- **Token Storage**: localStorage (puede mejorarse a sessionStorage)

## 🚀 Pasos Posteriores (Después de verificar que funciona)

1. **Mejorar autenticación**
   - Agregar Guards para rutas protegidas
   - Implementar interceptor para agregar token a requests
   - Refresh automático de tokens

2. **Expandir Dashboard**
   - Integrar datos reales de las APIs
   - Gráficos y visualizaciones
   - Tablas con paginación

3. **Componentes compartidos**
   - Crear UILibrary reutilizables
   - Validaciones comunes
   - Handlers de error globales

4. **Estado global**
   - Considerar NgRx o Akita para estado compartido
   - Caché de datos

5. **Testing**
   - Karma + Jasmine para unit tests
   - Cypress para E2E tests

---

**Estado actual:** Angular 18 completamente scaffolded y listo para compilación  
**Próximo hito:** Ejecución de `npm install && npm run build:prod` o `docker build`
