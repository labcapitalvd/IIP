import React, { useState } from 'react';
import {
  Box,
  Copy,
  Check,
  Download,
  Terminal,
  FileCode,
  Layers,
  X,
  Server,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';

interface DockerDeploymentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DockerDeploymentModal: React.FC<DockerDeploymentModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'compose' | 'dockerfile' | 'nginx' | 'commands'>('compose');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!isOpen) return null;

  const dockerComposeContent = `version: '3.8'

services:
  # ==========================================================
  # Índice de Innovación Pública (IIP) - Frontend Web App
  # ==========================================================
  iip-web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: iip-veeduria-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - VITE_AUTH_API_URL=http://localhost:4293
      - VITE_CORE_API_URL=http://localhost:4294
    networks:
      - iip-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # ==========================================================
  # Microservicios FastAPI Opcionales (Referencia de Red)
  # ==========================================================
  # auth-service:
  #   image: python:3.11-slim
  #   container_name: iip-auth-service
  #   ports:
  #     - "4293:4293"
  #   networks:
  #     - iip-network
  #
  # core-service:
  #   image: python:3.11-slim
  #   container_name: iip-core-service
  #   ports:
  #     - "4294:4294"
  #   networks:
  #     - iip-network

networks:
  iip-network:
    name: iip-veeduria-net
    driver: bridge`;

  const dockerfileContent = `# ==========================================================
# Índice de Innovación Pública (IIP) - Veeduría Distrital
# Multi-stage Production Dockerfile
# ==========================================================

# ----------------------------------------------------------
# Stage 1: Build stage
# ----------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json ./

# Install project dependencies
RUN npm install

# Copy application source code
COPY . .

# Compile optimized static bundle
RUN npm run build

# ----------------------------------------------------------
# Stage 2: High-Performance Production Nginx Runtime
# ----------------------------------------------------------
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx configuration with SPA routing and security headers
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production build from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose standard container port
EXPOSE 3000

# Healthcheck to ensure container availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Launch Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]`;

  const nginxContent = `server {
    listen 3000;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip Compression for fast delivery
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types 
        text/plain 
        text/css 
        text/xml 
        text/javascript 
        application/x-javascript 
        application/xml 
        application/javascript 
        application/json 
        image/svg+xml;
    gzip_disable "MSIE [1-6]\\.";

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # SPA Routing: Fallback all route paths to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets (CSS, JS, Web Fonts, Images)
    location ~* \\.(?:ico|css|js|gif|jpe?g|png|svg|woff2?|eot|ttf|otf)$ {
        expires 6M;
        access_log off;
        add_header Cache-Control "public, max-age=15552000, immutable";
    }

    # Error handling
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}`;

  const commandsContent = `# 1. Construir y levantar contenedor con Docker Compose
docker compose up -d --build

# 2. Ver logs en tiempo real
docker compose logs -f iip-web

# 3. Verificar estado y healthcheck
docker compose ps

# 4. Detener los contenedores
docker compose down

# 5. Despliegue manual directo con Docker CLI (alternativo sin compose):
docker build -t veeduria/iip-app:latest .
docker run -d -p 3000:3000 --name iip-app veeduria/iip-app:latest`;

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getActiveContent = () => {
    switch (activeTab) {
      case 'compose':
        return { content: dockerComposeContent, filename: 'docker-compose.yml', lang: 'yaml' };
      case 'dockerfile':
        return { content: dockerfileContent, filename: 'Dockerfile', lang: 'dockerfile' };
      case 'nginx':
        return { content: nginxContent, filename: 'nginx.conf', lang: 'nginx' };
      case 'commands':
        return { content: commandsContent, filename: 'docker-commands.sh', lang: 'bash' };
    }
  };

  const activeData = getActiveContent();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-700 rounded-3xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] text-slate-100 animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-400/30 flex items-center justify-center font-bold">
              <Box className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-extrabold text-white text-base">
                  Contenedorización Docker & YAML
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                  Listo para Producción
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Archivos de despliegue multi-stage optimizados para el IIP (Veeduría Distrital)
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between px-6 pt-4 pb-2 border-b border-slate-800 bg-slate-950/40 overflow-x-auto gap-2">
          <div className="flex items-center gap-2 min-w-max">
            <button
              onClick={() => setActiveTab('compose')}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === 'compose'
                  ? 'bg-amber-500 text-slate-950 shadow-md font-black'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>docker-compose.yml</span>
            </button>

            <button
              onClick={() => setActiveTab('dockerfile')}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === 'dockerfile'
                  ? 'bg-amber-500 text-slate-950 shadow-md font-black'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Box className="w-3.5 h-3.5" />
              <span>Dockerfile</span>
            </button>

            <button
              onClick={() => setActiveTab('nginx')}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === 'nginx'
                  ? 'bg-amber-500 text-slate-950 shadow-md font-black'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>nginx.conf</span>
            </button>

            <button
              onClick={() => setActiveTab('commands')}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                activeTab === 'commands'
                  ? 'bg-amber-500 text-slate-950 shadow-md font-black'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Comandos CLI</span>
            </button>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => copyToClipboard(activeData.content, activeTab)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              {copiedKey === activeTab ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">¡Copiado!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copiar</span>
                </>
              )}
            </button>

            <button
              onClick={() => downloadFile(activeData.content, activeData.filename)}
              className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Descargar {activeData.filename}</span>
            </button>
          </div>
        </div>

        {/* Code Content Area */}
        <div className="p-6 overflow-y-auto flex-1 font-mono text-xs bg-slate-950/90 leading-relaxed text-slate-300 select-text">
          <pre className="whitespace-pre overflow-x-auto p-4 bg-slate-950 rounded-2xl border border-slate-800/80">
            <code>{activeData.content}</code>
          </pre>
        </div>

        {/* Footer Summary */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Incluye compilación multi-stage de Node 20, servidor Nginx Alpine con soporte SPA y compresión gzip.
            </span>
          </div>

          <button
            onClick={onClose}
            className="w-full sm:w-auto px-5 py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
