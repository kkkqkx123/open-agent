"""API启动脚本"""
import uvicorn
from .config import get_settings


def main():
    """启动API服务器"""
    settings = get_settings()
    
    print(f"启动 {settings.app_name} v{settings.app_version}")
    print(f"环境: {settings.environment}")
    print(f"调试模式: {settings.debug}")
    print(f"监听地址: http://{settings.host}:{settings.port}")
    
    if settings.debug:
        print(f"API文档: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()