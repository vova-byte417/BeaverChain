"""
Model Registry - 数据库服务
使用 SQLAlchemy ORM 提供模型版本的 CRUD 操作
"""
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import create_engine, and_, or_, desc, asc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import json
import difflib

from ..models.schemas import (
    ModelVersionCreate,
    ModelVersionUpdate,
    ModelVersionResponse,
    VersionStatus,
    VersionDiff,
    RollbackRequest
)

# SQLAlchemy ORM 模型定义
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean

Base = declarative_base()


class ModelVersionORM(Base):
    """模型版本 ORM 模型"""
    __tablename__ = "model_versions"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    owner_id = Column(String(64), nullable=True, index=True)
    project_id = Column(String(64), nullable=True, index=True)
    
    # JSON 配置字段
    weights_config = Column(JSON, nullable=True)
    prompt_config = Column(JSON, nullable=True)
    rag_config = Column(JSON, nullable=True)
    guardrails_config = Column(JSON, nullable=True)
    inference_params = Column(JSON, nullable=True)
    lineage_info = Column(JSON, nullable=True)
    evaluation_metrics = Column(JSON, nullable=True)
    
    tags = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, database_url: str = "sqlite:///./model_registry.db"):
        """
        初始化数据库服务
        
        Args:
            database_url: 数据库连接 URL，支持 SQLite、PostgreSQL 等
                          SQLite: sqlite:///./model_registry.db
                          PostgreSQL: postgresql://user:pass@localhost/db
        """
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建表
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def _orm_to_response(self, orm_model: ModelVersionORM) -> ModelVersionResponse:
        """将 ORM 模型转换为响应模型"""
        return ModelVersionResponse(
            id=str(orm_model.id),
            name=orm_model.name,
            version=orm_model.version,
            description=orm_model.description,
            status=VersionStatus(orm_model.status),
            tags=orm_model.tags or [],
            project_id=orm_model.project_id,
            weights_config=orm_model.weights_config,
            prompt_config=orm_model.prompt_config,
            rag_config=orm_model.rag_config,
            guardrails_config=orm_model.guardrails_config,
            inference_params=orm_model.inference_params,
            lineage_info=orm_model.lineage_info,
            evaluation_metrics=orm_model.evaluation_metrics,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )
    
    def create_model_version(
        self,
        data: ModelVersionCreate,
        owner_id: Optional[str] = None
    ) -> ModelVersionResponse:
        """创建模型版本"""
        session = self.get_session()
        try:
            # 检查 name + version 是否已存在
            existing = session.query(ModelVersionORM).filter(
                and_(
                    ModelVersionORM.name == data.name,
                    ModelVersionORM.version == data.version
                )
            ).first()
            
            if existing:
                raise ValueError(f"Model version '{data.name}' v{data.version} already exists")
            
            # 创建新记录
            model_id = str(uuid.uuid4())
            db_model = ModelVersionORM(
                id=model_id,
                name=data.name,
                version=data.version,
                description=data.description,
                status=data.status.value,
                owner_id=owner_id,
                project_id=data.project_id,
                tags=data.tags,
                weights_config=data.weights_config.dict() if data.weights_config else None,
                prompt_config=data.prompt_config.dict() if data.prompt_config else None,
                rag_config=data.rag_config.dict() if data.rag_config else None,
                guardrails_config=data.guardrails_config.dict() if data.guardrails_config else None,
                inference_params=data.inference_params.dict() if data.inference_params else None,
                lineage_info=data.lineage_info.dict() if data.lineage_info else None,
                evaluation_metrics=data.evaluation_metrics.dict() if data.evaluation_metrics else None
            )
            
            session.add(db_model)
            session.commit()
            session.refresh(db_model)
            
            return self._orm_to_response(db_model)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_model_version(self, model_id: str) -> Optional[ModelVersionResponse]:
        """获取单个模型版本"""
        session = self.get_session()
        try:
            db_model = session.query(ModelVersionORM).filter(ModelVersionORM.id == model_id).first()
            if db_model:
                return self._orm_to_response(db_model)
            return None
        finally:
            session.close()
    
    def get_model_version_by_name_and_version(self, name: str, version: str) -> Optional[ModelVersionResponse]:
        """通过名称和版本号获取模型版本"""
        session = self.get_session()
        try:
            db_model = session.query(ModelVersionORM).filter(
                and_(
                    ModelVersionORM.name == name,
                    ModelVersionORM.version == version
                )
            ).first()
            if db_model:
                return self._orm_to_response(db_model)
            return None
        finally:
            session.close()
    
    def list_model_versions(
        self,
        name: Optional[str] = None,
        status: Optional[VersionStatus] = None,
        project_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[ModelVersionResponse], int]:
        """
        列出模型版本
        
        Returns:
            (版本列表, 总数量)
        """
        session = self.get_session()
        try:
            query = session.query(ModelVersionORM)
            
            # 应用过滤条件
            filters = []
            if name:
                filters.append(ModelVersionORM.name.ilike(f"%{name}%"))
            if status:
                filters.append(ModelVersionORM.status == status.value)
            if project_id:
                filters.append(ModelVersionORM.project_id == project_id)
            if owner_id:
                filters.append(ModelVersionORM.owner_id == owner_id)
            if tags:
                # JSON 数组包含查询（PostgreSQL 专用语法，SQLite 使用不同方式）
                for tag in tags:
                    filters.append(func.json_extract(ModelVersionORM.tags, f'$[*]').like(f'%{tag}%'))
            
            if filters:
                query = query.filter(and_(*filters))
            
            # 获取总数
            total = query.count()
            
            # 排序
            if sort_order == "desc":
                query = query.order_by(desc(getattr(ModelVersionORM, sort_by, ModelVersionORM.created_at)))
            else:
                query = query.order_by(asc(getattr(ModelVersionORM, sort_by, ModelVersionORM.created_at)))
            
            # 分页
            query = query.offset(skip).limit(limit)
            
            db_models = query.all()
            
            return [self._orm_to_response(m) for m in db_models], total
        finally:
            session.close()
    
    def update_model_version(
        self,
        model_id: str,
        data: ModelVersionUpdate
    ) -> Optional[ModelVersionResponse]:
        """更新模型版本"""
        session = self.get_session()
        try:
            db_model = session.query(ModelVersionORM).filter(ModelVersionORM.id == model_id).first()
            if not db_model:
                return None
            
            # 更新字段
            update_data = data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if value is not None:
                    # 处理嵌套的 Pydantic 模型
                    if field in [
                        'weights_config', 'prompt_config', 'rag_config',
                        'guardrails_config', 'inference_params', 'evaluation_metrics'
                    ]:
                        setattr(db_model, field, value.dict() if hasattr(value, 'dict') else value)
                    else:
                        setattr(db_model, field, value.value if hasattr(value, 'value') else value)
            
            db_model.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(db_model)
            
            return self._orm_to_response(db_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_model_version(self, model_id: str) -> bool:
        """删除模型版本（软删除，设置状态为 archived）"""
        session = self.get_session()
        try:
            db_model = session.query(ModelVersionORM).filter(ModelVersionORM.id == model_id).first()
            if not db_model:
                return False
            
            # 软删除：设置状态为 archived
            db_model.status = VersionStatus.ARCHIVED.value
            db_model.updated_at = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def hard_delete_model_version(self, model_id: str) -> bool:
        """硬删除模型版本（从数据库彻底删除）"""
        session = self.get_session()
        try:
            db_model = session.query(ModelVersionORM).filter(ModelVersionORM.id == model_id).first()
            if not db_model:
                return False
            
            session.delete(db_model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _deep_diff(self, old_dict: Dict, new_dict: Dict, path: str = "") -> Dict[str, Any]:
        """
        深度对比两个字典，找出差异
        
        Returns:
            {
                "field_path": {
                    "old": value,
                    "new": value,
                    "change_type": "modified|added|removed"
                },
                ...
            }
        """
        diff_result = {}
        
        # 获取所有 key
        all_keys = set(old_dict.keys()) | set(new_dict.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)
            
            if key not in old_dict:
                diff_result[current_path] = {
                    "old": None,
                    "new": new_val,
                    "change_type": "added"
                }
            elif key not in new_dict:
                diff_result[current_path] = {
                    "old": old_val,
                    "new": None,
                    "change_type": "removed"
                }
            elif isinstance(old_val, dict) and isinstance(new_val, dict):
                # 递归对比嵌套字典
                nested_diff = self._deep_diff(old_val, new_val, current_path)
                diff_result.update(nested_diff)
            elif isinstance(old_val, list) and isinstance(new_val, list):
                # 对比列表
                if old_val != new_val:
                    diff_result[current_path] = {
                        "old": old_val,
                        "new": new_val,
                        "change_type": "modified"
                    }
            elif old_val != new_val:
                diff_result[current_path] = {
                    "old": old_val,
                    "new": new_val,
                    "change_type": "modified"
                }
        
        return diff_result
    
    def compare_versions(
        self,
        base_version_id: str,
        target_version_id: str
    ) -> Optional[VersionDiff]:
        """对比两个版本的差异"""
        base = self.get_model_version(base_version_id)
        target = self.get_model_version(target_version_id)
        
        if not base or not target:
            return None
        
        # 转换为字典进行对比
        base_dict = base.dict()
        target_dict = target.dict()
        
        # 主要配置字段对比
        config_fields = [
            'weights_config', 'prompt_config', 'rag_config',
            'guardrails_config', 'inference_params'
        ]
        
        changed_fields = {}
        for field in config_fields:
            base_val = base_dict.get(field) or {}
            target_val = target_dict.get(field) or {}
            
            if base_val != target_val:
                field_diff = self._deep_diff(base_val, target_val, field)
                changed_fields.update(field_diff)
        
        # 基本信息对比
        basic_fields = ['name', 'description', 'status', 'tags']
        for field in basic_fields:
            if base_dict.get(field) != target_dict.get(field):
                changed_fields[field] = {
                    "old": base_dict.get(field),
                    "new": target_dict.get(field),
                    "change_type": "modified"
                }
        
        # 评估指标变化
        eval_changes = None
        base_eval = base_dict.get('evaluation_metrics') or {}
        target_eval = target_dict.get('evaluation_metrics') or {}
        if base_eval != target_eval:
            eval_changes = {}
            for key in set(base_eval.keys()) | set(target_eval.keys()):
                old_val = base_eval.get(key)
                new_val = target_eval.get(key)
                if old_val != new_val and old_val is not None and new_val is not None:
                    change = None
                    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                        change = new_val - old_val
                    eval_changes[key] = {
                        "old": old_val,
                        "new": new_val,
                        "change": change
                    }
        
        return VersionDiff(
            base_version_id=base_version_id,
            target_version_id=target_version_id,
            base_version=base.version,
            target_version=target.version,
            changed_fields=changed_fields,
            evaluation_changes=eval_changes
        )
    
    def rollback_to_version(
        self,
        current_version_id: str,
        request: RollbackRequest,
        owner_id: Optional[str] = None
    ) -> Optional[ModelVersionResponse]:
        """
        回滚到指定版本
        
        Args:
            current_version_id: 当前版本 ID（要回滚的版本）
            request: 回滚请求（包含目标版本 ID）
            owner_id: 操作人 ID
        
        Returns:
            新版本（如果 create_new_version=True）或更新后的当前版本
        """
        target_version = self.get_model_version(request.target_version_id)
        if not target_version:
            raise ValueError(f"Target version not found: {request.target_version_id}")
        
        current_version = self.get_model_version(current_version_id)
        if not current_version:
            raise ValueError(f"Current version not found: {current_version_id}")
        
        if request.create_new_version:
            # 创建新版本
            new_version = ModelVersionCreate(
                name=current_version.name,
                version=self._increment_version(current_version.version),
                description=f"Rollback from v{current_version.version} to v{target_version.version}. Reason: {request.reason or 'Not specified'}",
                status=VersionStatus.DRAFT,
                tags=current_version.tags,
                weights_config=target_version.weights_config,
                prompt_config=target_version.prompt_config,
                rag_config=target_version.rag_config,
                guardrails_config=target_version.guardrails_config,
                inference_params=target_version.inference_params,
                lineage_info=None,  # 可以从 target_version 复制
                evaluation_metrics=target_version.evaluation_metrics
            )
            
            # 设置血缘信息
            from ..models.schemas import LineageInfo
            new_version.lineage_info = LineageInfo(
                parent_version_id=request.target_version_id,
                created_by=owner_id,
                creation_method="rollback"
            )
            
            return self.create_model_version(new_version, owner_id)
        else:
            # 原地更新当前版本
            update_data = ModelVersionUpdate(
                weights_config=target_version.weights_config,
                prompt_config=target_version.prompt_config,
                rag_config=target_version.rag_config,
                guardrails_config=target_version.guardrails_config,
                inference_params=target_version.inference_params,
                evaluation_metrics=target_version.evaluation_metrics
            )
            
            return self.update_model_version(current_version_id, update_data)
    
    def _increment_version(self, version: str) -> str:
        """递增版本号（patch 版本）"""
        try:
            parts = version.split('.')
            if len(parts) >= 3:
                patch = int(parts[2]) + 1
                return f"{parts[0]}.{parts[1]}.{patch}"
        except (ValueError, IndexError):
            pass
        
        # 如果格式不支持自动递增，添加时间戳后缀
        from datetime import datetime
        return f"{version}.rollback_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_version_history(self, name: str, limit: int = 20) -> List[ModelVersionResponse]:
        """获取某个模型的所有版本历史"""
        session = self.get_session()
        try:
            db_models = session.query(ModelVersionORM).filter(
                ModelVersionORM.name == name
            ).order_by(desc(ModelVersionORM.created_at)).limit(limit).all()
            
            return [self._orm_to_response(m) for m in db_models]
        finally:
            session.close()
    
    def get_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        session = self.get_session()
        try:
            query = session.query(ModelVersionORM)
            if project_id:
                query = query.filter(ModelVersionORM.project_id == project_id)
            
            total_count = query.count()
            
            # 按状态统计
            status_stats = {}
            for status in VersionStatus:
                count = query.filter(ModelVersionORM.status == status.value).count()
                status_stats[status.value] = count
            
            # 获取唯一的模型名称数量
            unique_names = session.query(ModelVersionORM.name).distinct().count()
            
            # 最近创建的版本
            recent = query.order_by(desc(ModelVersionORM.created_at)).limit(5).all()
            
            return {
                "total_versions": total_count,
                "unique_models": unique_names,
                "status_distribution": status_stats,
                "recent_versions": [
                    {"id": m.id, "name": m.name, "version": m.version, "created_at": m.created_at.isoformat()}
                    for m in recent
                ]
            }
        finally:
            session.close()
