"""FastAPI应用入口"""
from src.interfaces.dependency_injection import get_logger
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .config import get_settings
from .dependencies import initialize_dependencies
from .middleware import setup_middleware
from .routers import sessions, workflows, analytics, history, websocket, states
from .models.responses import ApiResponse


# 配置日志
def setup_logging():
    """设置日志"""
    settings = get_settings()
    
    # 创建日志目录
    log_file = settings.log_file
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置日志级别
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting FastAPI application...")
    
    # 初始化依赖项
    try:
        await initialize_dependencies()
        logger.info("Dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise
    
    # 创建数据目录
    settings = get_settings()
    data_path = Path(settings.data_path)
    data_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Application started successfully")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down FastAPI application...")
    logger.info("Application shutdown complete")


# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="模块化代理框架的RESTful API",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # 设置中间件
    setup_middleware(app)
    
    # 注册路由
    app.include_router(sessions.router)
    app.include_router(workflows.router)
    app.include_router(analytics.router)
    app.include_router(history.router)
    app.include_router(states.router)
    app.include_router(websocket.router)
    
    # 添加根路径
    @app.get("/", response_model=ApiResponse)
    async def root():
        """根路径"""
        return ApiResponse(
            success=True,
            message=f"欢迎使用 {settings.app_name}",
            data={
                "version": settings.app_version,
                "environment": settings.environment,
                "docs_url": "/docs" if settings.debug else None
            }
        )
    
    # 健康检查
    @app.get("/health", response_model=ApiResponse)
    async def health_check():
        """健康检查"""
        return ApiResponse(
            success=True,
            message="服务运行正常",
            data={
                "status": "healthy",
                "version": settings.app_version
            }
        )
    
    # 自定义OpenAPI
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description="模块化代理框架的RESTful API",
            routes=app.routes,
        )
        
        # 添加自定义信息
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_code": exc.status_code,
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger = get_logger(__name__)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "内部服务器错误",
                "error": str(exc) if settings.debug else None,
            }
        )
    
    return app


# 创建应用实例
app = create_app()


# 如果直接运行此文件，启动开发服务器
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )