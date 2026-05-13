"""
Model Registry - Pydantic Schemas
定义所有请求/响应的数据结构
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class VersionStatus(str, Enum):
    """版本状态枚举"""
    DRAFT = "draft"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class WeightsConfig(BaseModel):
    """模型权重配置"""
    model_type: str = Field(..., description="模型类型: gpt4, claude, llama, custom 等")
    provider: str = Field(..., description="提供商: openai, anthropic, huggingface, local 等")
    model_id: str = Field(..., description="模型 ID 或名称")
    base_url: Optional[str] = Field(None, description="API 基础 URL（自定义模型时使用）")
    file_path: Optional[str] = Field(None, description="权重文件在存储中的路径")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    file_hash: Optional[str] = Field(None, description="文件哈希值（用于校验）")
    quantization: Optional[str] = Field(None, description="量化类型: fp16, int8, int4, gptq, awq 等")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数字典")
    lora_config: Optional[Dict[str, Any]] = Field(None, description="LoRA 配置")
    qlora_config: Optional[Dict[str, Any]] = Field(None, description="QLoRA 配置")


class PromptConfig(BaseModel):
    """Prompt 配置"""
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    user_prompt_template: Optional[str] = Field(None, description="用户提示词模板")
    variables: List[str] = Field(default_factory=list, description="模板变量列表")
    prompt_template_id: Optional[str] = Field(None, description="关联的 Prompt 模板 ID")
    version: Optional[str] = Field(None, description="Prompt 版本号")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="few-shot 示例")


class RAGConfig(BaseModel):
    """RAG 配置"""
    enabled: bool = Field(default=True, description="是否启用 RAG")
    knowledge_base_id: Optional[str] = Field(None, description="知识库 ID")
    embedding_model: str = Field(default="text-embedding-3-large", description="嵌入模型")
    embedding_dim: int = Field(default=1536, description="嵌入维度")
    chunk_size: int = Field(default=512, description="分块大小")
    chunk_overlap: int = Field(default=50, description="分块重叠")
    top_k: int = Field(default=5, description="返回结果数量")
    score_threshold: float = Field(default=0.8, description="相似度阈值")
    search_strategy: str = Field(default="hybrid", description="检索策略: hybrid, dense, sparse")
    rerank_enabled: bool = Field(default=False, description="是否启用重排序")
    rerank_model: Optional[str] = Field(None, description="重排序模型")
    rerank_top_n: int = Field(default=3, description="重排序后返回数量")
    query_expansion_enabled: bool = Field(default=False, description="是否启用查询扩展")


class GuardrailsConfig(BaseModel):
    """Guardrails 安全配置"""
    toxicity_filter_enabled: bool = Field(default=True, description="是否启用毒性过滤")
    toxicity_threshold: float = Field(default=0.7, description="毒性阈值")
    sensitive_words_enabled: bool = Field(default=True, description="是否启用敏感词过滤")
    sensitive_words_list: List[str] = Field(default_factory=list, description="自定义敏感词列表")
    hallucination_detection_enabled: bool = Field(default=True, description="是否启用幻觉检测")
    hallucination_threshold: float = Field(default=0.5, description="幻觉检测阈值")
    pii_detection_enabled: bool = Field(default=True, description="是否启用 PII 检测")
    pii_redact_enabled: bool = Field(default=True, description="是否启用 PII 脱敏")
    output_format_validation: Optional[str] = Field(None, description="输出格式验证: json, xml 等")
    custom_rules: List[Dict[str, Any]] = Field(default_factory=list, description="自定义规则")


class InferenceParams(BaseModel):
    """推理参数配置"""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样参数")
    top_k: int = Field(default=50, ge=1, description="Top K 采样")
    max_tokens: int = Field(default=2048, ge=1, description="最大生成 token 数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop_sequences: List[str] = Field(default_factory=list, description="停止序列")
    seed: Optional[int] = Field(None, description="随机种子（用于可复现性）")


class LineageInfo(BaseModel):
    """版本血缘信息"""
    parent_version_id: Optional[str] = Field(None, description="父版本 ID")
    forked_from: Optional[str] = Field(None, description="从哪个版本 Fork")
    derived_from: List[Dict[str, Any]] = Field(default_factory=list, description="派生来源列表")
    created_by: Optional[str] = Field(None, description="创建者 ID")
    creation_method: str = Field(default="manual", description="创建方式: manual, fork, rollback, auto")


class EvaluationMetrics(BaseModel):
    """评估指标"""
    hallucination_rate: Optional[float] = Field(None, description="幻觉率")
    toxicity_score: Optional[float] = Field(None, description="毒性评分")
    faithfulness: Optional[float] = Field(None, description="忠实度")
    relevance: Optional[float] = Field(None, description="相关性")
    bleu_score: Optional[float] = Field(None, description="BLEU 评分")
    rouge_score: Optional[Dict[str, float]] = Field(None, description="ROUGE 评分")
    avg_latency_ms: Optional[float] = Field(None, description="平均延迟（毫秒）")
    throughput: Optional[float] = Field(None, description="吞吐量（token/秒）")
    error_rate: Optional[float] = Field(None, description="错误率")
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="自定义指标")


class ModelVersionBase(BaseModel):
    """模型版本基础字段"""
    name: str = Field(..., min_length=1, max_length=255, description="模型名称")
    version: str = Field(..., min_length=1, max_length=50, description="版本号（SemVer 格式推荐）")
    description: Optional[str] = Field(None, description="版本描述")
    status: VersionStatus = Field(default=VersionStatus.DRAFT, description="版本状态")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    project_id: Optional[str] = Field(None, description="所属项目 ID")


class ModelVersionCreate(ModelVersionBase):
    """创建模型版本请求"""
    weights_config: Optional[WeightsConfig] = Field(None, description="权重配置")
    prompt_config: Optional[PromptConfig] = Field(None, description="Prompt 配置")
    rag_config: Optional[RAGConfig] = Field(None, description="RAG 配置")
    guardrails_config: Optional[GuardrailsConfig] = Field(None, description="Guardrails 配置")
    inference_params: Optional[InferenceParams] = Field(None, description="推理参数")
    lineage_info: Optional[LineageInfo] = Field(None, description="血缘信息")
    evaluation_metrics: Optional[EvaluationMetrics] = Field(None, description="评估指标")
    
    @validator('version')
    def validate_version(cls, v):
        """简单的版本号格式验证"""
        # 建议使用 SemVer 格式，如 1.0.0, 1.0.0-beta 等
        import re
        semver_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$'
        if not re.match(semver_pattern, v):
            raise ValueError(
                f"版本号 '{v}' 格式不正确，建议使用 SemVer 格式（如 1.0.0, 1.0.0-beta）"
            )
        return v


class ModelVersionUpdate(BaseModel):
    """更新模型版本请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    status: Optional[VersionStatus] = Field(None)
    tags: Optional[List[str]] = Field(None)
    weights_config: Optional[WeightsConfig] = Field(None)
    prompt_config: Optional[PromptConfig] = Field(None)
    rag_config: Optional[RAGConfig] = Field(None)
    guardrails_config: Optional[GuardrailsConfig] = Field(None)
    inference_params: Optional[InferenceParams] = Field(None)
    evaluation_metrics: Optional[EvaluationMetrics] = Field(None)


class ModelVersionResponse(ModelVersionBase):
    """模型版本响应"""
    id: str = Field(..., description="版本 ID")
    weights_config: Optional[WeightsConfig] = Field(None)
    prompt_config: Optional[PromptConfig] = Field(None)
    rag_config: Optional[RAGConfig] = Field(None)
    guardrails_config: Optional[GuardrailsConfig] = Field(None)
    inference_params: Optional[InferenceParams] = Field(None)
    lineage_info: Optional[LineageInfo] = Field(None)
    evaluation_metrics: Optional[EvaluationMetrics] = Field(None)
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        orm_mode = True


class VersionDiff(BaseModel):
    """版本差异对比结果"""
    base_version_id: str = Field(..., description="基准版本 ID")
    target_version_id: str = Field(..., description="目标版本 ID")
    base_version: str = Field(..., description="基准版本号")
    target_version: str = Field(..., description="目标版本号")
    changed_fields: Dict[str, Dict[str, Any]] = Field(..., description="变更的字段")
    added_fields: List[str] = Field(default_factory=list, description="新增的字段")
    removed_fields: List[str] = Field(default_factory=list, description="删除的字段")
    evaluation_changes: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="指标变化")


class RollbackRequest(BaseModel):
    """回滚请求"""
    target_version_id: str = Field(..., description="目标版本 ID")
    reason: Optional[str] = Field(None, description="回滚原因")
    create_new_version: bool = Field(default=True, description="是否创建新版本（True=创建新版本，False=原地修改）")


class ChunkUploadInfo(BaseModel):
    """分片上传信息"""
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., gt=0, description="文件总大小")
    chunk_size: int = Field(default=5 * 1024 * 1024, description="分片大小（默认 5MB）")
    content_type: Optional[str] = Field(None, description="内容类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ChunkUploadComplete(BaseModel):
    """分片上传完成请求"""
    upload_id: str = Field(..., description="上传会话 ID")
    chunks: List[Dict[str, Any]] = Field(..., description="分片列表")
    file_hash: Optional[str] = Field(None, description="文件哈希值")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool = Field(True, description="是否成功")
    upload_id: Optional[str] = Field(None, description="上传会话 ID")
    file_path: Optional[str] = Field(None, description="文件存储路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    message: Optional[str] = Field(None, description="提示信息")


# SQLAlchemy ORM Models (需要时引入 SQLAlchemy)
try:
    from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer, BigInteger
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.sql import func
    
    Base = declarative_base()
    
    class ModelVersionORM(Base):
        """模型版本 ORM 模型"""
        __tablename__ = "model_versions"
        
        id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
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
        
        tags = Column(JSON, nullable=True)  # List[str]
        
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
        
        __mapper_args__ = {
            "eager_defaults": True
        }

except ImportError:
    # SQLAlchemy 未安装时跳过 ORM 定义
    pass
