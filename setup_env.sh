#!/bin/bash

# 从.env文件读取并导出环境变量
export JWT_SECRET_KEY="food_journey_secret_key_2024"
export DATABASE_URL="sqlite:///./sql_app.db"
export API_V1_PREFIX="/api"
export PROJECT_NAME="Food Journey API"
export BACKEND_CORS_ORIGINS='["*"]'
export UPLOAD_DIR="uploads"
export MAX_UPLOAD_SIZE=5242880
export CORS_ALLOWED_ORIGINS='["*"]'
export ENVIRONMENT="development"

echo "环境变量已设置:"
echo "JWT_SECRET_KEY: $JWT_SECRET_KEY"
echo "DATABASE_URL: $DATABASE_URL"
echo "ENVIRONMENT: $ENVIRONMENT" 