# Web前端项目配置和依赖管理方案

## 1. 项目初始化配置

### 1.1 基础项目结构
```
web/
├── package.json                    # 项目依赖配置
├── tsconfig.json                   # TypeScript配置
├── vite.config.ts                  # Vite构建配置
├── .env.development               # 开发环境变量
├── .env.production                # 生产环境变量
├── .eslintrc.js                   # ESLint代码规范
├── .prettierrc                    # Prettier格式化
├── tailwind.config.js             # Tailwind CSS配置
├── src/
│   ├── main.tsx                   # 应用入口
│   ├── App.tsx                    # 根组件
│   ├── vite-env.d.ts              # Vite类型声明
│   └── ...                        # 其他源码文件
└── public/                        # 静态资源
```

### 1.2 核心依赖配置

```json
{
  "name": "maaf-web-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,css,md}\"",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6",
    "zustand": "^4.4.7",
    "@tanstack/react-query": "^5.12.0",
    "axios": "^1.6.2",
    "socket.io-client": "^4.7.4",
    "react-flow-renderer": "^10.3.17",
    "echarts": "^5.4.3",
    "echarts-for-react": "^3.0.2",
    "dayjs": "^1.11.10",
    "classnames": "^2.3.2",
    "lodash-es": "^4.17.21",
    "react-virtualized": "^9.22.5",
    "react-hotkeys-hook": "^4.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@types/lodash-es": "^4.17.12",
    "@types/react-virtualized": "^9.21.29",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "prettier": "^3.1.1",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "vitest": "^1.0.4",
    "@vitest/ui": "^1.0.4",
    "jsdom": "^23.0.1"
  }
}
```

### 1.3 TypeScript配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/modules/*": ["src/modules/*"],
      "@/services/*": ["src/services/*"],
      "@/stores/*": ["src/stores/*"],
      "@/utils/*": ["src/utils/*"],
      "@/types/*": ["src/types/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 1.4 Vite配置

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/modules': path.resolve(__dirname, './src/modules'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/stores': path.resolve(__dirname, './src/stores'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/types': path.resolve(__dirname, './src/types')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/maaf/web/api')
      },
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ws/, '/maaf/web/ws')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['antd', '@ant-design/icons'],
          'charts-vendor': ['echarts', 'echarts-for-react'],
          'flow-vendor': ['react-flow-renderer']
        }
      }
    }
  }
})
```

## 2. 代码规范和开发工具

### 2.1 ESLint配置

```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended'
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true }
    ],
    '@typescript-eslint/no-unused-vars': ['error', { 
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_'
    }],
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn'
  }
}
```

### 2.2 Prettier配置

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### 2.3 Tailwind CSS配置

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6f7ff',
          100: '#bae7ff',
          200: '#91d5ff',
          300: '#69c0ff',
          400: '#40a9ff',
          500: '#1890ff',
          600: '#096dd9',
          700: '#0050b3',
          800: '#003a8c',
          900: '#002766',
        },
        success: '#52c41a',
        warning: '#faad14',
        error: '#ff4d4f',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

## 3. 环境变量配置

### 3.1 开发环境 (.env.development)

```bash
# API配置
VITE_API_BASE_URL=http://localhost:8080/maaf/web/api
VITE_WS_BASE_URL=ws://localhost:8080/maaf/web/ws

# 应用配置
VITE_APP_TITLE=模块化代理框架 - Web界面
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development

# 功能开关
VITE_ENABLE_REALTIME=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WORKFLOW_EDITOR=true

# 性能配置
VITE_API_TIMEOUT=30000
VITE_WS_RECONNECT_INTERVAL=5000
VITE_WS_MAX_RECONNECT_ATTEMPTS=5
```

### 3.2 生产环境 (.env.production)

```bash
# API配置
VITE_API_BASE_URL=/maaf/web/api
VITE_WS_BASE_URL=/maaf/web/ws

# 应用配置
VITE_APP_TITLE=模块化代理框架 - Web界面
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=production

# 功能开关
VITE_ENABLE_REALTIME=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WORKFLOW_EDITOR=true

# 性能配置
VITE_API_TIMEOUT=30000
VITE_WS_RECONNECT_INTERVAL=10000
VITE_WS_MAX_RECONNECT_ATTEMPTS=3
```

## 4. 开发工作流

### 4.1 Git工作流

```bash
# 分支策略
main        # 主分支，稳定版本
develop     # 开发分支，集成测试
feature/*   # 功能分支
hotfix/*    # 热修复分支
release/*   # 发布分支

# 提交规范
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建/工具
```

### 4.2 开发脚本

```json
{
  "scripts": {
    "dev": "vite",
    "dev:mock": "vite --mode mock",
    "build": "tsc && vite build",
    "build:analyze": "tsc && ANALYZE=true vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,css,md}\"",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "generate:component": "plop component",
    "generate:module": "plop module",
    "generate:service": "plop service"
  }
}
```

## 5. 依赖管理策略

### 5.1 依赖分类管理

```typescript
// 核心依赖 - 必须更新
const coreDependencies = [
  'react', 'react-dom', 'react-router-dom',
  'typescript', 'vite'
]

// UI依赖 - 定期更新
const uiDependencies = [
  'antd', '@ant-design/icons',
  'echarts', 'echarts-for-react',
  'react-flow-renderer'
]

// 工具依赖 - 按需更新
const utilityDependencies = [
  'axios', 'dayjs', 'lodash-es',
  'classnames', 'socket.io-client'
]
```

### 5.2 版本锁定策略

```json
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "packageManager": "npm@9.8.1",
  "volta": {
    "node": "18.19.0",
    "npm": "9.8.1"
  }
}
```

### 5.3 安全更新策略

```bash
# 定期安全检查
npm audit
npm audit fix

# 依赖更新检查
npm outdated
npm update

# 安全扫描
npm run security:check
npm run security:fix
```

## 6. 构建和部署配置

### 6.1 构建优化

```typescript
// vite.config.ts - 生产构建配置
export default defineConfig({
  build: {
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('react')) return 'react-vendor'
            if (id.includes('antd')) return 'antd-vendor'
            if (id.includes('echarts')) return 'charts-vendor'
            if (id.includes('react-flow')) return 'flow-vendor'
            return 'vendor'
          }
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
})
```

### 6.2 Docker配置

```dockerfile
# Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 6.3 CI/CD配置

```yaml
# .github/workflows/deploy.yml
name: Deploy Web Frontend

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test:coverage
      
      - name: Build
        run: npm run build
      
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: |
          # 部署到服务器或CDN
          echo "Deploying to production..."
```

这个配置方案提供了完整的项目初始化、依赖管理、开发工作流和部署配置，确保项目的可维护性和可扩展性。