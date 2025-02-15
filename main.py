import logging
from src.config import setup_logging, config

# 配置日志
setup_logging(
    level="DEBUG" if config.DEBUG else "INFO",
    log_file=True,
    console=True
)

import subprocess
import os
from dotenv import load_dotenv
import sys
import signal
import atexit
import time
import threading
import queue

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

def log_stream(stream, log_queue: queue.Queue, name: str):
    """读取流并将输出放入队列"""
    try:
        for line in iter(stream.readline, ''):  # 改为空字符串，因为已经是文本模式
            if line.strip():  # 只处理非空行
                log_queue.put((name, line.strip()))
    except Exception as e:
        logger.error(f"日志流处理错误 ({name}): {e}")
    finally:
        stream.close()

class ServiceManager:
    def __init__(self):
        self.fastapi_process = None
        self.gradio_process = None
        self.is_shutting_down = False
        self.log_queue = queue.Queue()
        self.log_thread = None
        self.log_threads = []  # 保存所有日志线程的引用

    def _start_log_monitor(self):
        """启动日志监控线程"""
        def monitor():
            while not self.is_shutting_down:
                try:
                    name, line = self.log_queue.get(timeout=1)
                    if line:
                        logger.info(f"[{name}] {line}")
                except queue.Empty:
                    continue
                except Exception as e:
                    if not self.is_shutting_down:  # 只在非关闭状态下报告错误
                        logger.error(f"日志监控错误: {e}")
                    break

        self.log_thread = threading.Thread(target=monitor, daemon=True)
        self.log_thread.start()

    def _start_process_log_threads(self, process, name):
        """启动进程的日志监控线程"""
        stdout_thread = threading.Thread(
            target=log_stream,
            args=(process.stdout, self.log_queue, f"{name}-Out"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=log_stream,
            args=(process.stderr, self.log_queue, f"{name}-Err"),
            daemon=True
        )
        stdout_thread.start()
        stderr_thread.start()
        self.log_threads.extend([stdout_thread, stderr_thread])

    def run_fastapi(self):
        """启动FastAPI服务"""
        try:
            # 获取SSL配置
            use_https = os.getenv("USE_HTTPS", "false").lower() == "true"
            ssl_certfile = os.getenv("SSL_CERTFILE")
            ssl_keyfile = os.getenv("SSL_KEYFILE")
            
            # 展开路径中的用户目录符号 (~)
            if ssl_certfile:
                ssl_certfile = os.path.expanduser(ssl_certfile)
            if ssl_keyfile:
                ssl_keyfile = os.path.expanduser(ssl_keyfile)
            
            # 准备命令行参数
            cmd = [
                sys.executable,
                "-m", "uvicorn",
                "src.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            
            # 添加SSL配置
            if use_https and ssl_certfile and ssl_keyfile:
                if os.path.exists(ssl_certfile) and os.path.exists(ssl_keyfile):
                    cmd.extend([
                        "--ssl-keyfile", ssl_keyfile,
                        "--ssl-certfile", ssl_certfile
                    ])
                else:
                    logger.warning("SSL证书文件不存在，将使用HTTP模式启动")
            
            # 启动FastAPI进程
            self.fastapi_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动日志处理线程
            self._start_process_log_threads(self.fastapi_process, "FastAPI")
            logger.info("FastAPI服务已启动")
            
        except Exception as e:
            logger.error(f"启动FastAPI服务失败: {e}")
            raise

    def run_gradio(self):
        """运行 Gradio 服务"""
        try:
            cmd = [sys.executable, "-c", """
import logging
# 禁用所有日志输出
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('uvicorn').setLevel(logging.CRITICAL)
logging.getLogger('fastapi').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('httpcore').setLevel(logging.CRITICAL)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
logging.getLogger('PIL').setLevel(logging.CRITICAL)
logging.getLogger('gradio').setLevel(logging.CRITICAL)

from src.web_app import WebApp
app = WebApp()
app.launch(
    server_name='localhost', 
    server_port=7860, 
    share=False,
    show_error=True,
    quiet=True  # 设置为 True 以减少输出
)
"""]
            self.gradio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8'
            )
            
            # 启动输出监控线程
            self._start_process_log_threads(self.gradio_process, "Gradio")
            
            logger.info("Gradio 服务已启动 - http://localhost:7860")
        except Exception as e:
            logger.error(f"Gradio 服务启动失败: {e}")
            raise

    def cleanup(self):
        """清理资源"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("正在清理资源...")
        
        # 优雅关闭子进程
        for process, name in [
            (self.fastapi_process, "FastAPI"), 
            (self.gradio_process, "Gradio")
        ]:
            if process:
                logger.info(f"正在关闭 {name} 服务...")
                process.terminate()
                try:
                    # 等待进程结束，最多等待5秒
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} 服务未能在5秒内关闭，强制结束")
                    process.kill()
                logger.info(f"{name} 服务已关闭")
        
        # 等待所有日志线程结束
        for thread in self.log_threads:
            try:
                thread.join(timeout=2)
            except TimeoutError:
                logger.warning(f"日志线程 {thread.name} 未能及时结束")

    def signal_handler(self, signum, frame):
        """处理信号"""
        logger.info(f"收到信号 {signum}，正在优雅关闭...")
        self.cleanup()
        sys.exit(0)

def main():
    manager = ServiceManager()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # 注册清理函数
    atexit.register(manager.cleanup)
    
    try:
        logger.info("正在启动服务...")
        
        # 启动日志监控
        manager._start_log_monitor()
        
        # 启动服务
        manager.run_fastapi()
        manager.run_gradio()
        
        # 等待进程结束，同时检查子进程状态
        while True:
            if manager.fastapi_process.poll() is not None:
                logger.error("FastAPI 服务意外退出")
                break
            if manager.gradio_process.poll() is not None:
                logger.error("Gradio 服务意外退出")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"服务运行出错: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()