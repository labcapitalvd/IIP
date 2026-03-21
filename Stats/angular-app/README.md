# IIP Stats - Angular Frontend

Frontend moderna para IIP (Inteligencia Integral de Procesos) construida con **Angular 18**.

## Requisitos

- Node.js 18+ 
- npm 9+

## Instalación

```bash
cd Stats/angular-app

# Instalar dependencias
npm install

# Iniciar desarrollo (puerto 4200 por defecto)
npm start

# Build para producción
npm run build:prod
```

## Estructura del Proyecto

```
src/
├── app/
│   ├── pages/
│   │   ├── dashboard/        # Módulo dashboard
│   │   └── auth/             # Módulo autenticación
│   ├── shared/               # Componentes y servicios compartidos
│   ├── services/             # Servicios de API
│   ├── models/               # Interfaces y tipos
│   ├── app.component.*       # Componente raíz
│   ├── app.module.ts         # Módulo raíz
│   └── app-routing.module.ts # Rutas
├── assets/                   # Recursos estáticos
├── styles.scss              # Estilos globales
├── index.html               # Plantilla HTML
└── main.ts                  # Punto de entrada
```

## Servicios Disponibles

### Auth Service
- **Login**: `POST /auth/login`
- **Register**: `POST /auth/register`
- **Refresh Token**: `POST /auth/reauth`
- **Logout**: `POST /auth/logout`

### Core Service
Acceso a las APIs del Core en `https://localhost:8002`

### IA Agent Service
Acceso a APIs de IA en `https://localhost:8003`

## Configuración de Desarrollo

### CORS
Por defecto, el servidor de desarrollo está configurado para permitir CORS desde `localhost:4200`.

### Variables de Entorno
Crear archivo `.env`:
```
NG_APP_API_URL=https://localhost:8001
NG_APP_CORE_URL=https://localhost:8002
NG_APP_IA_AGENT_URL=https://localhost:8003
```

## Autenticación

El proyecto incluye un módulo de autenticación básico que:
1. Captura credenciales del usuario
2. Realiza login en `/auth/login`
3. Almacena tokens en `localStorage`
4. Puede ser extendido con un Guard para proteger rutas

## Usuarios de Prueba

- **root** / `RootPassword123!`
- **admin** / `AdminPassword123!`
- **user** / `UserPassword123!`

## Compilación con Docker

```bash
# Desde la raíz del proyecto
docker build -f Dockerfile.angular -t iip-stats-angular .

# Ejecutar
docker run -p 3000:3000 iip-stats-angular
```

## Próximas Mejoras

- [ ] Guards de autenticación
- [ ] Interceptores para manejo de tokens
- [ ] Componentes reutilizables (UI Library)
- [ ] Temas (Light/Dark)
- [ ] Internacionalización (i18n)
- [ ] Estado global (NgRx o Akita)

## Documentación

Más información disponible en:
- [Angular Docs](https://angular.io)
- [SvelteKit Migration Guide](../stats/README.md) - Para entender la transición

