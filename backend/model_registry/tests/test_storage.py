"""
Model Registry - 存储服务单元测试
"""
import pytest
import tempfile
import shutil
import os
import sys
import hashlib

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.storage import (
    StorageService,
    LocalStorageBackend,
)


@pytest.fixture
def temp_storage_path():
    """创建临时存储目录"""
    path = tempfile.mkdtemp(prefix="model_registry_test_")
    yield path
    # 清理
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def local_storage(temp_storage_path):
    """创建本地存储服务"""
    return StorageService.create_local(temp_storage_path)


class TestLocalStorageBackend:
    """本地存储后端测试"""
    
    def test_save_and_get_file(self, local_storage):
        """测试保存和获取文件"""
        file_content = b"Hello, Model Registry!"
        file_path = "test/file.txt"
        
        # 保存文件
        saved_path = local_storage.save_file(file_path, file_content)
        assert saved_path == file_path
        
        # 获取文件
        retrieved = local_storage.get_file(file_path)
        assert retrieved == file_content
    
    def test_file_exists(self, local_storage):
        """测试文件存在检查"""
        # 不存在的文件
        assert not local_storage.file_exists("nonexistent.txt")
        
        # 保存后应该存在
        local_storage.save_file("existent.txt", b"test")
        assert local_storage.file_exists("existent.txt")
    
    def test_delete_file(self, local_storage):
        """测试删除文件"""
        file_path = "to_delete.txt"
        local_storage.save_file(file_path, b"delete me")
        assert local_storage.file_exists(file_path)
        
        # 删除
        result = local_storage.delete_file(file_path)
        assert result is True
        assert not local_storage.file_exists(file_path)
        
        # 删除不存在的文件
        result = local_storage.delete_file("nonexistent.txt")
        assert result is False
    
    def test_get_file_metadata(self, local_storage):
        """测试获取文件元数据"""
        file_path = "metadata_test.txt"
        content = b"test content"
        metadata = {"key": "value", "version": "1.0"}
        
        local_storage.save_file(file_path, content, metadata)
        
        meta = local_storage.get_file_metadata(file_path)
        assert meta["file_size"] == len(content)
        assert "created_at" in meta
        assert "modified_at" in meta
        assert meta["custom_metadata"]["key"] == "value"
    
    def test_get_file_not_found(self, local_storage):
        """测试获取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            local_storage.get_file("nonexistent.txt")
    
    def test_calculate_file_hash(self, local_storage):
        """测试文件哈希计算"""
        content = b"test hash content"
        
        md5_hash = local_storage.calculate_file_hash(content, 'md5')
        assert len(md5_hash) == 32
        
        sha256_hash = local_storage.calculate_file_hash(content, 'sha256')
        assert len(sha256_hash) == 64
        
        # 验证正确性
        expected_md5 = hashlib.md5(content).hexdigest()
        assert md5_hash == expected_md5
    
    def test_stream_file(self, local_storage):
        """测试流式读取文件"""
        file_path = "stream_test.txt"
        content = b"a" * 10000  # 10KB
        
        local_storage.save_file(file_path, content)
        
        # 流式读取
        streamed_content = b""
        for chunk in local_storage.stream_file(file_path, chunk_size=1000):
            streamed_content += chunk
        
        assert streamed_content == content
    
    def test_get_file_size(self, local_storage):
        """测试获取文件大小"""
        file_path = "size_test.txt"
        content = b"test content" * 100
        
        local_storage.save_file(file_path, content)
        size = local_storage.get_file_size(file_path)
        
        assert size == len(content)


class TestMultipartUpload:
    """分片上传功能测试"""
    
    def test_initiate_upload(self, local_storage):
        """测试初始化上传"""
        upload_id = local_storage.initiate_multipart_upload(
            "large_model.bin",
            metadata={"model_type": "gpt", "size": "100MB"}
        )
        
        assert upload_id is not None
        assert len(upload_id) > 0
    
    def test_upload_chunk(self, local_storage):
        """测试上传分片"""
        upload_id = local_storage.initiate_multipart_upload("chunk_test.bin")
        
        # 上传第一个分片
        chunk1_data = b"chunk 1 data"
        chunk1_info = local_storage.upload_chunk(upload_id, 1, chunk1_data)
        
        assert chunk1_info["chunk_number"] == 1
        assert chunk1_info["chunk_size"] == len(chunk1_data)
        assert "chunk_hash" in chunk1_info
        
        # 上传第二个分片
        chunk2_data = b"chunk 2 data"
        chunk2_info = local_storage.upload_chunk(upload_id, 2, chunk2_data)
        
        assert chunk2_info["chunk_number"] == 2
    
    def test_upload_chunk_invalid_upload_id(self, local_storage):
        """测试上传分片时使用无效的 upload_id"""
        with pytest.raises(ValueError, match="Upload session not found"):
            local_storage.upload_chunk("invalid_upload_id", 1, b"data")
    
    def test_complete_multipart_upload(self, local_storage):
        """测试完成分片上传"""
        upload_id = local_storage.initiate_multipart_upload("complete_test.bin")
        
        # 上传多个分片
        chunks_data = [
            b"chunk 1: hello ",
            b"chunk 2: world",
            b"chunk 3: !"
        ]
        
        for i, data in enumerate(chunks_data, 1):
            local_storage.upload_chunk(upload_id, i, data)
        
        # 完成上传
        file_path = local_storage.complete_multipart_upload(upload_id)
        
        assert file_path is not None
        assert local_storage.file_exists(file_path)
        
        # 验证文件内容正确合并
        merged_content = local_storage.get_file(file_path)
        expected_content = b"".join(chunks_data)
        assert merged_content == expected_content
    
    def test_abort_multipart_upload(self, local_storage):
        """测试中止分片上传"""
        upload_id = local_storage.initiate_multipart_upload("abort_test.bin")
        
        # 上传一个分片
        local_storage.upload_chunk(upload_id, 1, b"some data")
        
        # 中止上传
        result = local_storage.abort_multipart_upload(upload_id)
        assert result is True
        
        # 再次中止应该返回 False
        result = local_storage.abort_multipart_upload(upload_id)
        assert result is False


class TestStorageEdgeCases:
    """边界情况测试"""
    
    def test_save_empty_file(self, local_storage):
        """测试保存空文件"""
        file_path = "empty.txt"
        saved_path = local_storage.save_file(file_path, b"")
        
        assert saved_path == file_path
        content = local_storage.get_file(file_path)
        assert content == b""
    
    def test_nested_directories(self, local_storage):
        """测试嵌套目录"""
        nested_path = "level1/level2/level3/file.txt"
        content = b"nested file"
        
        saved_path = local_storage.save_file(nested_path, content)
        assert saved_path == nested_path
        assert local_storage.get_file(nested_path) == content
    
    def test_special_characters_in_filename(self, local_storage):
        """测试文件名中的特殊字符"""
        test_cases = [
            "file with spaces.txt",
            "file_with_underscores.txt",
            "file-with-dashes.txt",
            "文件中文名称.txt",
            "file@special#chars.bin",
        ]
        
        for filename in test_cases:
            content = f"content for {filename}".encode()
            path = local_storage.save_file(filename, content)
            
            assert local_storage.file_exists(path)
            assert local_storage.get_file(path) == content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
