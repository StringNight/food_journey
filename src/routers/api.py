from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from . import auth, profile, chat, recipes, favorites

router = APIRouter()

# 添加根路径处理函数
@router.get("/", response_class=HTMLResponse)
async def root():
    """返回欢迎页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Welcome to Infsols! (上海寰解科技有限公司)</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }
            .container {
                text-align: center;
                padding: 2rem;
                border-radius: 10px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 1rem;
                font-size: 2.5rem;
            }
            h2 {
                color: #555;
                margin-bottom: 1.5rem;
                font-size: 2rem;
            }
            .company-name {
                color: #1a73e8;
                font-size: 3rem;
                font-weight: bold;
                margin: 1.5rem 0;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Infsols! (上海寰解科技有限公司)</h1>
            <div class="company-name">上海寰解科技有限公司</div>
        </div>
    </body>
    </html>
    """
    return html_content

# 包含各个子路由
router.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
router.include_router(profile.router, prefix="/api/v1/profile", tags=["用户档案"])
router.include_router(chat.router, prefix="/api/v1/chat", tags=["聊天"])
router.include_router(recipes.router, prefix="/api/v1/recipes", tags=["食谱"])
router.include_router(favorites.router, prefix="/api/v1/favorites", tags=["收藏"])