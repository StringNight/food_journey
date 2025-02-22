from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import sqlalchemy as sa

from alembic import context

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入所有模型
from src.database import Base
from src.models import (
    User, UserProfileModel, RecipeModel, ExerciseType, ExerciseSet, ExerciseRecord,
    RatingModel, ChatMessageModel, FavoriteModel, FoodItem, MealRecord, DailyNutritionSummary
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从 .env 文件加载环境变量
load_dotenv()

# 从环境变量获取数据库 URL
sqlalchemy_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/food_journey")
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            try:
                # 尝试运行迁移
                context.run_migrations()
            except Exception as e:
                # 如果出现找不到 revision 的异常，则删除 alembic_version 表后重试
                if "Can't locate revision" in str(e):
                    connection.execute(sa.text("DROP TABLE IF EXISTS alembic_version"))
                    context.run_migrations()
                else:
                    raise e


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
