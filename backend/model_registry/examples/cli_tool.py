#!/usr/bin/env python3
"""
Model Registry - 命令行工具示例

提供命令行接口来管理模型版本：
- 列出模型版本
- 创建/查看/更新/删除版本
- 对比版本
- 上传/下载文件

使用方法:
    python cli_tool.py list
    python cli_tool.py create --name my-model --version 1.0.0
    python cli_tool.py get <version-id>
    python cli_tool.py compare <base-id> <target-id>
    python cli_tool.py upload <file-path>
"""

import argparse
import json
import sys
import os
from typing import Optional

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import DatabaseService
from services.storage import StorageService
from models.schemas import (
    ModelVersionCreate,
    ModelVersionUpdate,
    VersionStatus,
)


class ModelRegistryCLI:
    """命令行接口类"""
    
    def __init__(self, db_url: str = None, storage_path: str = None):
        self.db = DatabaseService(db_url or "sqlite:///./model_registry.db")
        self.storage = StorageService.create_local(
            storage_path or "./model_registry_files"
        )
    
    def cmd_list(self, args):
        """列出模型版本"""
        versions, total = self.db.list_model_versions(
            status=args.status,
            skip=args.skip,
            limit=args.limit,
            sort_by=args.sort_by,
            sort_order=args.sort_order
        )
        
        print(f"\n📦 共 {total} 个模型版本\n")
        print(f"{'ID':<40} {'名称':<20} {'版本':<12} {'状态':<12} {'创建时间'}")
        print("-" * 110)
        
        for v in versions:
            created = v.created_at.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{v.id:<40} {v.name:<20} v{v.version:<10} {v.status.value:<12} {created}")
        
        print()
    
    def cmd_get(self, args):
        """查看单个版本详情"""
        version = self.db.get_model_version(args.version_id)
        if not version:
            print(f"❌ 版本不存在: {args.version_id}")
            return
        
        print(f"\n📋 模型版本详情\n")
        print(f"  ID:         {version.id}")
        print(f"  名称:       {version.name}")
        print(f"  版本号:     v{version.version}")
        print(f"  状态:       {version.status.value}")
        print(f"  描述:       {version.description or 'N/A'}")
        print(f"  标签:       {', '.join(version.tags) if version.tags else 'N/A'}")
        print(f"  创建时间:   {version.created_at}")
        print(f"  更新时间:   {version.updated_at}")
        
        if version.weights_config:
            print(f"\n  权重配置:")
            print(f"    模型类型: {version.weights_config.model_type}")
            print(f"    提供商:   {version.weights_config.provider}")
            print(f"    模型 ID:  {version.weights_config.model_id}")
        
        if version.evaluation_metrics:
            m = version.evaluation_metrics
            print(f"\n  评估指标:")
            print(f"    幻觉率:   {m.hallucination_rate:.2%}" if m.hallucination_rate else "")
            print(f"    毒性分:   {m.toxicity_score:.2f}" if m.toxicity_score else "")
            print(f"    忠实度:   {m.faithfulness:.2%}" if m.faithfulness else "")
            print(f"    延迟(ms): {m.avg_latency_ms}" if m.avg_latency_ms else "")
        
        print()
    
    def cmd_create(self, args):
        """创建新版本"""
        try:
            # 从 JSON 文件读取或使用命令行参数
            if args.from_json:
                with open(args.from_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                model_data = ModelVersionCreate(**data)
            else:
                model_data = ModelVersionCreate(
                    name=args.name,
                    version=args.version,
                    description=args.description,
                    status=VersionStatus(args.status) if args.status else VersionStatus.DRAFT,
                    tags=args.tags.split(',') if args.tags else [],
                )
            
            result = self.db.create_model_version(model_data)
            print(f"✅ 模型版本创建成功!")
            print(f"   ID:      {result.id}")
            print(f"   名称:    {result.name}")
            print(f"   版本:    v{result.version}")
            print(f"   状态:    {result.status.value}")
            print()
        
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            sys.exit(1)
    
    def cmd_update(self, args):
        """更新版本"""
        update_data = {}
        
        if args.description is not None:
            update_data["description"] = args.description
        if args.status is not None:
            update_data["status"] = args.status
        if args.tags is not None:
            update_data["tags"] = args.tags.split(',')
        
        if not update_data:
            print("❌ 请指定要更新的字段 (--description, --status, --tags)")
            sys.exit(1)
        
        try:
            data = ModelVersionUpdate(**update_data)
            result = self.db.update_model_version(args.version_id, data)
            
            if not result:
                print(f"❌ 版本不存在: {args.version_id}")
                sys.exit(1)
            
            print(f"✅ 版本更新成功!")
            print(f"   ID:      {result.id}")
            print(f"   状态:    {result.status.value}")
            print()
        
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            sys.exit(1)
    
    def cmd_delete(self, args):
        """删除版本"""
        try:
            if args.hard:
                success = self.db.hard_delete_model_version(args.version_id)
            else:
                success = self.db.delete_model_version(args.version_id)
            
            if not success:
                print(f"❌ 版本不存在: {args.version_id}")
                sys.exit(1)
            
            print(f"✅ 版本{'硬' if args.hard else ''}删除成功!")
            print()
        
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            sys.exit(1)
    
    def cmd_compare(self, args):
        """对比两个版本"""
        diff = self.db.compare_versions(args.base_id, args.target_id)
        if not diff:
            print("❌ 一个或两个版本不存在")
            sys.exit(1)
        
        print(f"\n🔍 版本对比\n")
        print(f"  基准版本: v{diff.base_version} ({diff.base_version_id})")
        print(f"  目标版本: v{diff.target_version} ({diff.target_version_id})")
        print(f"\n  变更字段 ({len(diff.changed_fields)} 个):")
        for field, changes in diff.changed_fields.items():
            if isinstance(changes, dict):
                old_val = changes.get('old', 'N/A')
                new_val = changes.get('new', 'N/A')
                change_type = changes.get('change_type', 'modified')
                icon = {'added': '+', 'removed': '-', 'modified': '~'}.get(change_type, '~')
                print(f"    {icon} {field}:")
                print(f"        - 旧值: {old_val}")
                print(f"        + 新值: {new_val}")
            else:
                print(f"    ~ {field}: {changes}")
        
        if diff.evaluation_changes:
            print(f"\n  评估指标变化:")
            for metric, change in diff.evaluation_changes.items():
                print(f"    - {metric}: {change}")
        
        print()
    
    def cmd_rollback(self, args):
        """回滚版本"""
        from models.schemas import RollbackRequest
        
        try:
            request = RollbackRequest(
                target_version_id=args.target_id,
                reason=args.reason,
                create_new_version=not args.inplace
            )
            
            result = self.db.rollback_to_version(args.version_id, request)
            if not result:
                print(f"❌ 回滚失败")
                sys.exit(1)
            
            print(f"✅ 回滚成功!")
            print(f"   新/当前版本: v{result.version}")
            print(f"   ID: {result.id}")
            print()
        
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            sys.exit(1)
    
    def cmd_stats(self, args):
        """查看统计信息"""
        stats = self.db.get_statistics()
        
        print(f"\n📊 模型注册表统计\n")
        print(f"  总版本数:   {stats['total_versions']}")
        print(f"  唯一模型数: {stats['unique_models']}")
        
        print(f"\n  状态分布:")
        for status, count in stats['status_distribution'].items():
            print(f"    - {status}: {count}")
        
        print(f"\n  最近版本:")
        for v in stats['recent_versions'][:5]:
            print(f"    - {v['name']} v{v['version']}")
        
        print()
    
    def cmd_upload(self, args):
        """上传文件"""
        if not os.path.exists(args.file_path):
            print(f"❌ 文件不存在: {args.file_path}")
            sys.exit(1)
        
        file_size = os.path.getsize(args.file_path)
        filename = args.filename or os.path.basename(args.file_path)
        
        if file_size > 50 * 1024 * 1024:  # >50MB 使用分片上传
            print(f"📁 使用分片上传 (文件大小: {file_size / 1024 / 1024:.1f} MB)")
            result = self._upload_large_file(args.file_path, filename)
        else:
            print(f"💾 使用简单上传 (文件大小: {file_size / 1024:.1f} KB)")
            with open(args.file_path, 'rb') as f:
                content = f.read()
            result = self.storage.save_file(filename, content)
        
        print(f"✅ 上传成功!")
        print(f"   存储路径: {result if isinstance(result, str) else result['file_path']}")
        print()
    
    def _upload_large_file(self, file_path: str, filename: str) -> dict:
        """分片上传大文件"""
        chunk_size = 5 * 1024 * 1024  # 5MB
        file_size = os.path.getsize(file_path)
        
        upload_id = self.storage.initiate_multipart_upload(filename)
        chunks_info = []
        chunk_number = 1
        
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                
                chunk_info = self.storage.upload_chunk(upload_id, chunk_number, chunk_data)
                chunks_info.append(chunk_info)
                print(f"   ✓ 已上传分片 {chunk_number}/{(file_size + chunk_size -1) // chunk_size}")
                chunk_number += 1
        
        final_path = self.storage.complete_multipart_upload(upload_id, chunks_info)
        return {"file_path": final_path}
    
    def cmd_download(self, args):
        """下载文件"""
        if not self.storage.file_exists(args.remote_path):
            print(f"❌ 文件不存在: {args.remote_path}")
            sys.exit(1)
        
        content = self.storage.get_file(args.remote_path)
        local_path = args.local_path or os.path.basename(args.remote_path)
        
        with open(local_path, 'wb') as f:
            f.write(content)
        
        print(f"✅ 下载成功!")
        print(f"   本地路径: {local_path}")
        print(f"   文件大小: {len(content)} bytes")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Model Registry 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s list                             列出所有版本
  %(prog)s create --name my-model --version 1.0.0  创建新版本
  %(prog)s get <version-id>                 查看版本详情
  %(prog)s update <version-id> --status production  更新版本
  %(prog)s delete <version-id>              删除版本
  %(prog)s compare <base-id> <target-id>    对比两个版本
  %(prog)s rollback <version-id> <target-id> 回滚版本
  %(prog)s upload <local-file>              上传文件
  %(prog)s download <remote-path> <local-path> 下载文件
  %(prog)s stats                            查看统计信息
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出模型版本")
    list_parser.add_argument("--status", choices=[s.value for s in VersionStatus], help="按状态过滤")
    list_parser.add_argument("--skip", type=int, default=0, help="跳过数量")
    list_parser.add_argument("--limit", type=int, default=50, help="返回数量")
    list_parser.add_argument("--sort-by", default="created_at", help="排序字段")
    list_parser.add_argument("--sort-order", default="desc", choices=["asc", "desc"], help="排序方向")
    
    # get 命令
    get_parser = subparsers.add_parser("get", help="查看版本详情")
    get_parser.add_argument("version_id", help="版本 ID")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建新版本")
    create_parser.add_argument("--name", required=False, help="模型名称")
    create_parser.add_argument("--version", required=False, help="版本号")
    create_parser.add_argument("--description", help="版本描述")
    create_parser.add_argument("--status", choices=[s.value for s in VersionStatus], help="版本状态")
    create_parser.add_argument("--tags", help="标签（逗号分隔）")
    create_parser.add_argument("--from-json", help="从 JSON 文件读取配置")
    
    # update 命令
    update_parser = subparsers.add_parser("update", help="更新版本")
    update_parser.add_argument("version_id", help="版本 ID")
    update_parser.add_argument("--description", help="更新描述")
    update_parser.add_argument("--status", choices=[s.value for s in VersionStatus], help="更新状态")
    update_parser.add_argument("--tags", help="更新标签（逗号分隔）")
    
    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除版本")
    delete_parser.add_argument("version_id", help="版本 ID")
    delete_parser.add_argument("--hard", action="store_true", help="硬删除（彻底从数据库删除）")
    
    # compare 命令
    compare_parser = subparsers.add_parser("compare", help="对比两个版本")
    compare_parser.add_argument("base_id", help="基准版本 ID")
    compare_parser.add_argument("target_id", help="目标版本 ID")
    
    # rollback 命令
    rollback_parser = subparsers.add_parser("rollback", help="回滚版本")
    rollback_parser.add_argument("version_id", help="当前版本 ID")
    rollback_parser.add_argument("target_id", help="目标版本 ID")
    rollback_parser.add_argument("--reason", default="", help="回滚原因")
    rollback_parser.add_argument("--inplace", action="store_true", help="原地更新（不创建新版本）")
    
    # stats 命令
    subparsers.add_parser("stats", help="查看统计信息")
    
    # upload 命令
    upload_parser = subparsers.add_parser("upload", help="上传文件")
    upload_parser.add_argument("file_path", help="本地文件路径")
    upload_parser.add_argument("--filename", help="远程文件名（可选）")
    
    # download 命令
    download_parser = subparsers.add_parser("download", help="下载文件")
    download_parser.add_argument("remote_path", help="远程文件路径")
    download_parser.add_argument("local_path", nargs="?", help="本地保存路径（可选）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ModelRegistryCLI()
    
    # 执行命令
    command_map = {
        "list": cli.cmd_list,
        "get": cli.cmd_get,
        "create": cli.cmd_create,
        "update": cli.cmd_update,
        "delete": cli.cmd_delete,
        "compare": cli.cmd_compare,
        "rollback": cli.cmd_rollback,
        "stats": cli.cmd_stats,
        "upload": cli.cmd_upload,
        "download": cli.cmd_download,
    }
    
    if args.command in command_map:
        command_map[args.command](args)
    else:
        print(f"❌ 未知命令: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
