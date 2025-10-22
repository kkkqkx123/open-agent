"""Git管理器模块

提供会话的Git版本控制功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import json
from datetime import datetime


class IGitManager(ABC):
    """Git管理器接口"""

    @abstractmethod
    def init_repo(self, repo_path: Path) -> bool:
        """初始化Git仓库

        Args:
            repo_path: 仓库路径

        Returns:
            bool: 是否成功初始化
        """
        pass

    @abstractmethod
    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """提交更改

        Args:
            repo_path: 仓库路径
            message: 提交消息
            metadata: 提交元数据

        Returns:
            bool: 是否成功提交
        """
        pass

    @abstractmethod
    def get_commit_history(self, repo_path: Path) -> List[Dict[str, Any]]:
        """获取提交历史

        Args:
            repo_path: 仓库路径

        Returns:
            List[Dict[str, Any]]: 提交历史列表
        """
        pass

    @abstractmethod
    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支

        Args:
            repo_path: 仓库路径
            branch_name: 分支名称

        Returns:
            bool: 是否成功创建
        """
        pass

    @abstractmethod
    def switch_branch(self, repo_path: Path, branch_name: str) -> bool:
        """切换分支

        Args:
            repo_path: 仓库路径
            branch_name: 分支名称

        Returns:
            bool: 是否成功切换
        """
        pass

    @abstractmethod
    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """合并分支

        Args:
            repo_path: 仓库路径
            source_branch: 源分支
            target_branch: 目标分支

        Returns:
            bool: 是否成功合并
        """
        pass


