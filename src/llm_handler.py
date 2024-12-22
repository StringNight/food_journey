from langchain_community.chat_models import ChatOllama
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
            # 初始化支持流式输出的 ChatOllama
            self.chat = ChatOllama(
                model="qwen2.5:14b",
                base_url="http://localhost:11434",
                temperature=0.7,
                streaming=True,  # 启用流式输出
                callbacks=[StreamingStdOutCallbackHandler()]
            )
            
            # 创建系统提示
            self.system_prompt = """你是一个风趣幽默的米其林厨师，并曾在所有的米其林和黑珍珠餐厅工作过，同时也是国家级的营养学专家。你的性格特点是：
1. 热情友好，喜欢用轻松愉快的语气交谈
2. 擅长讲笑话和俏皮话，但不会影响专业性
3. 会根据用户的烹饪水平调整建议的难度
4. 会关心用户的饮食偏好和健康目标
5. 喜欢通过提问来了解用户的具体需求

用户档案信息：
{user_profile}

对话规则：
1. 根据用户的烹饪水平调整回答的专业程度
2. 考虑用户的饮食限制和过敏源
3. 参考用户的卡路里偏好给出建议
4. 结合用户的健康目标提供指导
5. 在合适的时候提出跟进问题

回答格式要求：
1. 每个步骤都要详细解释原理和注意事项
2. 提供具体的时间、温度等数值参考
3. 说明每个步骤可能出现的问题和解决方案
4. 包含完整的营养成分分析，包括但不限于卡路里、维生素、矿物质、蛋白质、脂肪、碳水化合物等
5. 使用emoji增加趣味性"""
            
            logging.info("LLM处理器初始化成功")
            
        except Exception as e:
            logging.error(f"LLM处理器初始化失败: {e}")
            raise

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
   - 食材搭配的营养学原理
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
            MessageResponse: 包含回复消息和建议的响应
        """
        try:
            response_text = ""
            async for chunk in self.get_response(message, user_profile=user_profile):
                response_text += chunk
            
            # 从响应中提取建议（如果有）
            suggestions = []
            if "建议：" in response_text:
                suggestions_text = response_text.split("建议：")[1].strip()
                suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip()]
            
            return MessageResponse(
                message=response_text,
                suggestions=suggestions if suggestions else None
            )
            
        except Exception as e:
            logging.error(f"处理聊天消息失败: {e}")
            return MessageResponse(
                message="抱歉，我现在无法正常回答。请稍后再试。",
                suggestions=["请重新发送您的问题", "换个方式提问", "稍后再试"]
            )