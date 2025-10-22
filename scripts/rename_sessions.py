#!/usr/bin/env python3
"""
Session文件重命名脚本

将test_sessions目录中的session文件按照以下规则重命名：
workflow名称(全小写)+年月日(如251022)+时分秒+现有命名规则的前6位

例如：react-251022-174800-1f73e8
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional


def extract_workflow_name(session_data: Dict) -> str:
    """从session数据中提取workflow名称并转换为小写"""
    workflow_name = session_data.get("workflow_config", {}).get("name", "")
    # 转换为小写并移除下划线和后缀，保持简洁
    # 例如: "react_workflow" -> "react"
    base_name = workflow_name.lower().replace("_", "")
    # 移除常见的后缀如"workflow"
    if base_name.endswith("workflow"):
        base_name = base_name[:-8]  # 移除"workflow"(8个字符)
    return base_name


def extract_datetime(session_data: Dict) -> Tuple[str, str]:
    """从session数据中提取创建时间并格式化为年月日和时分秒"""
    created_at = session_data.get("metadata", {}).get("created_at", "")
    if not created_at:
        return "", ""
    
    try:
        # 解析ISO格式时间字符串
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        # 格式化为年月日(如251022)和时分秒(如174800)
        date_str = dt.strftime("%y%m%d")
        time_str = dt.strftime("%H%M%S")
        return date_str, time_str
    except (ValueError, TypeError):
        return "", ""


def extract_uuid_prefix(filename: str) -> str:
    """从文件名中提取UUID的前6位"""
    # 移除.json扩展名
    uuid = filename.replace(".json", "")
    return uuid[:6]


def generate_new_filename(session_data: Dict, old_filename: str) -> Optional[str]:
    """根据session数据生成新的文件名"""
    workflow_name = extract_workflow_name(session_data)
    date_str, time_str = extract_datetime(session_data)
    uuid_prefix = extract_uuid_prefix(old_filename)
    
    # 检查必要信息是否完整
    if not workflow_name or not date_str or not time_str or not uuid_prefix:
        print(f"警告: 无法从 {old_filename} 提取完整信息")
        print(f"  workflow_name: {workflow_name}")
        print(f"  date_str: {date_str}")
        print(f"  time_str: {time_str}")
        print(f"  uuid_prefix: {uuid_prefix}")
        return None
    
    # 生成新文件名: workflow-年月日-时分秒-uuid前6位
    new_filename = f"{workflow_name}-{date_str}-{time_str}-{uuid_prefix}.json"
    return new_filename


def load_session_data(filepath: Path) -> Optional[Dict]:
    """加载session文件数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"错误: 无法读取文件 {filepath}: {e}")
        return None


def rename_session_file(session_dir: Path, dry_run: bool = True) -> None:
    """重命名session目录中的所有文件"""
    if not session_dir.exists():
        print(f"错误: 目录 {session_dir} 不存在")
        return
    
    json_files = list(session_dir.glob("*.json"))
    if not json_files:
        print(f"在目录 {session_dir} 中没有找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个session文件")
    
    rename_count = 0
    error_count = 0
    
    for old_filepath in json_files:
        session_data = load_session_data(old_filepath)
        if not session_data:
            error_count += 1
            continue
        
        new_filename = generate_new_filename(session_data, old_filepath.name)
        if not new_filename:
            error_count += 1
            continue
        
        new_filepath = session_dir / new_filename
        
        # 检查目标文件是否已存在
        if new_filepath.exists():
            print(f"警告: 目标文件 {new_filename} 已存在，跳过重命名 {old_filepath.name}")
            error_count += 1
            continue
        
        print(f"{'[预览] ' if dry_run else ''}{old_filepath.name} -> {new_filename}")
        
        if not dry_run:
            try:
                old_filepath.rename(new_filepath)
                rename_count += 1
            except OSError as e:
                print(f"错误: 无法重命名 {old_filepath.name}: {e}")
                error_count += 1
        else:
            rename_count += 1
    
    print(f"\n{'预览结果' if dry_run else '重命名结果'}:")
    print(f"  成功: {rename_count}")
    print(f"  错误: {error_count}")
    print(f"  总计: {len(json_files)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="重命名session文件")
    parser.add_argument(
        "--session-dir",
        default="test_sessions",
        help="session文件目录路径 (默认: test_sessions)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行重命名操作 (默认只预览)"
    )
    
    args = parser.parse_args()
    
    session_dir = Path(args.session_dir)
    
    if args.execute:
        print("执行重命名操作...\n")
        rename_session_file(session_dir, dry_run=False)
    else:
        print("预览重命名操作 (使用 --execute 执行实际重命名)...\n")
        rename_session_file(session_dir, dry_run=True)


if __name__ == "__main__":
    main()