class GitManager(IGitManager):
    """Git管理器实现"""

    def __init__(self, git_executable: str = "git") -> None:
        """初始化Git管理器

        Args:
            git_executable: Git可执行文件路径
        """
        self.git_executable = git_executable

    def _run_git_command(self, repo_path: Path, args: List[str]) -> subprocess.CompletedProcess:
        """运行Git命令

        Args:
            repo_path: 仓库路径
            args: 命令参数

        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        cmd = [self.git_executable] + args
        return subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

    def init_repo(self, repo_path: Path) -> bool:
        """初始化Git仓库"""
        try:
            # 确保目录存在
            repo_path.mkdir(parents=True, exist_ok=True)

            # 初始化仓库
            result = self._run_git_command(repo_path, ["init"])
            if result.returncode != 0:
                return False

            # 配置用户信息（如果未配置）
            self._configure_user_if_needed(repo_path)

            # 创建.gitignore文件
            self._create_gitignore(repo_path)

            # 初始提交
            return self.commit_changes(repo_path, "初始化会话仓库")
        except Exception:
            return False

    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """提交更改"""
        try:
            # 添加所有更改
            result = self._run_git_command(repo_path, ["add", "."])
            if result.returncode != 0:
                return False

            # 检查是否有更改需要提交
            result = self._run_git_command(repo_path, ["status", "--porcelain"])
            if result.returncode != 0:
                return False

            if not result.stdout.strip():
                # 没有更改需要提交
                return True

            # 提交更改
            commit_args = ["commit", "-m", message]
            if metadata:
                # 将元数据添加到提交消息中
                metadata_str = json.dumps(metadata, ensure_ascii=False)
                commit_args = ["commit", "-m", f"{message}\n\n元数据: {metadata_str}"]

            result = self._run_git_command(repo_path, commit_args)
            return result.returncode == 0
        except Exception:
            return False

    def get_commit_history(self, repo_path: Path) -> List[Dict[str, Any]]:
        """获取提交历史"""
        try:
            # 获取提交日志
            result = self._run_git_command(repo_path, [
                "log",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=iso",
                "--no-pager"
            ])

            if result.returncode != 0:
                return []

            commits = []
            lines = result.stdout.strip().split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                if not line:
                    i += 1
                    continue

                parts = line.split("|", 3)
                if len(parts) < 4:
                    i += 1
                    continue

                commit_hash, author, date, message = parts[:4]

                # 尝试解析元数据（可能在下一行或下下行）
                metadata = {}
                # 检查下一行是否是空行，再下一行是否是元数据
                next_index = i + 1
                if next_index < len(lines):
                    if lines[next_index].strip() == "" and next_index + 1 < len(lines) and lines[next_index + 1].startswith("元数据: "):
                        # 跳过空行，处理元数据行
                        try:
                            metadata_str = lines[next_index + 1][len("元数据: "):]
                            metadata = json.loads(metadata_str)
                            i += 2  # 跳过空行和元数据行
                        except json.JSONDecodeError:
                            i += 1  # 只跳过空行
                    elif lines[next_index].startswith("元数据: "):
                        # 下一行直接是元数据
                        try:
                            metadata_str = lines[next_index][len("元数据: "):]
                            metadata = json.loads(metadata_str)
                            i += 1  # 跳过元数据行
                        except json.JSONDecodeError:
                            pass
                elif "\n\n元数据: " in message:
                    # 处理在同一行的情况（向后兼容）
                    message_parts = message.split("\n\n元数据: ", 1)
                    message = message_parts[0]
                    try:
                        metadata = json.loads(message_parts[1])
                    except json.JSONDecodeError:
                        pass

                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "timestamp": date,
                    "message": message,
                    "metadata": metadata
                })
                i += 1

            return commits
        except Exception:
            return []

    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支"""
        try:
            result = self._run_git_command(repo_path, ["checkout", "-b", branch_name])
            return result.returncode == 0
        except Exception:
            return False

    def switch_branch(self, repo_path: Path, branch_name: str) -> bool:
        """切换分支"""
        try:
            result = self._run_git_command(repo_path, ["checkout", branch_name])
            return result.returncode == 0
        except Exception:
            return False

    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """合并分支"""
        try:
            # 切换到目标分支
            if not self.switch_branch(repo_path, target_branch):
                return False

            # 合并源分支
            result = self._run_git_command(repo_path, ["merge", source_branch])
            return result.returncode == 0
        except Exception:
            return False

    def _configure_user_if_needed(self, repo_path: Path) -> None:
        """如果需要，配置Git用户信息"""
        try:
            # 检查是否已配置用户名
            result = self._run_git_command(repo_path, ["config", "user.name"])
            if result.returncode != 0 or not result.stdout.strip():
                self._run_git_command(repo_path, ["config", "user.name", "Session Manager"])

            # 检查是否已配置邮箱
            result = self._run_git_command(repo_path, ["config", "user.email"])
            if result.returncode != 0 or not result.stdout.strip():
                self._run_git_command(repo_path, ["config", "user.email", "session@example.com"])
        except Exception:
            pass

    def _create_gitignore(self, repo_path: Path) -> None:
        """创建.gitignore文件"""
        gitignore_path = repo_path / ".gitignore"
        if not gitignore_path.exists():
            try:
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write("""# 会话临时文件
*.tmp
*.temp

# 系统文件
.DS_Store
Thumbs.db

# IDE文件
.vscode/
.idea/
""")
            except Exception:
                pass


class MockGitManager(IGitManager):
    """模拟Git管理器（用于测试）"""

    def __init__(self) -> None:
        """初始化模拟Git管理器"""
        self._repos: Dict[str, List[Dict[str, Any]]] = {}

    def init_repo(self, repo_path: Path) -> bool:
        """初始化Git仓库"""
        repo_key = str(repo_path)
        self._repos[repo_key] = []
        return True

    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """提交更改"""
        repo_key = str(repo_path)
        if repo_key not in self._repos:
            return False

        self._repos[repo_key].append({
            "hash": f"mock_{len(self._repos[repo_key])}",
            "author": "Mock User",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "metadata": metadata or {}
        })
        return True

    def get_commit_history(self, repo_path: Path) -> List[Dict[str, Any]]:
        """获取提交历史"""
        repo_key = str(repo_path)
        return self._repos.get(repo_key, [])

    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支"""
        return True

    def switch_branch(self, repo_path: Path, branch_name: str) -> bool:
        """切换分支"""
        return True

    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """合并分支"""
        return True


def create_git_manager(use_mock: bool = False, git_executable: str = "git") -> IGitManager:
    """创建Git管理器实例

    Args:
        use_mock: 是否使用模拟管理器
        git_executable: Git可执行文件路径

    Returns:
        IGitManager: Git管理器实例
    """
    if use_mock:
        return MockGitManager()
    else:
        return GitManager(git_executable)