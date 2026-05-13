"""
Model Registry - 存储服务
支持本地文件系统和 S3 兼容对象存储，提供分片上传功能
"""
import os
import io
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    def save_file(self, file_path: str, content: bytes, metadata: Optional[Dict] = None) -> str:
        """保存文件"""
        pass
    
    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        """获取文件内容"""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据"""
        pass
    
    @abstractmethod
    def initiate_multipart_upload(self, file_name: str, metadata: Optional[Dict] = None) -> str:
        """初始化分片上传，返回 upload_id"""
        pass
    
    @abstractmethod
    def upload_chunk(self, upload_id: str, chunk_number: int, chunk_data: bytes) -> Dict[str, Any]:
        """上传单个分片"""
        pass
    
    @abstractmethod
    def complete_multipart_upload(self, upload_id: str, chunks: List[Dict[str, Any]]) -> str:
        """完成分片上传，返回最终文件路径"""
        pass
    
    @abstractmethod
    def abort_multipart_upload(self, upload_id: str) -> bool:
        """中止分片上传"""
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储后端"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 分片上传的临时目录
        self.chunk_dir = self.base_path / ".chunks"
        self.chunk_dir.mkdir(exist_ok=True)
        
        # 分片上传会话存储
        self.upload_sessions: Dict[str, Dict] = {}
        self._load_sessions()
    
    def _get_full_path(self, file_path: str) -> Path:
        """获取完整的本地路径"""
        # 防止路径遍历攻击
        full_path = (self.base_path / file_path).resolve()
        if not str(full_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Invalid file path: {file_path}")
        return full_path
    
    def _save_sessions(self):
        """保存上传会话到磁盘"""
        sessions_file = self.chunk_dir / "_sessions.json"
        with open(sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.upload_sessions, f, indent=2, default=str)
    
    def _load_sessions(self):
        """从磁盘加载上传会话"""
        sessions_file = self.chunk_dir / "_sessions.json"
        if sessions_file.exists():
            with open(sessions_file, 'r', encoding='utf-8') as f:
                self.upload_sessions = json.load(f)
    
    def save_file(self, file_path: str, content: bytes, metadata: Optional[Dict] = None) -> str:
        """保存文件到本地"""
        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        # 保存元数据
        if metadata:
            meta_path = full_path.with_suffix(full_path.suffix + '.meta')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        return file_path
    
    def get_file(self, file_path: str) -> bytes:
        """获取文件内容"""
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        try:
            full_path = self._get_full_path(file_path)
            return full_path.exists()
        except ValueError:
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            full_path = self._get_full_path(file_path)
            if full_path.exists():
                full_path.unlink()
                
                # 同时删除元数据文件
                meta_path = full_path.with_suffix(full_path.suffix + '.meta')
                if meta_path.exists():
                    meta_path.unlink()
                
                return True
            return False
        except Exception:
            return False
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据"""
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = full_path.stat()
        
        # 尝试读取元数据文件
        metadata = {}
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        return {
            "file_path": file_path,
            "file_size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "custom_metadata": metadata
        }
    
    def initiate_multipart_upload(self, file_name: str, metadata: Optional[Dict] = None) -> str:
        """初始化分片上传"""
        upload_id = str(uuid.uuid4())
        
        # 创建上传会话
        self.upload_sessions[upload_id] = {
            "file_name": file_name,
            "metadata": metadata or {},
            "chunks": [],
            "created_at": datetime.now().isoformat(),
            "chunk_dir": str(self.chunk_dir / upload_id)
        }
        
        # 创建分片目录
        (self.chunk_dir / upload_id).mkdir(exist_ok=True)
        
        self._save_sessions()
        return upload_id
    
    def upload_chunk(self, upload_id: str, chunk_number: int, chunk_data: bytes) -> Dict[str, Any]:
        """上传单个分片"""
        if upload_id not in self.upload_sessions:
            raise ValueError(f"Upload session not found: {upload_id}")
        
        session = self.upload_sessions[upload_id]
        
        # 保存分片到临时文件
        chunk_file = self.chunk_dir / upload_id / f"chunk_{chunk_number:06d}"
        with open(chunk_file, 'wb') as f:
            f.write(chunk_data)
        
        # 计算分片哈希
        chunk_hash = hashlib.md5(chunk_data).hexdigest()
        
        chunk_info = {
            "chunk_number": chunk_number,
            "chunk_size": len(chunk_data),
            "chunk_hash": chunk_hash,
            "chunk_path": str(chunk_file)
        }
        
        session["chunks"].append(chunk_info)
        self._save_sessions()
        
        return chunk_info
    
    def complete_multipart_upload(self, upload_id: str, chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        """完成分片上传"""
        if upload_id not in self.upload_sessions:
            raise ValueError(f"Upload session not found: {upload_id}")
        
        session = self.upload_sessions[upload_id]
        
        # 按分片序号排序
        session_chunks = sorted(session["chunks"], key=lambda x: x["chunk_number"])
        
        # 合并所有分片
        file_ext = Path(session["file_name"]).suffix
        relative_path = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{upload_id}{file_ext}"
        full_path = self._get_full_path(relative_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as outfile:
            for chunk in session_chunks:
                chunk_path = Path(chunk["chunk_path"])
                if chunk_path.exists():
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
        
        # 计算文件哈希
        with open(full_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # 保存元数据
        metadata = {
            **session["metadata"],
            "upload_id": upload_id,
            "file_hash": file_hash,
            "chunks_count": len(session_chunks)
        }
        meta_path = full_path.with_suffix(full_path.suffix + '.meta')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # 清理临时分片文件
        import shutil
        shutil.rmtree(self.chunk_dir / upload_id, ignore_errors=True)
        
        # 删除会话
        del self.upload_sessions[upload_id]
        self._save_sessions()
        
        return relative_path
    
    def abort_multipart_upload(self, upload_id: str) -> bool:
        """中止分片上传"""
        if upload_id not in self.upload_sessions:
            return False
        
        # 清理临时分片文件
        import shutil
        shutil.rmtree(self.chunk_dir / upload_id, ignore_errors=True)
        
        # 删除会话
        del self.upload_sessions[upload_id]
        self._save_sessions()
        
        return True


class S3StorageBackend(StorageBackend):
    """S3 兼容对象存储后端"""
    
    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
        prefix: str = ""
    ):
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError("boto3 is required for S3 storage backend. Install it with: pip install boto3")
        
        self.bucket = bucket
        self.prefix = prefix.rstrip('/') + '/' if prefix else ''
        
        # 初始化 S3 客户端
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region,
            config=Config(signature_version='s3v4')
        )
        
        # 确保 bucket 存在
        try:
            self.s3_client.head_bucket(Bucket=bucket)
        except Exception:
            self.s3_client.create_bucket(Bucket=bucket)
    
    def _get_s3_key(self, file_path: str) -> str:
        """获取 S3 对象 key"""
        return f"{self.prefix}{file_path.lstrip('/')}"
    
    def save_file(self, file_path: str, content: bytes, metadata: Optional[Dict] = None) -> str:
        """保存文件到 S3"""
        s3_key = self._get_s3_key(file_path)
        
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=content,
            **extra_args
        )
        
        return file_path
    
    def get_file(self, file_path: str) -> bytes:
        """从 S3 获取文件"""
        s3_key = self._get_s3_key(file_path)
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return response['Body'].read()
        except self.s3_client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def file_exists(self, file_path: str) -> bool:
        """检查 S3 文件是否存在"""
        s3_key = self._get_s3_key(file_path)
        
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception:
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """从 S3 删除文件"""
        s3_key = self._get_s3_key(file_path)
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception:
            return False
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取 S3 文件元数据"""
        s3_key = self._get_s3_key(file_path)
        
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
            return {
                "file_path": file_path,
                "file_size": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified', '').isoformat(),
                "etag": response.get('ETag', '').strip('"'),
                "content_type": response.get('ContentType', ''),
                "custom_metadata": response.get('Metadata', {})
            }
        except Exception as e:
            raise FileNotFoundError(f"File not found: {file_path}, error: {e}")
    
    def initiate_multipart_upload(self, file_name: str, metadata: Optional[Dict] = None) -> str:
        """初始化 S3 分片上传"""
        s3_key = self._get_s3_key(f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}/{file_name}")
        
        kwargs = {}
        if metadata:
            kwargs['Metadata'] = {k: str(v) for k, v in metadata.items()}
        
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket,
            Key=s3_key,
            **kwargs
        )
        
        return f"{response['UploadId']}:{s3_key}"
    
    def upload_chunk(self, upload_id: str, chunk_number: int, chunk_data: bytes) -> Dict[str, Any]:
        """上传单个分片到 S3"""
        upload_id_part, s3_key = upload_id.split(':', 1)
        
        response = self.s3_client.upload_part(
            Bucket=self.bucket,
            Key=s3_key,
            PartNumber=chunk_number,
            UploadId=upload_id_part,
            Body=chunk_data
        )
        
        return {
            "chunk_number": chunk_number,
            "etag": response['ETag'].strip('"'),
            "chunk_size": len(chunk_data)
        }
    
    def complete_multipart_upload(self, upload_id: str, chunks: List[Dict[str, Any]]) -> str:
        """完成 S3 分片上传"""
        upload_id_part, s3_key = upload_id.split(':', 1)
        
        # 按序号排序并格式化 parts
        parts_sorted = sorted(chunks, key=lambda x: x["chunk_number"])
        parts = [{'ETag': f'"{p["etag"]}"', 'PartNumber': p["chunk_number"]} for p in parts_sorted]
        
        self.s3_client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=s3_key,
            UploadId=upload_id_part,
            MultipartUpload={'Parts': parts}
        )
        
        # 返回去掉 prefix 的路径
        return s3_key[len(self.prefix):] if self.prefix else s3_key
    
    def abort_multipart_upload(self, upload_id: str) -> bool:
        """中止 S3 分片上传"""
        try:
            upload_id_part, s3_key = upload_id.split(':', 1)
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=s3_key,
                UploadId=upload_id_part
            )
            return True
        except Exception:
            return False


class StorageService:
    """存储服务 - 统一接口"""
    
    def __init__(self, backend: StorageBackend):
        self.backend = backend
    
    @classmethod
    def create_local(cls, base_path: str) -> 'StorageService':
        """创建本地存储服务"""
        backend = LocalStorageBackend(base_path)
        return cls(backend)
    
    @classmethod
    def create_s3(
        cls,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
        prefix: str = ""
    ) -> 'StorageService':
        """创建 S3 存储服务"""
        backend = S3StorageBackend(bucket, access_key, secret_key, endpoint_url, region, prefix)
        return cls(backend)
    
    # 代理方法到 backend
    def save_file(self, file_path: str, content: bytes, metadata: Optional[Dict] = None) -> str:
        return self.backend.save_file(file_path, content, metadata)
    
    def get_file(self, file_path: str) -> bytes:
        return self.backend.get_file(file_path)
    
    def file_exists(self, file_path: str) -> bool:
        return self.backend.file_exists(file_path)
    
    def delete_file(self, file_path: str) -> bool:
        return self.backend.delete_file(file_path)
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        return self.backend.get_file_metadata(file_path)
    
    def initiate_multipart_upload(self, file_name: str, metadata: Optional[Dict] = None) -> str:
        return self.backend.initiate_multipart_upload(file_name, metadata)
    
    def upload_chunk(self, upload_id: str, chunk_number: int, chunk_data: bytes) -> Dict[str, Any]:
        return self.backend.upload_chunk(upload_id, chunk_number, chunk_data)
    
    def complete_multipart_upload(self, upload_id: str, chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        return self.backend.complete_multipart_upload(upload_id, chunks)
    
    def abort_multipart_upload(self, upload_id: str) -> bool:
        return self.backend.abort_multipart_upload(upload_id)
    
    @staticmethod
    def calculate_file_hash(file_content: bytes, algorithm: str = 'md5') -> str:
        """计算文件哈希值"""
        if algorithm == 'md5':
            return hashlib.md5(file_content).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(file_content).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(file_content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def stream_file(self, file_path: str, chunk_size: int = 8192):
        """流式读取大文件"""
        content = self.get_file(file_path)
        buffer = io.BytesIO(content)
        
        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    def get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        metadata = self.get_file_metadata(file_path)
        return metadata.get('file_size', 0)
