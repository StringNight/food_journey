"""Web应用入口模块"""

import gradio as gr
from typing import Dict, Optional
import logging
from .config import config, setup_logging
from .services.user_service import UserService
from .services.recipe_service import RecipeService
from .services.ai_service_client import AIServiceClient

# 配置日志
setup_logging(
    level="DEBUG" if config.DEBUG else "INFO",
    log_file=True,
    console=True
)

class WebApp:
    """Web应用类
    
    提供Web界面，用于菜谱创建和管理，以及AI功能测试
    """
    
    def __init__(self):
        """初始化Web应用"""
        self.user_service = UserService()
        self.recipe_service = RecipeService()
        self.ai_client = AIServiceClient()
        self.logger = logging.getLogger(__name__)
        
        # 创建Gradio界面
        self.interface = self._build_interface()
    
    def _build_interface(self) -> gr.Blocks:
        """构建Gradio界面
        
        Returns:
            gr.Blocks: Gradio界面对象
        """
        with gr.Blocks(
            title="美食之旅",
            theme=gr.themes.Soft(
                primary_hue="orange",
                secondary_hue="blue"
            )
        ) as interface:
            gr.Markdown("# 🍳 美食之旅")
            
            with gr.Tabs():
                # AI功能测试标签页
                with gr.Tab("🤖 AI助手"):
                    self._build_ai_test_tab()
                
                # 菜谱创建标签页
                with gr.Tab("📝 创建菜谱"):
                    self._build_recipe_creation_tab()
                
                # 菜谱搜索标签页
                with gr.Tab("🔍 搜索菜谱"):
                    self._build_recipe_search_tab()
            
        return interface
        
    def _build_ai_test_tab(self):
        """构建AI功能测试标签页"""
        with gr.Tabs():
            # 文本聊天
            with gr.Tab("💬 文本聊天"):
                chat_history = gr.Chatbot(
                    label="对话历史",
                    height=400,
                    type="messages"
                )
                with gr.Row():
                    text_input = gr.Textbox(
                        label="输入消息",
                        placeholder="请输入你的问题...",
                        lines=3
                    )
                    send_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空对话")
                
                async def on_message(message: str, history: list):
                    if not message:
                        return history
                    try:
                        # 发送聊天请求
                        response = await self.ai_client.chat(
                            messages=[{
                                "role": "system",
                                "content": "你是一个专业的厨师和营养专家。"
                            }, {
                                "role": "user",
                                "content": message
                            }],
                            model="qwen2.5:14b"
                        )
                        
                        # 更新对话历史
                        history.append({
                            "role": "user",
                            "content": message
                        })
                        history.append({
                            "role": "assistant",
                            "content": response.get("response", "")
                        })
                        return history
                    except Exception as e:
                        self.logger.error(f"聊天请求失败: {str(e)}")
                        history.append({
                            "role": "user",
                            "content": message
                        })
                        history.append({
                            "role": "assistant",
                            "content": f"抱歉，处理请求时出错: {str(e)}"
                        })
                        return history
                
                send_btn.click(
                    fn=on_message,
                    inputs=[text_input, chat_history],
                    outputs=chat_history,
                    api_name="chat"
                ).then(
                    lambda: "", None, text_input  # 清空输入框
                )
                
                text_input.submit(
                    fn=on_message,
                    inputs=[text_input, chat_history],
                    outputs=chat_history,
                    api_name="chat_submit"
                ).then(
                    lambda: "", None, text_input  # 清空输入框
                )
                
                clear_btn.click(lambda: None, None, chat_history)
            
            # 语音聊天
            with gr.Tab("🎤 语音聊天"):
                voice_history = gr.Chatbot(
                    label="对话历史",
                    height=400,
                    type="messages"
                )
                audio_input = gr.Audio(
                    label="录制语音",
                    sources=["microphone"],
                    type="filepath"
                )
                voice_clear_btn = gr.Button("清空对话")
                
                async def on_voice(audio_data, history: list):
                    if not audio_data:
                        return history
                    try:
                        # 转写语音
                        transcribed_text = await self.ai_client.process_voice(audio_data)
                        if not transcribed_text:
                            history.append({
                                "role": "assistant",
                                "content": "抱歉，无法识别语音内容"
                            })
                            return history
                            
                        # 发送聊天请求
                        response = await self.ai_client.chat(
                            messages=[{
                                "role": "system",
                                "content": "你是一个专业的厨师和营养专家。"
                            }, {
                                "role": "user",
                                "content": transcribed_text
                            }],
                            model="qwen2.5:14b"
                        )
                        
                        # 更新对话历史
                        history.append({
                            "role": "user",
                            "content": f"语音转写：{transcribed_text}"
                        })
                        history.append({
                            "role": "assistant",
                            "content": response.get("response", "")
                        })
                        return history
                    except Exception as e:
                        self.logger.error(f"语音处理失败: {str(e)}")
                        history.append({
                            "role": "assistant",
                            "content": f"抱歉，处理语音时出错: {str(e)}"
                        })
                        return history
                
                audio_input.change(
                    fn=on_voice,
                    inputs=[audio_input, voice_history],
                    outputs=voice_history,
                    api_name="voice_chat"
                )
                
                voice_clear_btn.click(lambda: None, None, voice_history)
            
            # 食物识别
            with gr.Tab("🍲 食物识别"):
                food_history = gr.Chatbot(
                    label="识别历史",
                    height=400,
                    type="messages"
                )
                with gr.Row():
                    with gr.Column():
                        image_input = gr.Image(
                            label="上传食物图片",
                            type="filepath",
                            image_mode="RGB",
                            sources=["upload", "webcam"]
                        )
                    with gr.Column():
                        result_output = gr.Textbox(
                            label="识别结果",
                            lines=10,
                            interactive=False
                        )
                food_clear_btn = gr.Button("清空记录")
                
                async def on_image(image, history: list):
                    if not image:
                        return history, "请上传图片"
                    try:
                        # 识别图片中的食物
                        recognition_result = await self.ai_client.recognize_food(image)
                        
                        if not recognition_result["success"]:
                            error_msg = recognition_result.get("message", "未知错误")
                            history.append({
                                "role": "assistant",
                                "content": f"识别失败: {error_msg}"
                            })
                            return history, error_msg
                        
                        # 格式化识别结果
                        food_items = recognition_result.get("food_items", [])
                        if not food_items:
                            history.append({
                                "role": "assistant",
                                "content": "未识别到食物"
                            })
                            return history, "未识别到食物"
                        
                        # 构建识别结果文本
                        result_text = "识别结果：\n"
                        for item in food_items:
                            if isinstance(item, dict):
                                name = item.get("name", "未知食物")
                                confidence = item.get("confidence", 0)
                                result_text += f"- {name} (置信度: {confidence:.2%})\n"
                            elif isinstance(item, str):
                                result_text += f"- {item}\n"
                        
                        history.append({
                            "role": "assistant",
                            "content": result_text
                        })
                        return history, result_text
                        
                    except Exception as e:
                        self.logger.error(f"图片处理失败: {str(e)}")
                        error_msg = f"处理图片时出错: {str(e)}"
                        history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        return history, error_msg
                
                image_input.change(
                    fn=on_image,
                    inputs=[image_input, food_history],
                    outputs=[food_history, result_output],
                    api_name="food_recognition"
                )
                
                food_clear_btn.click(
                    lambda: (None, ""),
                    None,
                    [food_history, result_output]
                )
                
    def _build_recipe_creation_tab(self):
        """构建菜谱创建标签页"""
        with gr.Column():
            # 基本信息
            title = gr.Textbox(
                label="菜谱名称",
                placeholder="请输入菜谱名称",
                max_lines=1
            )
            description = gr.Textbox(
                label="菜谱描述",
                placeholder="请简单描述这道菜",
                lines=3
            )
            
            # 食材和步骤
            ingredients = gr.Dataframe(
                headers=["食材", "用量"],
                label="食材清单",
                col_count=2,
                row_count=5,
                interactive=True
            )
            steps = gr.Dataframe(
                headers=["步骤", "描述"],
                label="烹饪步骤",
                col_count=2,
                row_count=5,
                interactive=True
            )
            
            # 其他信息
            with gr.Row():
                cooking_time = gr.Number(
                    label="烹饪时间（分钟）",
                    value=30,
                    minimum=1,
                    maximum=180
                )
                difficulty = gr.Dropdown(
                    label="难度等级",
                    choices=["简单", "中等", "困难"],
                    value="简单"
                )
                cuisine_type = gr.Dropdown(
                    label="菜系",
                    choices=["中餐", "西餐", "日料", "其他"],
                    value="中餐"
                )
            
            # 提交按钮
            submit_btn = gr.Button(
                "创建菜谱",
                variant="primary"
            )
            result = gr.Textbox(label="结果")
            
            submit_btn.click(
                fn=self._handle_recipe_creation,
                inputs=[
                    title, description, ingredients,
                    steps, cooking_time, difficulty,
                    cuisine_type
                ],
                outputs=result
            )
    
    def _build_recipe_search_tab(self):
        """构建菜谱搜索标签页"""
        with gr.Column():
            # 搜索条件
            with gr.Row():
                difficulty = gr.Dropdown(
                    label="难度等级",
                    choices=["全部", "简单", "中等", "困难"],
                    value="全部"
                )
                cuisine_type = gr.Dropdown(
                    label="菜系",
                    choices=["全部", "中餐", "西餐", "日料", "其他"],
                    value="全部"
                )
                max_time = gr.Slider(
                    label="最长烹饪时间（分钟）",
                    minimum=0,
                    maximum=180,
                    value=60,
                    step=5
                )
            
            # 搜索按钮
            search_btn = gr.Button(
                "搜索",
                variant="primary"
            )
            results = gr.Dataframe(
                headers=["菜名", "描述", "难度", "烹饪时间", "菜系"],
                label="搜索结果",
                interactive=False
            )
            
            search_btn.click(
                fn=self._handle_recipe_search,
                inputs=[difficulty, cuisine_type, max_time],
                outputs=results
            )
    
    async def _handle_recipe_creation(
        self,
        title: str,
        description: str,
        ingredients: list,
        steps: list,
        cooking_time: int,
        difficulty: str,
        cuisine_type: str
    ) -> str:
        """处理菜谱创建请求"""
        try:
            # 输入验证
            if not title or not ingredients or not steps:
                return "请填写必要的信息（菜名、食材、步骤）"
            
            # 转换数据格式
            recipe_data = {
                "title": title.strip(),
                "description": description.strip() if description else None,
                "ingredients": [
                    {"name": str(row[0]).strip(), "amount": str(row[1]).strip()}
                    for row in ingredients
                    if row[0] and row[1]
                ],
                "steps": [
                    {"step": str(i+1), "description": str(row[1]).strip()}
                    for i, row in enumerate(steps)
                    if row[1]
                ],
                "cooking_time": max(1, min(180, cooking_time)),
                "difficulty": difficulty,
                "cuisine_type": cuisine_type
            }
            
            # 创建菜谱
            recipe_id = await self.recipe_service.create_recipe(recipe_data)
            if recipe_id:
                return f"创建成功！菜谱ID: {recipe_id}"
            else:
                return "创建失败，请重试"
                
        except Exception as e:
            self.logger.error(f"创建菜谱失败: {str(e)}")
            return f"发生错误: {str(e)}"
    
    async def _handle_recipe_search(
        self,
        difficulty: str,
        cuisine_type: str,
        max_time: int
    ) -> list:
        """处理菜谱搜索请求"""
        try:
            # 准备搜索参数
            search_params = {}
            if difficulty != "全部":
                search_params["difficulty"] = difficulty
            if cuisine_type != "全部":
                search_params["cuisine_type"] = cuisine_type
            if max_time > 0:
                search_params["cooking_time"] = max_time
            
            # 搜索菜谱
            result = await self.recipe_service.search_recipes(**search_params)
            
            # 转换为显示格式
            return [
                [
                    recipe["title"],
                    recipe["description"] or "",
                    recipe["difficulty"],
                    recipe["cooking_time"],
                    recipe["cuisine_type"]
                ]
                for recipe in result["recipes"]
            ]
            
        except Exception as e:
            self.logger.error(f"搜索菜谱失败: {str(e)}")
            return []
    
    def launch(self, **kwargs):
        """启动Web应用
        
        Args:
            **kwargs: 传递给gradio launch的参数
        """
        # 合并配置参数
        launch_kwargs = {
            "server_name": config.HOST,
            "server_port": config.PORT,
            "debug": config.DEBUG,
        }
        
        # 如果配置了HTTPS，添加SSL证书配置
        if config.use_https and config.ssl_certfile and config.ssl_keyfile:
            launch_kwargs.update({
                "ssl_keyfile": config.ssl_keyfile,
                "ssl_certfile": config.ssl_certfile
            })
            self.logger.info("启用HTTPS支持")
        
        # 更新用户提供的参数
        launch_kwargs.update(kwargs)
        
        # 启动应用
        self.interface.launch(**launch_kwargs) 