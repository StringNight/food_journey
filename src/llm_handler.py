from langchain_ollama import ChatOllama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import Generator, List, Dict, Optional, Any, AsyncGenerator
import logging
import json
from langchain.prompts import PromptTemplate
from src.schemas.chat import MessageResponse

class LLMHandler:
    """LLM处理器类
    
    负责处理与大语言模型的交互，包括菜谱生成、个性化推荐等功能
    """
    
    def __init__(self):
        """初始化LLM处理器
        
        Args:
            model_name: 使用的模型名称
        """
        try:
            logging.info("开始初始化 LLM 处理器...")
            
            # 初始化 ChatOllama
            self.chat = None
            self._init_chat()
            
            # 创建系统提示
            self.system_prompt = """你是一个专业的厨师和营养专家。请根据用户的需求提供合适的饮食建议。

用户档案信息：
{user_profile}

请注意：
1. 考虑用户的饮食限制和过敏源
2. 参考用户的卡路里偏好
3. 结合用户的健康目标
4. 提供详细的营养信息"""
            
            logging.info("LLM处理器初始化成功")
            
        except Exception as e:
            logging.error(f"LLM处理器初始化失败: {e}", exc_info=True)
            # 不抛出异常，让服务继续运行
            
    def _init_chat(self):
        """初始化聊天模型"""
        try:
            logging.info("正在初始化 ChatOllama...")
            logging.info("使用配置: model=qwen2.5:14b, base_url=http://127.0.0.1:11434")
            
            self.chat = ChatOllama(
                model="qwen2.5:14b",
                base_url="http://127.0.0.1:11434",
                temperature=0.7,
                streaming=False,  # 暂时关闭流式输出以便调试
                callbacks=[StreamingStdOutCallbackHandler()],
                timeout=30,  # 设置超时时间为 30 秒
                request_timeout=30.0,  # 设置请求超时时间
                api_version="v1"  # 指定 API 版本
            )
            
            # 测试连接
            self._test_connection()
            logging.info("ChatOllama 初始化成功")
            
        except Exception as e:
            logging.error(f"ChatOllama 初始化失败: {str(e)}", exc_info=True)
            self.chat = None
            raise  # 抛出异常以便上层处理

    def _test_connection(self):
        """测试与 Ollama 服务的连接"""
        if not self.chat:
            logging.error("ChatOllama 未初始化")
            return
            
        try:
            logging.info("测试与 Ollama 服务的连接...")
            test_messages = [
                SystemMessage(content="你是一个助手。"),
                HumanMessage(content="测试连接")
            ]
            response = self.chat.generate([test_messages])
            logging.info("成功连接到 Ollama 服务")
            logging.info(f"测试响应: {response.generations[0][0].text}")
        except Exception as e:
            logging.error(f"连接 Ollama 服务失败: {str(e)}", exc_info=True)
            self.chat = None
            raise  # 抛出异常以便上层处理

    async def get_response(self, 
                          prompt: str,
                          chat_history: Optional[List[List[str]]] = None,
                          user_profile: Optional[Dict] = None) -> Generator:
        """
        获取LLM的流式响应
        """
        try:
            # 检查输入是否包含非美食相关的关键词
            non_food_keywords = [
                "股票", "基金", "政治", "军事", "游戏", "电影",
                "音乐", "体育", "新闻", "天气", "交通"
            ]
            
            if any(keyword in prompt for keyword in non_food_keywords):
                yield "哎呀，虽然我很想和您聊天，但我是一个专注于美食的厨师呢！要不我们聊聊美食、烹饪或营养健康的话题吧？😊"
                return
            
            # 格式化用户档案信息
            profile_str = "暂无用户档案信息"
            if user_profile:
                profile_str = f"""
                烹饪水平：{user_profile.get('cooking_skill_level', '未知')}
                喜爱的菜系：{', '.join(user_profile.get('favorite_cuisines', []))}
                饮食限制：{', '.join(user_profile.get('dietary_restrictions', []))}
                过敏源：{', '.join(user_profile.get('allergies', []))}
                卡路里偏好：{user_profile.get('calorie_preference', '未设置')}
                健康目标：{', '.join(user_profile.get('health_goals', []))}
                """
            
            # 创建消息列表
            messages = [
                SystemMessage(content=self.system_prompt.format(user_profile=profile_str))
            ]
            
            # 添加对话历史
            if chat_history:
                for user_msg, ai_msg in chat_history:
                    if user_msg:  # 有时用户消息可能是空的（比如图片输入）
                        messages.append(HumanMessage(content=user_msg))
                    if ai_msg:
                        messages.append(AIMessage(content=ai_msg))
            
            # 添加当前用户输入
            messages.append(HumanMessage(content=prompt))
            
            # 获取流式响应
            response = await self.chat.agenerate([messages])
            
            # 返回生成器
            for chunk in response.generations[0][0].text:
                yield chunk
                
        except Exception as e:
            logging.error(f"获取LLM响应失败: {e}")
            yield f"抱歉，处理您的请求时出现错误: {str(e)}"

    async def analyze_recipe(self, recipe_text: str, chat_history: Optional[List[List[str]]] = None, user_profile: Optional[Dict] = None) -> Generator:
        """分析菜谱内容"""
        prompt = f"""让我来为您详细分析这道菜品！🔍

{recipe_text}

我会从以下几个方面为您进行专业而有趣的解析：

1. 食材解析 🥘
   - 核心食材的特点和选购建议
   - 每种食材的最佳处理方法
   - 食材配的营养学原理
   - 可能的替代食材及其影响

2. 烹饪步骤详解 👨‍🍳
   每个步骤我都会说明：
   - 具体操作要领
   - 火候和时间控制（精确到分钟）
   - 为什么要这样做（科学原理）
   - 常见错误和规避方法
   - 关键控制点和判断标准

3. 厨具选择 🔪
   - 必备厨具清单
   - 各种厨具的使用技巧
   - 替代方案（如果没有特定厨具）

4. 营养价值分析 📊
   每份（约300克）含量：
   - 热量（kcal）
   - 蛋白质（g）
   - 脂肪（g）
   - 碳水化合物（g）
   - 膳食纤维（g）
   - 维生素和矿物质
   - 适合人群及注意事项

5. 烹饪小贴士 💡
   - 提前准备的建议
   - 保存方法和时间
   - 配菜和搭配建议
   - 调味技巧和诀窍

6. 健康建议 ❤️
   - 热量控制建议
   - 营养均衡建议
   - 特殊人群食用建议
   - 食材营养最大化方法

让我们开始这场美食探索之旅吧！"""

        async for chunk in self.get_response(prompt, chat_history, user_profile):
            yield chunk

    async def generate_recipe(self, 
                            ingredients: List[str], 
                            chat_history: Optional[List[List[str]]] = None,
                            user_profile: Optional[Dict] = None) -> Generator:
        """根据食材生成菜谱"""
        ingredients_text = "、".join(ingredients)
        
        prompt = f"""让我用这些食材为您设计一道美味佳肴！✨

食材清单：{ingredients_text}

作为一位米其林三星厨师，我会为您详细说明：

1. 菜品构思 🎨
   - 菜品名称及创意来源
   - 烹饪风格和特色
   - 预期成品效果
   - 难度评估（1-5星）

2. 食材准备 🥬
   每种食材我都会说明：
   - 具体用量（克/个）
   - 处理方法
   - 新鲜度判断标准
   - 选购技巧

3. 详细步骤 👨‍🍳
   每个步骤都包含：
   - 具体操作描述
   - 火候控制（小火/中火/大火）
   - 精确时间（分钟）
   - 成功的判断标准
   - 可能的失误和补救方法

4. 关键技巧 🔑
   - 刀工要求和技巧
   - 调味比例和顺序
   - 火候掌控要点
   - 摆盘建议

5. 营养分析 📊
   每份（约300克）含量：
   - 热量：xxx kcal
   - 蛋白质：xx g
   - 脂肪：xx g
   - 碳水化合物：xx g
   - 膳食纤维：xx g
   - 维生素和矿物质
   - 适合人群

6. 健康建议 ❤️
   - 食用建议
   - 适量参考
   - 禁忌人群
   - 营养价值最大化方法

7. 趣味知识 💡
   - 菜品小故事
   - 营养科普
   - 趣味问答

让我们开始这场美味的创作之旅吧！"""

        async for chunk in self.get_response(prompt, chat_history, user_profile):
            yield chunk

    async def get_cooking_tips(self, 
                             recipe_name: str, 
                             skill_level: str = "beginner",
                             chat_history: Optional[List[List[str]]] = None,
                             user_profile: Optional[Dict] = None) -> Generator:
        """获取烹饪技巧"""
        prompt = f"""让我来为您详细讲解制作 {recipe_name} 的专业技巧！👨‍🍳

考虑到您的烹饪水平是 {skill_level}，我会特别注意以下几点：

1. 准备工作 📝
   - 详细的食材清单（包含用量）
   - 必备厨具清单
   - 食材处理技巧
   - 预处理时间安排

2. 关键步骤详解 🔍
   每个步骤都包含：
   - 具体操作要领
   - 火候控制说明
   - 时间控制点
   - 成功的判断标准
   - 常见问题和解决方案

3. 专业技巧 ⭐
   - 刀工技巧
   - 调味秘诀
   - 火候掌控
   - 食材搭配原理
   - 口感提升方法

4. 品质控制 ✅
   - 食材新鲜度判断
   - 成熟度判断标准
   - 最佳食用温度
   - 保存方法和时间

5. 营养价值 📊
   - 每份营养成分
   - 热量控制建议
   - 适合人群
   - 食用建议

6. 进阶提示 🎯
   - 创新改良方案
   - 摆盘技巧
   - 配菜建议
   - 风味提升方法

让我们一起提升厨艺水平！"""

        async for chunk in self.get_response(prompt, chat_history, user_profile):
            yield chunk

    async def process_chat_message(self, message: str, user_profile: Optional[Dict] = None) -> MessageResponse:
        """处理聊天消息
        
        Args:
            message: 用户消息
            user_profile: 用户档案信息
            
        Returns:
            MessageResponse: 处理结果
        """
        try:
            logging.info(f"收到用户消息: {message}")
            
            # 如果 LLM 服务不可用，返回友好的错误消息
            if not self.chat:
                return MessageResponse(
                    message="抱歉，AI 助手当前不可用，请稍后再试。",
                    suggestions=None,
                    image_url=None,
                    voice_url=None
                )
            
            # 格式化用户档案
            profile_str = "暂无用户档案信息"
            if user_profile:
                profile_items = []
                if user_profile.get('cooking_skill_level'):
                    profile_items.append(f"烹饪水平：{user_profile['cooking_skill_level']}")
                if user_profile.get('favorite_cuisines'):
                    cuisines = user_profile['favorite_cuisines']
                    if isinstance(cuisines, (list, tuple)):
                        profile_items.append(f"喜爱的菜系：{', '.join(str(x) for x in cuisines)}")
                    else:
                        profile_items.append(f"喜爱的菜系：{cuisines}")
                if user_profile.get('dietary_restrictions'):
                    restrictions = user_profile['dietary_restrictions']
                    if isinstance(restrictions, (list, tuple)):
                        profile_items.append(f"饮食限制：{', '.join(str(x) for x in restrictions)}")
                    else:
                        profile_items.append(f"饮食限制：{restrictions}")
                if user_profile.get('allergies'):
                    allergies = user_profile['allergies']
                    if isinstance(allergies, (list, tuple)):
                        profile_items.append(f"过敏源：{', '.join(str(x) for x in allergies)}")
                    else:
                        profile_items.append(f"过敏源：{allergies}")
                if user_profile.get('calorie_preference'):
                    profile_items.append(f"卡路里偏好：{user_profile['calorie_preference']}")
                if user_profile.get('health_goals'):
                    goals = user_profile['health_goals']
                    if isinstance(goals, (list, tuple)):
                        profile_items.append(f"健康目标：{', '.join(str(x) for x in goals)}")
                    else:
                        profile_items.append(f"健康目标：{goals}")
                
                profile_str = "\n".join(profile_items) if profile_items else "暂无用户档案信息"
            
            # 创建消息列表
            messages = [
                SystemMessage(content=self.system_prompt.format(user_profile=profile_str)),
                HumanMessage(content=message)
            ]
            
            logging.info("开始调用 LLM 生成响应...")
            
            # 获取响应
            response = await self.chat.agenerate([messages])
            response_text = response.generations[0][0].text
            
            logging.info(f"LLM 响应内容: {response_text}")
            
            return MessageResponse(
                message=response_text,
                suggestions=None,
                image_url=None,
                voice_url=None
            )
            
        except Exception as e:
            logging.error(f"处理聊天消息失败: {e}", exc_info=True)
            return MessageResponse(
                message="抱歉，处理您的请求时出现错误，请稍后再试。",
                suggestions=None,
                image_url=None,
                voice_url=None
            )