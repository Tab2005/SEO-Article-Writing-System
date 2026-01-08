"""
SEO Article Writing System - FastAPI Application Entry Point

This is the main entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 將在後續任務中添加路由導入
# from app.api.v1 import auth, research, content

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="SEO Article Writing System API",
        description="AI-powered SEO article writing and research platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS 設定 (開發階段允許所有來源)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生產環境需要限制具體域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 健康檢查端點
    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {
            "message": "SEO Article Writing System API",
            "status": "running",
            "version": "0.1.0"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    # TODO: 在後續任務中添加路由
    # app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
    # app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
    # app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    
    return app

# 建立 FastAPI 實例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )