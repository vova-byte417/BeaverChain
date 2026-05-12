"""
Model Registry - FastAPI 路由
提供完整的 REST API 接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Depends, status
from fastapi.responses import StreamingResponse
from datetime import datetime
import io

from ..models.schemas import (
    ModelVersionCreate,
    ModelVersionUpdate,
    ModelVersionResponse,
    VersionStatus,
    VersionDiff,
    RollbackRequest,
    ChunkUploadInfo,
    ChunkUploadComplete,
    FileUploadResponse,
)
from ..services.database import DatabaseService
from ..services.storage import StorageService


# 依赖注入函数
def get_db_service():
    """获取数据库服务实例"""
    return DatabaseService()


def get_storage_service():
    """获取存储服务实例（默认本地存储）"""
    import os
    base_path = os.environ.get(
        "MODEL_REGISTRY_STORAGE_PATH",
        "./model_registry_files"
    )
    return StorageService.create_local(base_path)


router = APIRouter(prefix="/api/v1/model-versions", tags=["Model Registry"])


@router.post(
    "",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建模型版本",
    description="创建一个新的模型版本，包含所有配置信息"
)
async def create_model_version(
    data: ModelVersionCreate,
    db: DatabaseService = Depends(get_db_service),
):
    try:
        return db.create_model_version(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="列出模型版本",
    description="获取模型版本列表，支持过滤、分页、排序"
)
async def list_model_versions(
    name: Optional[str] = Query(None, description="按名称过滤（支持模糊搜索）"),
    status: Optional[VersionStatus] = Query(None, description="按状态过滤"),
    project_id: Optional[str] = Query(None, description="按项目 ID 过滤"),
    tags: Optional[List[str]] = Query(None, description="按标签过滤"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向：asc 或 desc"),
    db: DatabaseService = Depends(get_db_service),
):
    try:
        versions, total = db.list_model_versions(
            name=name,
            status=status,
            project_id=project_id,
            tags=tags,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "success": True,
            "data": [v.dict() for v in versions],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": (skip + len(versions)) < total
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{model_id}",
    response_model=ModelVersionResponse,
    summary="获取模型版本详情",
    description="获取指定 ID 的模型版本详细信息"
)
async def get_model_version(
    model_id: str,
    db: DatabaseService = Depends(get_db_service),
):
    try:
        version = db.get_model_version(model_id)
        if not version:
            raise HTTPException(status_code=404, detail="Model version not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/name/{name}/version/{version}",
    response_model=ModelVersionResponse,
    summary="通过名称和版本号获取",
    description="通过模型名称和版本号获取版本详情"
)
async def get_model_version_by_name_version(
    name: str,
    version: str,
    db: DatabaseService = Depends(get_db_service),
):
    try:
        model_version = db.get_model_version_by_name_and_version(name, version)
        if not model_version:
            raise HTTPException(status_code=404, detail="Model version not found")
        return model_version
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/{model_id}",
    response_model=ModelVersionResponse,
    summary="更新模型版本",
    description="更新模型版本的配置信息（支持部分更新）"
)
async def update_model_version(
    model_id: str,
    data: ModelVersionUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    try:
        updated = db.update_model_version(model_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Model version not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{model_id}",
    summary="删除模型版本",
    description="删除模型版本（软删除，标记为 archived 状态）"
)
async def delete_model_version(
    model_id: str,
    hard_delete: bool = Query(False, description="是否硬删除（彻底从数据库删除）"),
    db: DatabaseService = Depends(get_db_service),
):
    try:
        if hard_delete:
            success = db.hard_delete_model_version(model_id)
        else:
            success = db.delete_model_version(model_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        
        return {
            "success": True,
            "message": f"Model version {model_id} {'hard ' if hard_delete else ''}deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/compare",
    response_model=VersionDiff,
    summary="对比两个版本",
    description="对比两个模型版本的配置差异"
)
async def compare_versions(
    base_id: str = Query(..., description="基准版本 ID"),
    target_id: str = Query(..., description="目标版本 ID"),
    db: DatabaseService = Depends(get_db_service),
):
    try:
        diff = db.compare_versions(base_id, target_id)
        if not diff:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        return diff
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/{model_id}/rollback",
    response_model=ModelVersionResponse,
    summary="回滚版本",
    description="回滚到指定的历史版本"
)
async def rollback_version(
    model_id: str,
    request: RollbackRequest,
    db: DatabaseService = Depends(get_db_service),
):
    try:
        result = db.rollback_to_version(model_id, request)
        if not result:
            raise HTTPException(status_code=400, detail="Rollback failed")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/history/{name}",
    response_model=List[ModelVersionResponse],
    summary="获取版本历史",
    description="获取指定模型名称的所有版本历史"
)
async def get_version_history(
    name: str,
    limit: int = Query(20, ge=1, le=100, description="返回的最大记录数"),
    db: DatabaseService = Depends(get_db_service),
):
    try:
        history = db.get_version_history(name, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/statistics/summary",
    response_model=Dict[str, Any],
    summary="获取统计信息",
    description="获取模型版本库的统计概览"
)
async def get_statistics(
    project_id: Optional[str] = Query(None, description="按项目 ID 过滤"),
    db: DatabaseService = Depends(get_db_service),
):
    try:
        stats = db.get_statistics(project_id)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== 文件上传相关 API ====================

@router.post(
    "/upload/init",
    response_model=FileUploadResponse,
    summary="初始化分片上传",
    description="初始化大文件分片上传会话，获取 upload_id"
)
async def initiate_upload(
    info: ChunkUploadInfo,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        upload_id = storage.initiate_multipart_upload(
            info.file_name,
            metadata=info.metadata
        )
        return FileUploadResponse(
            success=True,
            upload_id=upload_id,
            message=f"Upload initiated successfully, chunk_size={info.chunk_size} bytes"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")


@router.post(
    "/upload/chunk",
    response_model=FileUploadResponse,
    summary="上传单个分片",
    description="上传单个文件分片"
)
async def upload_chunk(
    upload_id: str = Form(..., description="上传会话 ID"),
    chunk_number: int = Form(..., ge=1, description="分片序号（从 1 开始）"),
    chunk_file: UploadFile = File(..., description="分片文件内容"),
    storage: StorageService = Depends(get_storage_service),
):
    try:
        chunk_data = await chunk_file.read()
        
        chunk_info = storage.upload_chunk(
            upload_id=upload_id,
            chunk_number=chunk_number,
            chunk_data=chunk_data
        )
        
        return FileUploadResponse(
            success=True,
            upload_id=upload_id,
            message=f"Chunk {chunk_number} uploaded successfully, size={chunk_info['chunk_size']} bytes"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload chunk: {str(e)}")


@router.post(
    "/upload/complete",
    response_model=FileUploadResponse,
    summary="完成分片上传",
    description="完成所有分片上传，合并为完整文件"
)
async def complete_upload(
    data: ChunkUploadComplete,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        file_path = storage.complete_multipart_upload(
            upload_id=data.upload_id,
            chunks=data.chunks
        )
        
        file_size = storage.get_file_size(file_path)
        
        return FileUploadResponse(
            success=True,
            upload_id=data.upload_id,
            file_path=file_path,
            file_size=file_size,
            message="File upload completed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete upload: {str(e)}")


@router.post(
    "/upload/abort",
    summary="中止分片上传",
    description="中止分片上传，清理已上传的分片"
)
async def abort_upload(
    upload_id: str,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        success = storage.abort_multipart_upload(upload_id)
        if success:
            return {"success": True, "message": f"Upload {upload_id} aborted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Upload session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to abort upload: {str(e)}")


@router.post(
    "/upload/simple",
    response_model=FileUploadResponse,
    summary="简单文件上传",
    description="小文件直接上传（不使用分片），推荐用于 < 50MB 的文件"
)
async def simple_upload(
    file: UploadFile = File(..., description="要上传的文件"),
    file_name: Optional[str] = Form(None, description="自定义文件名（可选）"),
    storage: StorageService = Depends(get_storage_service),
):
    try:
        content = await file.read()
        actual_filename = file_name or file.filename or f"upload_{int(datetime.now().timestamp())}"
        
        # 生成存储路径
        import uuid
        file_ext = actual_filename.split('.')[-1] if '.' in actual_filename else 'bin'
        relative_path = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{str(uuid.uuid4())}.{file_ext}"
        
        file_hash = storage.calculate_file_hash(content)
        metadata = {
            "original_filename": actual_filename,
            "content_type": file.content_type,
            "file_hash": file_hash,
            "uploaded_at": datetime.now().isoformat()
        }
        
        saved_path = storage.save_file(relative_path, content, metadata)
        
        return FileUploadResponse(
            success=True,
            file_path=saved_path,
            file_size=len(content),
            message=f"File uploaded successfully, hash={file_hash}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get(
    "/files/{file_path:path}",
    summary="下载文件",
    description="下载存储的模型权重文件"
)
async def download_file(
    file_path: str,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        if not storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_content = storage.get_file(file_path)
        filename = file_path.split('/')[-1]
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get(
    "/files/{file_path:path}/metadata",
    summary="获取文件元数据",
    description="获取文件的元数据信息"
)
async def get_file_metadata(
    file_path: str,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        if not storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        metadata = storage.get_file_metadata(file_path)
        return {"success": True, "data": metadata}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.delete(
    "/files/{file_path:path}",
    summary="删除文件",
    description="删除存储的文件"
)
async def delete_file(
    file_path: str,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        success = storage.delete_file(file_path)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"success": True, "message": f"File {file_path} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get(
    "/files/{file_path:path}/exists",
    summary="检查文件是否存在",
    description="检查文件是否存在于存储中"
)
async def check_file_exists(
    file_path: str,
    storage: StorageService = Depends(get_storage_service),
):
    try:
        exists = storage.file_exists(file_path)
        return {"success": True, "exists": exists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check file existence: {str(e)}")
