"""Web应用入口模块"""

import gradio as gr
from typing import Dict, Optional, AsyncGenerator, List
import logging
from .config import config, setup_logging
from .services.user_service import UserService
from .services.recipe_service import RecipeService
from .services.ai_service_client import AIServiceClient
import time
import asyncio
import os

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
        self.logger = logging.getLogger(__name__)
        self.ai_client = AIServiceClient()
        self.user_service = UserService()
        self.recipe_service = RecipeService()
        self.interface = None
        self._debounce_timers = {}  # 用于防抖动的计时器字典
        
    def _create_debounce_key(self, message: str, history: List[Dict[str, str]]) -> str:
        """创建防抖动键"""
        return f"{message}_{len(history)}"
        
    async def _debounce(self, key: str, delay: float = 0.1):
        """防抖动处理"""
        if key in self._debounce_timers:
            self._debounce_timers[key] = time.time()
            return True
            
        self._debounce_timers[key] = time.time()
        await asyncio.sleep(delay)
        
        # 如果计时器值没有改变，说明在延迟期间没有新的调用
        if self._debounce_timers.get(key) == time.time():
            del self._debounce_timers[key]
            return False
            
        return True
        
    async def _handle_text_message(
        self,
        message: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理文本消息，支持流式输出"""
        try:
            if not message:
                yield [{"role": "assistant", "content": "请输入消息"}]
                return
                
            # 获取用户画像
            user_profile = await self.user_service.get_user_profile("test_user")
            
            # 添加用户消息到历史
            history.append({"role": "user", "content": message})
            yield history
            
            # 创建防抖动键
            debounce_key = self._create_debounce_key(message, history)
            last_update_time = time.time()
            current_response = ""
            
            # 处理消息并流式输出
            async for response_chunk in self.ai_client.chat_stream(
                messages=history,
                model="qwen2.5:14b",
                user_profile=user_profile
            ):
                if response_chunk:
                    current_response += response_chunk
                    current_time = time.time()
                    
                    # 如果距离上次更新超过100ms，更新UI
                    if (current_time - last_update_time) >= 0.1:
                        if len(history) > 0 and history[-1]["role"] == "assistant":
                            history[-1]["content"] = current_response
                        else:
                            history.append({"role": "assistant", "content": current_response})
                        yield history
                        last_update_time = current_time
            
            # 确保最后一次更新被发送
            if current_response:
                if len(history) > 0 and history[-1]["role"] == "assistant":
                    history[-1]["content"] = current_response
                else:
                    history.append({"role": "assistant", "content": current_response})
                yield history
                    
        except Exception as e:
            self.logger.error(f"处理文本消息失败: {e}")
            history.append({"role": "assistant", "content": f"处理失败: {str(e)}"})
            yield history
            
    async def _handle_voice_message(
        self,
        audio_data,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理语音消息，支持流式输出"""
        try:
            if audio_data is None:
                yield [{"role": "assistant", "content": "请先录制语音"}]
                return
                
            # 获取用户画像
            user_profile = await self.user_service.get_user_profile("test_user")
            
            # 语音转文字
            transcribed_text = await self.ai_client.process_voice(audio_data)
            if not transcribed_text:
                yield [{"role": "assistant", "content": "语音识别失败"}]
                return
                
            # 先显示用户输入
            history = [{"role": "user", "content": f"语音输入：{transcribed_text}"}]
            yield history
            
            # 创建防抖动键
            debounce_key = self._create_debounce_key(transcribed_text, history)
            last_update_time = time.time()
            current_response = ""
            
            # 处理消息并流式输出
            async for response_chunk in self.ai_client.chat_stream(
                messages=history,
                model="qwen2.5:14b",
                user_profile=user_profile
            ):
                if response_chunk:
                    current_response += response_chunk
                    current_time = time.time()
                    
                    # 如果距离上次更新超过100ms，更新UI
                    if (current_time - last_update_time) >= 0.1:
                        if len(history) > 0 and history[-1]["role"] == "assistant":
                            history[-1]["content"] = current_response
                        else:
                            history.append({"role": "assistant", "content": current_response})
                        yield history
                        last_update_time = current_time
            
            # 确保最后一次更新被发送
            if current_response:
                if len(history) > 0 and history[-1]["role"] == "assistant":
                    history[-1]["content"] = current_response
                else:
                    history.append({"role": "assistant", "content": current_response})
                yield history
                    
        except Exception as e:
            self.logger.error(f"处理语音消息失败: {e}")
            history.append({"role": "assistant", "content": f"处理失败: {str(e)}"})
            yield history
            
    async def _handle_image_message(
        self,
        image,
        caption: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理图片消息，支持流式输出"""
        try:
            if image is None:
                yield [{"role": "assistant", "content": "请先上传图片"}]
                return
                
            # 获取用户画像
            user_profile = await self.user_service.get_user_profile("test_user")
                
            # 显示处理中的状态
            history = [{"role": "user", "content": "图片上传成功"}]
            yield history
            
            history.append({"role": "assistant", "content": "正在识别图片中的食物..."})
            yield history
                
            # 图片识别
            recognition_result = await self.ai_client.recognize_food(image)
            if not recognition_result["success"]:
                history[-1]["content"] = f"图片识别失败: {recognition_result.get('message', '未知错误')}"
                yield history
                return
                
            # 构建消息
            food_items = recognition_result["food_items"]
            food_description = "图片中识别到的食物：" + ", ".join(
                [f"{item['name']}（置信度：{item['confidence']:.2%}）" 
                 for item in food_items]
            )
            
            # 更新识别结果
            history[-1]["content"] = food_description
            yield history
            
            # 如果有用户说明，添加到结果中
            if caption:
                history[-1]["content"] += f"\n用户说明：{caption}"
                yield history
                
            # 创建防抖动键
            debounce_key = self._create_debounce_key(food_description, history)
            last_update_time = time.time()
            current_response = ""
            
            # 处理消息并流式输出
            async for response_chunk in self.ai_client.chat_stream(
                messages=history,
                model="qwen2.5:14b",
                user_profile=user_profile
            ):
                if response_chunk:
                    current_response += response_chunk
                    current_time = time.time()
                    
                    # 如果距离上次更新超过100ms，更新UI
                    if (current_time - last_update_time) >= 0.1:
                        if len(history) > 0 and history[-1]["role"] == "assistant":
                            history[-1]["content"] = current_response
                        else:
                            history.append({"role": "assistant", "content": current_response})
                        yield history
                        last_update_time = current_time
            
            # 确保最后一次更新被发送
            if current_response:
                if len(history) > 0 and history[-1]["role"] == "assistant":
                    history[-1]["content"] = current_response
                else:
                    history.append({"role": "assistant", "content": current_response})
                yield history
                    
        except Exception as e:
            self.logger.error(f"处理图片消息失败: {e}")
            history.append({"role": "assistant", "content": f"处理失败: {str(e)}"})
            yield history
            
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
                    type="messages",
                    show_label=True,
                    show_share_button=False,
                    show_copy_button=True
                )
                with gr.Row():
                    text_input = gr.Textbox(
                        label="输入消息",
                        placeholder="请输入你的问题...",
                        lines=2
                    )
                    send_btn = gr.Button("发送")
                text_clear = gr.Button("清空对话")
                
                send_btn.click(
                    fn=self._handle_text_message,
                    inputs=[text_input, chat_history],
                    outputs=chat_history,
                    api_name="chat"
                ).then(
                    lambda: "", None, text_input  # 清空输入框
                )
                
                text_input.submit(
                    fn=self._handle_text_message,
                    inputs=[text_input, chat_history],
                    outputs=chat_history,
                    api_name="chat_submit"
                ).then(
                    lambda: "", None, text_input  # 清空输入框
                )
                
                text_clear.click(lambda: None, None, chat_history, queue=False)
            
            # 语音聊天
            with gr.Tab("🎤 语音聊天"):
                voice_history = gr.Chatbot(
                    label="对话历史",
                    height=400,
                    type="messages",
                    show_label=True,
                    show_share_button=False,
                    show_copy_button=True
                )
                audio_input = gr.Audio(
                    label="录制语音",
                    sources=["microphone", "upload"],
                    type="filepath",
                    format="wav"
                )
                voice_clear = gr.Button("清空对话")
                
                audio_input.change(
                    fn=self._handle_voice_message,
                    inputs=[audio_input, voice_history],
                    outputs=voice_history,
                    api_name="voice_chat",
                    queue=True
                )
                
                voice_clear.click(lambda: None, None, voice_history, queue=False)
            
            # 食物识别
            with gr.Tab("🍲 食物识别"):
                food_history = gr.Chatbot(
                    label="识别历史",
                    height=400,
                    type="messages",
                    show_label=True,
                    show_share_button=False,
                    show_copy_button=True
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
                        caption_input = gr.Textbox(
                            label="补充说明",
                            placeholder="请输入图片补充说明（可选）",
                            lines=2
                        )
                send_img_btn = gr.Button("发送")
                clear_img_btn = gr.Button("清空对话")

                send_img_btn.click(
                    fn=self._handle_image_message,
                    inputs=[image_input, caption_input, food_history],
                    outputs=food_history,
                    api_name="food_recognition",
                    queue=True
                )
                
                clear_img_btn.click(lambda: None, None, food_history, queue=False)
            
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
        # 初始化界面
        if self.interface is None:
            self.interface = self._build_interface()
            
        # 合并配置参数
        launch_kwargs = {
            "server_name": config.HOST,
            "server_port": config.PORT,
            "debug": config.DEBUG,
        }
        
        # 只有在SSL证书文件都存在的情况下才启用HTTPS
        if (config.use_https and config.ssl_certfile and config.ssl_keyfile and 
            os.path.exists(config.ssl_certfile) and os.path.exists(config.ssl_keyfile)):
            launch_kwargs.update({
                "ssl_keyfile": config.ssl_keyfile,
                "ssl_certfile": config.ssl_certfile
            })
            self.logger.info("启用HTTPS支持")
        else:
            self.logger.warning("SSL证书文件不存在或未配置，将使用HTTP模式")
            # 确保不使用SSL
            launch_kwargs.update({
                "ssl_keyfile": None,
                "ssl_certfile": None
            })
        
        # 更新用户提供的参数
        launch_kwargs.update(kwargs)
        
        try:
            # 启动应用
            self.interface.launch(**launch_kwargs)
        except OSError as e:
            if "Cannot find empty port" in str(e):
                self.logger.warning(f"端口 {launch_kwargs.get('server_port')} 被占用，尝试使用其他端口")
                # 移除特定端口，让Gradio自动选择可用端口
                launch_kwargs.pop('server_port', None)
                # 设置一个较大的端口范围
                launch_kwargs['server_port'] = 0  # 让系统自动分配端口
                self.interface.launch(**launch_kwargs)
            else:
                raise 