"""Git服务实现 - 用于会话版本控制"""

from src.interfaces.dependency_injection import get_logger
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = get_logger(__name__)


class IGitService(ABC):
    """Git服务接口"""
    
    @abstractmethod
    def init_repo(self, repo_path: Path) -> bool:
        """初始化Git仓库"""
    
    @abstractmethod
    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """提交更改"""
    
    @abstractmethod
    def get_commit_history(self, repo_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取提交历史"""
    
    @abstractmethod
    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支"""
    
    @abstractmethod
    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """合并分支"""


class GitService(IGitService):
    """Git服务实现"""
    
    def __init__(self, git_command: str = "git"):
        """初始化Git服务
        
        Args:
            git_command: Git命令路径
        """
        self._git_command = git_command
        logger.info("GitService初始化完成")
    
    def init_repo(self, repo_path: Path) -> bool:
        """初始化Git仓库"""
        try:
            # 确保目录存在
            repo_path.mkdir(parents=True, exist_ok=True)
            
            # 初始化Git仓库
            result = subprocess.run(
                [self._git_command, "init"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 配置用户信息（如果需要）
            subprocess.run(
                [self._git_command, "config", "user.name", "Session Manager"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            subprocess.run(
                [self._git_command, "config", "user.email", "session@system.local"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 创建初始提交
            readme_content = f"# Session Repository\n\nSession ID: {repo_path.name}\nCreated at: {datetime.now().isoformat()}\n"
            readme_path = repo_path / "README.md"
            readme_path.write_text(readme_content)
            
            subprocess.run(
                [self._git_command, "add", "README.md"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            subprocess.run(
                [self._git_command, "commit", "-m", "Initial commit"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Git仓库初始化成功: {repo_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git仓库初始化失败: {repo_path}, error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Git仓库初始化异常: {repo_path}, error: {e}")
            return False
    
    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """提交更改"""
        try:
            # 添加所有更改
            subprocess.run(
                [self._git_command, "add", "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 构建提交消息
            commit_message = message
            if metadata:
                metadata_str = ", ".join([f"{k}={v}" for k, v in metadata.items()])
                commit_message = f"{message}\n\nMetadata: {metadata_str}"
            
            # 提交更改
            result = subprocess.run(
                [self._git_command, "commit", "-m", commit_message],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 获取提交哈希
            hash_result = subprocess.run(
                [self._git_command, "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hash = hash_result.stdout.strip()
            logger.info(f"Git提交成功: {repo_path}, hash: {commit_hash}")
            return commit_hash
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git提交失败: {repo_path}, error: {e.stderr}")
            return ""
        except Exception as e:
            logger.error(f"Git提交异常: {repo_path}, error: {e}")
            return ""
    
    def get_commit_history(self, repo_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取提交历史"""
        try:
            # 构建git log命令
            cmd = [
                self._git_command, "log",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=iso"
            ]
            
            if limit:
                cmd.extend(["-n", str(limit)])
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            
            logger.debug(f"获取Git历史成功: {repo_path}, commits: {len(commits)}")
            return commits
            
        except subprocess.CalledProcessError as e:
            logger.error(f"获取Git历史失败: {repo_path}, error: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"获取Git历史异常: {repo_path}, error: {e}")
            return []
    
    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支"""
        try:
            result = subprocess.run(
                [self._git_command, "checkout", "-b", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Git分支创建成功: {repo_path}, branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git分支创建失败: {repo_path}, error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Git分支创建异常: {repo_path}, error: {e}")
            return False
    
    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """合并分支"""
        try:
            # 切换到目标分支
            subprocess.run(
                [self._git_command, "checkout", target_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 合并源分支
            result = subprocess.run(
                [self._git_command, "merge", source_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Git分支合并成功: {repo_path}, {source_branch} -> {target_branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git分支合并失败: {repo_path}, error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Git分支合并异常: {repo_path}, error: {e}")
            return False


class MockGitService(IGitService):
    """模拟Git服务 - 用于测试"""
    
    def __init__(self) -> None:
        """初始化模拟Git服务"""
        self._commits: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("MockGitService初始化完成")
    
    def init_repo(self, repo_path: Path) -> bool:
        """初始化模拟Git仓库"""
        self._commits[str(repo_path)] = []
        logger.info(f"模拟Git仓库初始化: {repo_path}")
        return True
    
    def commit_changes(self, repo_path: Path, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """模拟提交更改"""
        repo_key = str(repo_path)
        if repo_key not in self._commits:
            self._commits[repo_key] = []
        
        commit_hash = f"mock_{len(self._commits[repo_key]) + 1:08x}"
        commit = {
            "hash": commit_hash,
            "author": "Session Manager",
            "date": datetime.now().isoformat(),
            "message": message,
            "metadata": metadata or {}
        }
        
        self._commits[repo_key].append(commit)
        logger.info(f"模拟Git提交: {repo_path}, hash: {commit_hash}")
        return commit_hash
    
    def get_commit_history(self, repo_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取模拟提交历史"""
        repo_key = str(repo_path)
        commits = self._commits.get(repo_key, [])
        
        if limit:
            commits = commits[-limit:]
        
        return commits
    
    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """模拟创建分支"""
        logger.info(f"模拟Git分支创建: {repo_path}, branch: {branch_name}")
        return True
    
    def merge_branch(self, repo_path: Path, source_branch: str, target_branch: str) -> bool:
        """模拟合并分支"""
        logger.info(f"模拟Git分支合并: {repo_path}, {source_branch} -> {target_branch}")
        return True