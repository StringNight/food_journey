"""
监控服务模块

提供系统性能监控、统计和报警功能
"""

from typing import Dict, List, Optional, Any
import logging
import psutil
import time
from datetime import datetime, timedelta
from .database_service import DatabaseService
from .cache_service import CacheService
from .index_service import IndexService

class MonitorService:
    def __init__(
        self,
        db_service: DatabaseService,
        cache_service: CacheService,
        index_service: IndexService
    ):
        """初始化监控服务
        
        Args:
            db_service: 数据库服务实例
            cache_service: 缓存服务实例
            index_service: 索引服务实例
        """
        self.db_service = db_service
        self.cache_service = cache_service
        self.index_service = index_service
        self.logger = logging.getLogger(__name__)
        
        # 性能指标
        self.metrics = {
            "system": {},
            "database": {},
            "cache": {},
            "api": {}
        }
        
        # 警报阈值
        self.thresholds = {
            "cpu_usage": 80,  # CPU使用率阈值（%）
            "memory_usage": 80,  # 内存使用率阈值（%）
            "disk_usage": 80,  # 磁盘使用率阈值（%）
            "slow_query": 1000,  # 慢查询阈值（毫秒）
            "error_rate": 5,  # 错误率阈值（%）
            "cache_miss_rate": 20  # 缓存未命中率阈值（%）
        }
    
    async def collect_metrics(self):
        """收集所有监控指标"""
        try:
            # 收集系统指标
            self.metrics["system"] = self._collect_system_metrics()
            
            # 收集数据库指标
            self.metrics["database"] = await self._collect_database_metrics()
            
            # 收集缓存指标
            self.metrics["cache"] = self._collect_cache_metrics()
            
            # 收集API指标
            self.metrics["api"] = await self._collect_api_metrics()
            
            # 检查警报
            await self._check_alerts()
            
            return self.metrics
            
        except Exception as e:
            self.logger.error(f"收集监控指标失败: {str(e)}")
            return {}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络IO
            net_io = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": disk.percent
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {str(e)}")
            return {}
    
    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """收集数据库指标"""
        try:
            # 数据库统计信息
            db_stats = self.db_service.get_stats()
            
            # 表统计信息
            table_stats = await self.index_service.analyze_table_stats()
            
            # 连接池信息
            pool_stats = {
                "size": self.db_service.pool.get_size(),
                "free": self.db_service.pool.get_size() - 
                        len(self.db_service.pool._holders),
                "min": self.db_service.min_connections,
                "max": self.db_service.max_connections
            }
            
            # 查询性能统计
            query = """
                SELECT 
                    datname, 
                    numbackends, 
                    xact_commit, 
                    xact_rollback,
                    blks_read, 
                    blks_hit,
                    tup_returned, 
                    tup_fetched,
                    tup_inserted, 
                    tup_updated, 
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = $1
            """
            db_performance = await self.db_service.fetch_one(
                query, 
                self.db_service.database
            )
            
            return {
                "stats": db_stats,
                "table_stats": table_stats,
                "pool": pool_stats,
                "performance": db_performance,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"收集数据库指标失败: {str(e)}")
            return {}
    
    def _collect_cache_metrics(self) -> Dict[str, Any]:
        """收集缓存指标"""
        try:
            # 缓存统计信息
            cache_stats = self.cache_service.get_stats()
            
            # 计算命中率
            total_requests = (
                cache_stats.get("hits", 0) + 
                cache_stats.get("misses", 0)
            )
            hit_rate = (
                cache_stats.get("hits", 0) / total_requests * 100
                if total_requests > 0 else 0
            )
            
            return {
                "stats": cache_stats,
                "hit_rate": f"{hit_rate:.2f}%",
                "miss_rate": f"{100 - hit_rate:.2f}%",
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"收集缓存指标失败: {str(e)}")
            return {}
    
    async def _collect_api_metrics(self) -> Dict[str, Any]:
        """收集API指标"""
        try:
            # 查询API请求统计
            query = """
                SELECT 
                    endpoint,
                    COUNT(*) as total_requests,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors,
                    MIN(response_time) as min_response_time,
                    MAX(response_time) as max_response_time
                FROM api_logs
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY endpoint
                ORDER BY total_requests DESC
            """
            api_stats = await self.db_service.fetch(query)
            
            # 计算总体统计
            total_requests = sum(
                stat["total_requests"] for stat in api_stats
            )
            total_errors = sum(
                stat["errors"] for stat in api_stats
            )
            error_rate = (
                total_errors / total_requests * 100
                if total_requests > 0 else 0
            )
            
            return {
                "endpoints": api_stats,
                "summary": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate": f"{error_rate:.2f}%"
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"收集API指标失败: {str(e)}")
            return {}
    
    async def _check_alerts(self):
        """检查警报条件"""
        try:
            alerts = []
            
            # 检查系统指标
            system = self.metrics["system"]
            if system.get("cpu", {}).get("usage_percent", 0) > self.thresholds["cpu_usage"]:
                alerts.append({
                    "level": "warning",
                    "message": f"CPU使用率过高: {system['cpu']['usage_percent']}%"
                })
            
            if system.get("memory", {}).get("usage_percent", 0) > self.thresholds["memory_usage"]:
                alerts.append({
                    "level": "warning",
                    "message": f"内存使用率过高: {system['memory']['usage_percent']}%"
                })
            
            if system.get("disk", {}).get("usage_percent", 0) > self.thresholds["disk_usage"]:
                alerts.append({
                    "level": "warning",
                    "message": f"磁盘使用率过高: {system['disk']['usage_percent']}%"
                })
            
            # 检查数据库指标
            db = self.metrics["database"]
            if db.get("stats", {}).get("slow_queries", 0) > 0:
                alerts.append({
                    "level": "warning",
                    "message": f"存在慢查询: {db['stats']['slow_queries']} 个"
                })
            
            # 检查缓存指标
            cache = self.metrics["cache"]
            miss_rate = float(cache.get("miss_rate", "0").rstrip("%"))
            if miss_rate > self.thresholds["cache_miss_rate"]:
                alerts.append({
                    "level": "warning",
                    "message": f"缓存未命中率过高: {miss_rate}%"
                })
            
            # 检查API指标
            api = self.metrics["api"]
            error_rate = float(
                api.get("summary", {})
                .get("error_rate", "0")
                .rstrip("%")
            )
            if error_rate > self.thresholds["error_rate"]:
                alerts.append({
                    "level": "error",
                    "message": f"API错误率过高: {error_rate}%"
                })
            
            # 记录警报
            if alerts:
                self.logger.warning("检测到以下警报:")
                for alert in alerts:
                    self.logger.warning(
                        f"[{alert['level']}] {alert['message']}"
                    )
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"检查警报失败: {str(e)}")
            return []
    
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """更新警报阈值
        
        Args:
            new_thresholds: 新的阈值设置
        """
        self.thresholds.update(new_thresholds)
        self.logger.info("警报阈值已更新")
    
    async def get_performance_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """生成性能报告
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict[str, Any]: 性能报告
        """
        try:
            # 查询时间段内的性能数据
            query = """
                SELECT 
                    date_trunc('hour', created_at) as time,
                    COUNT(*) as requests,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as errors
                FROM api_logs
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY date_trunc('hour', created_at)
                ORDER BY time
            """
            performance_data = await self.db_service.fetch(
                query,
                start_time,
                end_time
            )
            
            # 计算统计信息
            total_requests = sum(
                row["requests"] for row in performance_data
            )
            total_errors = sum(
                row["errors"] for row in performance_data
            )
            avg_response_time = (
                sum(row["avg_response_time"] for row in performance_data) /
                len(performance_data) if performance_data else 0
            )
            
            return {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "summary": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate": f"{total_errors/total_requests*100:.2f}%",
                    "avg_response_time": f"{avg_response_time:.2f}ms"
                },
                "hourly_data": performance_data
            }
            
        except Exception as e:
            self.logger.error(f"生成性能报告失败: {str(e)}")
            return {} 