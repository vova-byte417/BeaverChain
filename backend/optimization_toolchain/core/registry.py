"""
优化工具链 - 优化器注册表
统一管理所有可用的优化器
"""
from typing import Dict, Type, List, Optional
from .base import BaseOptimizer, OptimizationType, OptimizationConfig


class OptimizationRegistry:
    """优化器注册表类"""
    
    _registry: Dict[str, Type[BaseOptimizer]] = {}
    _config_templates: Dict[str, Dict] = {}
    _descriptions: Dict[str, str] = {}
    
    @classmethod
    def register(
        cls,
        name: str,
        optimizer_class: Type[BaseOptimizer],
        config_template: Optional[Dict] = None,
        description: str = "",
        optimization_type: Optional[OptimizationType] = None,
    ) -> None:
        """
        注册优化器
        
        Args:
            name: 优化器名称（唯一标识）
            optimizer_class: 优化器类
            config_template: 配置模板
            description: 优化器描述
            optimization_type: 优化类型
        """
        cls._registry[name.lower()] = optimizer_class
        cls._descriptions[name.lower()] = description
        
        if config_template:
            cls._config_templates[name.lower()] = config_template
    
    @classmethod
    def get_optimizer(cls, name: str) -> Optional[Type[BaseOptimizer]]:
        """
        获取优化器类
        
        Args:
            name: 优化器名称
            
        Returns:
            优化器类，如果不存在则返回 None
        """
        return cls._registry.get(name.lower())
    
    @classmethod
    def list_optimizers(cls) -> List[str]:
        """
        列出所有已注册的优化器名称
        
        Returns:
            优化器名称列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def get_config_template(cls, name: str) -> Optional[Dict]:
        """
        获取优化器的配置模板
        
        Args:
            name: 优化器名称
            
        Returns:
            配置模板字典，如果不存在则返回 None
        """
        return cls._config_templates.get(name.lower())
    
    @classmethod
    def get_description(cls, name: str) -> Optional[str]:
        """
        获取优化器描述
        
        Args:
            name: 优化器名称
            
        Returns:
            优化器描述
        """
        return cls._descriptions.get(name.lower())
    
    @classmethod
    def get_optimizers_by_type(cls, opt_type: OptimizationType) -> List[str]:
        """
        按类型获取优化器列表
        
        Args:
            opt_type: 优化类型
            
        Returns:
            符合条件的优化器名称列表
        """
        # 这里简化实现，实际可以按类型分类
        return [
            name for name in cls._registry.keys()
            if opt_type.value.lower() in name.lower()
        ] or cls.list_optimizers()
    
    @classmethod
    def create_optimizer(
        cls,
        name: str,
        config: Optional[OptimizationConfig] = None,
        **kwargs,
    ) -> Optional[BaseOptimizer]:
        """
        创建优化器实例
        
        Args:
            name: 优化器名称
            config: 优化配置
            **kwargs: 额外的配置参数
            
        Returns:
            优化器实例，如果不存在则返回 None
        """
        optimizer_class = cls.get_optimizer(name)
        if not optimizer_class:
            return None
        
        if config is None:
            # 使用默认配置
            config = OptimizationConfig(
                name=f"{name}_optimization",
                optimization_type=OptimizationType.QUANTIZATION,
                **kwargs
            )
        
        return optimizer_class(config)
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict]:
        """
        获取所有配置模板
        
        Returns:
            所有配置模板字典
        """
        return dict(cls._config_templates)
    
    @classmethod
    def get_optimizer_info(cls, name: str) -> Optional[Dict]:
        """
        获取优化器详细信息
        
        Args:
            name: 优化器名称
            
        Returns:
            优化器信息字典
        """
        if name.lower() not in cls._registry:
            return None
        
        return {
            "name": name,
            "description": cls.get_description(name),
            "config_template": cls.get_config_template(name),
            "class_name": cls._registry[name.lower()].__name__,
        }
    
    @classmethod
    def get_all_info(cls) -> List[Dict]:
        """
        获取所有优化器信息
        
        Returns:
            所有优化器信息列表
        """
        return [cls.get_optimizer_info(name) for name in cls.list_optimizers()]


# 便捷函数
def register_optimizer(
    name: str,
    config_template: Optional[Dict] = None,
    description: str = "",
    optimization_type: Optional[OptimizationType] = None,
):
    """
    装饰器：注册优化器
    
    Args:
        name: 优化器名称
        config_template: 配置模板
        description: 优化器描述
        optimization_type: 优化类型
    """
    def decorator(cls):
        OptimizationRegistry.register(
            name=name,
            optimizer_class=cls,
            config_template=config_template,
            description=description,
            optimization_type=optimization_type,
        )
        return cls
    return decorator
