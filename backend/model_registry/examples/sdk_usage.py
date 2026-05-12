"""
Model Registry - Python SDK 使用示例

本示例演示如何使用 Model Registry 的完整功能：
1. 基本 CRUD 操作
2. 版本对比和回滚
3. 文件上传（简单上传 + 分片上传）
4. 版本历史管理
5. 统计信息查询
"""

import requests
import json
import os
from typing import Optional, Dict, Any, List


class ModelRegistryClient:
    """简化的 Model Registry 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1/model-versions"
    
    def create_version(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模型版本"""
        response = requests.post(self.api_base, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_version(self, version_id: str) -> Dict[str, Any]:
        """获取模型版本"""
        response = requests.get(f"{self.api_base}/{version_id}")
        response.raise_for_status()
        return response.json()
    
    def list_versions(self, **kwargs) -> Dict[str, Any]:
        """列出模型版本"""
        response = requests.get(self.api_base, params=kwargs)
        response.raise_for_status()
        return response.json()
    
    def update_version(self, version_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型版本"""
        response = requests.patch(f"{self.api_base}/{version_id}", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_version(self, version_id: str, hard_delete: bool = False) -> Dict[str, Any]:
        """删除模型版本"""
        response = requests.delete(
            f"{self.api_base}/{version_id}",
            params={"hard_delete": hard_delete}
        )
        response.raise_for_status()
        return response.json()
    
    def compare_versions(self, base_id: str, target_id: str) -> Dict[str, Any]:
        """对比两个版本"""
        response = requests.get(
            f"{self.api_base}/compare",
            params={"base_id": base_id, "target_id": target_id}
        )
        response.raise_for_status()
        return response.json()
    
    def rollback_version(self, version_id: str, target_id: str, 
                         reason: str = "", create_new: bool = True) -> Dict[str, Any]:
        """回滚版本"""
        response = requests.post(
            f"{self.api_base}/{version_id}/rollback",
            json={
                "target_version_id": target_id,
                "reason": reason,
                "create_new_version": create_new
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_version_history(self, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取版本历史"""
        response = requests.get(
            f"{self.api_base}/history/{name}",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_file(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """简单文件上传"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.api_base}/upload/simple",
                files={"file": (filename or os.path.basename(file_path), f)}
            )
        response.raise_for_status()
        return response.json()
    
    def upload_large_file(self, file_path: str, chunk_size: int = 5*1024*1024) -> Dict[str, Any]:
        """
        分片上传大文件
        
        Args:
            file_path: 本地文件路径
            chunk_size: 分片大小（默认 5MB）
        """
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # 1. 初始化上传
        init_response = requests.post(
            f"{self.api_base}/upload/init",
            json={
                "file_name": filename,
                "file_size": file_size,
                "chunk_size": chunk_size,
                "metadata": {"upload_method": "chunked"}
            }
        )
        init_response.raise_for_status()
        upload_id = init_response.json()["upload_id"]
        print(f"✓ 初始化上传，upload_id: {upload_id}")
        
        # 2. 分片上传
        chunks_info = []
        chunk_number = 1
        
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                
                chunk_response = requests.post(
                    f"{self.api_base}/upload/chunk",
                    data={"upload_id": upload_id, "chunk_number": chunk_number},
                    files={"chunk_file": (f"chunk_{chunk_number}", chunk_data)}
                )
                chunk_response.raise_for_status()
                
                print(f"✓ 已上传分片 {chunk_number}, 大小: {len(chunk_data)} bytes")
                chunks_info.append({"chunk_number": chunk_number})
                chunk_number += 1
        
        # 3. 完成上传
        complete_response = requests.post(
            f"{self.api_base}/upload/complete",
            json={"upload_id": upload_id, "chunks": chunks_info}
        )
        complete_response.raise_for_status()
        
        print(f"✓ 文件上传完成: {complete_response.json()['file_path']}")
        return complete_response.json()
    
    def get_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        response = requests.get(
            f"{self.api_base}/statistics/summary",
            params={"project_id": project_id}
        )
        response.raise_for_status()
        return response.json()


def main():
    """主函数 - 演示各种功能"""
    print("=" * 60)
    print("  Model Registry 使用示例")
    print("=" * 60)
    print()
    
    # 初始化客户端
    client = ModelRegistryClient("http://localhost:8000")
    
    # 示例 1: 创建模型版本
    print("📦 示例 1: 创建模型版本")
    version_data = {
        "name": "my-assistant-model",
        "version": "1.0.0",
        "description": "我的第一个 AI 助手模型",
        "status": "draft",
        "tags": ["production", "gpt-4", "customer-support"],
        "weights_config": {
            "model_type": "gpt4",
            "provider": "openai",
            "model_id": "gpt-4-turbo-preview",
            "parameters": {"temperature": 0.7, "max_tokens": 2048}
        },
        "prompt_config": {
            "system_prompt": "你是一个专业的客户服务助手",
            "variables": ["user_query", "customer_id"]
        },
        "rag_config": {
            "enabled": True,
            "knowledge_base_id": "kb_customer_support",
            "top_k": 5,
            "score_threshold": 0.8
        },
        "guardrails_config": {
            "toxicity_filter_enabled": True,
            "toxicity_threshold": 0.7,
            "sensitive_words_enabled": True
        },
        "inference_params": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        "evaluation_metrics": {
            "hallucination_rate": 0.05,
            "toxicity_score": 0.01,
            "faithfulness": 0.95,
            "avg_latency_ms": 420
        }
    }
    
    v1 = client.create_version(version_data)
    print(f"✓ 版本创建成功: {v1['name']} v{v1['version']}")
    print(f"  版本 ID: {v1['id']}")
    print()
    
    # 示例 2: 创建第二个版本（修改一些配置）
    print("📦 示例 2: 创建第二个版本")
    v2_data = version_data.copy()
    v2_data["version"] = "1.1.0"
    v2_data["description"] = "优化 Prompt，提升回答质量"
    v2_data["inference_params"]["temperature"] = 0.6
    v2_data["inference_params"]["max_tokens"] = 4096
    v2_data["evaluation_metrics"]["hallucination_rate"] = 0.03
    v2_data["tags"].append("optimized")
    
    v2 = client.create_version(v2_data)
    print(f"✓ 版本创建成功: {v2['name']} v{v2['version']}")
    print()
    
    # 示例 3: 对比两个版本
    print("🔍 示例 3: 对比两个版本")
    diff = client.compare_versions(v1["id"], v2["id"])
    print(f"✓ 版本对比完成")
    print(f"  变更字段数: {len(diff['changed_fields'])}")
    if diff["evaluation_changes"]:
        print(f"  评估指标变化: {list(diff['evaluation_changes'].keys())}")
    print()
    
    # 示例 4: 列出所有版本
    print("📋 示例 4: 列出所有版本")
    versions = client.list_versions(status="draft", limit=10)
    print(f"✓ 共有 {versions['pagination']['total']} 个版本")
    for v in versions["data"][:3]:  # 只显示前 3 个
        print(f"  - {v['name']} v{v['version']} ({v['status']})")
    print()
    
    # 示例 5: 获取版本历史
    print("📜 示例 5: 获取版本历史")
    history = client.get_version_history("my-assistant-model", limit=5)
    print(f"✓ 历史版本数: {len(history)}")
    for h in history:
        print(f"  - {h['version']} (创建时间: {h['created_at'][:19]})")
    print()
    
    # 示例 6: 回滚版本
    print("⏪ 示例 6: 回滚版本")
    rollback_result = client.rollback_version(
        version_id=v2["id"],
        target_id=v1["id"],
        reason="新版本延迟较高，暂时回滚",
        create_new=True
    )
    print(f"✓ 回滚成功，新版本号: {rollback_result['version']}")
    print(f"  新版本 ID: {rollback_result['id']}")
    print()
    
    # 示例 7: 获取统计信息
    print("📊 示例 7: 获取统计信息")
    stats = client.get_statistics()
    print(f"✓ 统计信息获取成功:")
    print(f"  - 总版本数: {stats['data']['total_versions']}")
    print(f"  - 唯一模型数: {stats['data']['unique_models']}")
    print(f"  - 版本状态分布: {stats['data']['status_distribution']}")
    print()
    
    # 示例 8: 简单文件上传
    print("💾 示例 8: 简单文件上传")
    temp_file = "/tmp/test_weights.bin"
    with open(temp_file, 'wb') as f:
        f.write(b"mock model weights content" * 1000)
    
    upload_result = client.upload_file(temp_file, "model_v1_weights.bin")
    print(f"✓ 文件上传成功: {upload_result['file_path']}")
    print(f"  文件大小: {upload_result['file_size']} bytes")
    os.unlink(temp_file)
    print()
    
    # 示例 9: 分片上传大文件
    print("📁 示例 9: 分片上传大文件")
    large_file = "/tmp/large_weights.bin"
    with open(large_file, 'wb') as f:
        # 创建一个 15MB 的测试文件
        f.write(b"0" * (15 * 1024 * 1024))
    
    large_upload_result = client.upload_large_file(large_file, chunk_size=5*1024*1024)
    print(f"✓ 大文件上传成功: {large_upload_result['file_path']}")
    print(f"  文件大小: {large_upload_result['file_size']} bytes")
    os.unlink(large_file)
    print()
    
    # 示例 10: 更新版本状态
    print("✅ 示例 10: 发布版本到生产环境")
    updated = client.update_version(v2["id"], {
        "status": "production",
        "description": "已通过 QA 测试，正式发布到生产环境"
    })
    print(f"✓ 版本状态更新: {updated['status']}")
    print(f"  描述: {updated['description']}")
    print()
    
    print("=" * 60)
    print("  所有示例执行完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到 Model Registry 服务")
        print("   请确保服务已启动: python -m model_registry.main")
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
