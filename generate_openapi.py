"""生成OpenAPI文档"""

from fastapi.openapi.utils import get_openapi
from src.main import app
import json

def generate_openapi():
    """生成OpenAPI规范并保存到文件"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    # 保存到文件
    with open('openapi.json', 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    
    print("OpenAPI文档已生成：openapi.json")

if __name__ == "__main__":
    generate_openapi() 