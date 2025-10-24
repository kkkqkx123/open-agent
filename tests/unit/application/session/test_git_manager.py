"""Git管理器单元测试"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.sessions.git_manager import GitManager, MockGitManager, IGitManager, create_git_manager


class TestGitManager:
    """Git管理器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def git_manager(self):
        """创建Git管理器实例"""
        return GitManager()

    def test_init(self):
        """测试初始化"""
        manager = GitManager("custom-git")
        assert manager.git_executable == "custom-git"

        default_manager = GitManager()
        assert default_manager.git_executable == "git"

    def test_run_git_command(self, git_manager, temp_dir):
        """测试运行Git命令"""
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "success"
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            result = git_manager._run_git_command(temp_dir, ["status"])

            assert result.returncode == 0
            assert result.stdout == "success"
            mock_run.assert_called_once_with(
                ["git", "status"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False
            )

    def test_init_repo_success(self, git_manager, temp_dir):
        """测试成功初始化仓库"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟成功的Git命令
            mock_run.side_effect = [
                Mock(returncode=0),  # git init
                Mock(returncode=0),  # git config user.name check
                Mock(returncode=0),  # git config user.email check
                Mock(returncode=0),  # git commit
            ]

            with patch.object(git_manager, '_create_gitignore'):
                with patch.object(git_manager, 'commit_changes', return_value=True):
                    result = git_manager.init_repo(temp_dir)

            assert result is True
            assert temp_dir.exists()

    def test_init_repo_failure(self, git_manager, temp_dir):
        """测试初始化仓库失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟失败的git init命令
            mock_run.return_value = Mock(returncode=1)

            result = git_manager.init_repo(temp_dir)

            assert result is False

    def test_init_repo_exception(self, git_manager, temp_dir):
        """测试初始化仓库异常"""
        with patch.object(git_manager, '_run_git_command', side_effect=Exception("Git错误")):
            result = git_manager.init_repo(temp_dir)
            assert result is False

    def test_commit_changes_success(self, git_manager, temp_dir):
        """测试成功提交更改"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟成功的Git命令
            mock_run.side_effect = [
                Mock(returncode=0, stdout="M file.txt"),  # git add
                Mock(returncode=0, stdout="M file.txt"),  # git status
                Mock(returncode=0),  # git commit
            ]

            result = git_manager.commit_changes(temp_dir, "测试提交")

            assert result is True

    def test_commit_changes_no_changes(self, git_manager, temp_dir):
        """测试没有更改需要提交"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟没有更改的状态
            mock_run.side_effect = [
                Mock(returncode=0),  # git add
                Mock(returncode=0, stdout=""),  # git status (空输出)
            ]

            result = git_manager.commit_changes(temp_dir, "测试提交")

            assert result is True

    def test_commit_changes_with_metadata(self, git_manager, temp_dir):
        """测试带元数据的提交"""
        metadata = {"session_id": "test-session", "step": 1}
        
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟成功的Git命令
            mock_run.side_effect = [
                Mock(returncode=0, stdout="M file.txt"),  # git add
                Mock(returncode=0, stdout="M file.txt"),  # git status
                Mock(returncode=0),  # git commit
            ]

            result = git_manager.commit_changes(temp_dir, "测试提交", metadata)

            assert result is True
            # 验证提交消息包含元数据
            commit_call = mock_run.call_args_list[2]
            commit_message = commit_call[0][1][2]  # 获取commit命令的message参数
            assert "元数据:" in commit_message
            assert json.dumps(metadata, ensure_ascii=False) in commit_message

    def test_commit_changes_failure(self, git_manager, temp_dir):
        """测试提交更改失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟失败的git add命令
            mock_run.return_value = Mock(returncode=1)

            result = git_manager.commit_changes(temp_dir, "测试提交")

            assert result is False

    def test_get_commit_history_success(self, git_manager, temp_dir):
        """测试成功获取提交历史"""
        mock_log_output = """abc123|Test User|2023-01-01 00:00:00 +0000|Initial commit
def456|Test User|2023-01-02 00:00:00 +0000|Second commit

元数据: {"session_id": "test-session"}"""

        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_log_output)

            result = git_manager.get_commit_history(temp_dir)

            assert len(result) == 2
            assert result[0]["hash"] == "abc123"
            assert result[0]["author"] == "Test User"
            assert result[0]["message"] == "Initial commit"
            assert result[0]["metadata"] == {}

            assert result[1]["hash"] == "def456"
            assert result[1]["message"] == "Second commit"
            assert result[1]["metadata"] == {"session_id": "test-session"}

    def test_get_commit_history_failure(self, git_manager, temp_dir):
        """测试获取提交历史失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_manager.get_commit_history(temp_dir)

            assert result == []

    def test_get_commit_history_malformed_output(self, git_manager, temp_dir):
        """测试处理格式错误的提交历史输出"""
        mock_log_output = """malformed line
abc123|Test User|2023-01-01 00:00:00 +0000|Initial commit"""

        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_log_output)

            result = git_manager.get_commit_history(temp_dir)

            assert len(result) == 1
            assert result[0]["hash"] == "abc123"

    def test_create_branch_success(self, git_manager, temp_dir):
        """测试成功创建分支"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_manager.create_branch(temp_dir, "feature-branch")

            assert result is True
            mock_run.assert_called_once_with(temp_dir, ["checkout", "-b", "feature-branch"])

    def test_create_branch_failure(self, git_manager, temp_dir):
        """测试创建分支失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_manager.create_branch(temp_dir, "feature-branch")

            assert result is False

    def test_switch_branch_success(self, git_manager, temp_dir):
        """测试成功切换分支"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_manager.switch_branch(temp_dir, "main")

            assert result is True
            mock_run.assert_called_once_with(temp_dir, ["checkout", "main"])

    def test_switch_branch_failure(self, git_manager, temp_dir):
        """测试切换分支失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_manager.switch_branch(temp_dir, "main")

            assert result is False

    def test_merge_branch_success(self, git_manager, temp_dir):
        """测试成功合并分支"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            with patch.object(git_manager, 'switch_branch', return_value=True):
                mock_run.return_value = Mock(returncode=0)

                result = git_manager.merge_branch(temp_dir, "feature", "main")

                assert result is True
                mock_run.assert_called_once_with(temp_dir, ["merge", "feature"])

    def test_merge_branch_switch_failure(self, git_manager, temp_dir):
        """测试合并分支时切换失败"""
        with patch.object(git_manager, 'switch_branch', return_value=False):
            result = git_manager.merge_branch(temp_dir, "feature", "main")
            assert result is False

    def test_merge_branch_merge_failure(self, git_manager, temp_dir):
        """测试合并分支时合并失败"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            with patch.object(git_manager, 'switch_branch', return_value=True):
                mock_run.return_value = Mock(returncode=1)

                result = git_manager.merge_branch(temp_dir, "feature", "main")

                assert result is False

    def test_configure_user_if_needed(self, git_manager, temp_dir):
        """测试配置用户信息"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟未配置用户信息
            mock_run.side_effect = [
                Mock(returncode=1, stdout=""),  # git config user.name check
                Mock(returncode=0),  # git config user.name set
                Mock(returncode=1, stdout=""),  # git config user.email check
                Mock(returncode=0),  # git config user.email set
            ]

            git_manager._configure_user_if_needed(temp_dir)

            assert mock_run.call_count == 4

    def test_configure_user_already_configured(self, git_manager, temp_dir):
        """测试用户信息已配置的情况"""
        with patch.object(git_manager, '_run_git_command') as mock_run:
            # 模拟已配置用户信息
            mock_run.side_effect = [
                Mock(returncode=0, stdout="Test User"),  # git config user.name check
                Mock(returncode=0, stdout="test@example.com"),  # git config user.email check
            ]

            git_manager._configure_user_if_needed(temp_dir)

            assert mock_run.call_count == 2

    def test_create_gitignore(self, git_manager, temp_dir):
        """测试创建.gitignore文件"""
        gitignore_path = temp_dir / ".gitignore"
        
        git_manager._create_gitignore(temp_dir)
        
        assert gitignore_path.exists()
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "*.tmp" in content
        assert ".DS_Store" in content
        assert ".vscode/" in content

    def test_create_gitignore_already_exists(self, git_manager, temp_dir):
        """测试.gitignore文件已存在的情况"""
        gitignore_path = temp_dir / ".gitignore"
        gitignore_path.write_text("existing content")
        
        git_manager._create_gitignore(temp_dir)
        
        # 验证文件内容未被覆盖
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "existing content"


class TestMockGitManager:
    """模拟Git管理器测试类"""

    @pytest.fixture
    def mock_git_manager(self):
        """创建模拟Git管理器实例"""
        return MockGitManager()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init(self, mock_git_manager):
        """测试初始化"""
        assert mock_git_manager._repos == {}

    def test_init_repo(self, mock_git_manager, temp_dir):
        """测试初始化仓库"""
        result = mock_git_manager.init_repo(temp_dir)
        
        assert result is True
        repo_key = str(temp_dir)
        assert repo_key in mock_git_manager._repos
        assert mock_git_manager._repos[repo_key] == []

    def test_commit_changes(self, mock_git_manager, temp_dir):
        """测试提交更改"""
        # 先初始化仓库
        mock_git_manager.init_repo(temp_dir)
        
        metadata = {"session_id": "test-session"}
        result = mock_git_manager.commit_changes(temp_dir, "测试提交", metadata)
        
        assert result is True
        repo_key = str(temp_dir)
        commits = mock_git_manager._repos[repo_key]
        assert len(commits) == 1
        assert commits[0]["message"] == "测试提交"
        assert commits[0]["metadata"] == metadata
        assert commits[0]["hash"] == "mock_0"

    def test_commit_changes_repo_not_exists(self, mock_git_manager, temp_dir):
        """测试向不存在的仓库提交"""
        result = mock_git_manager.commit_changes(temp_dir, "测试提交")
        assert result is False

    def test_get_commit_history(self, mock_git_manager, temp_dir):
        """测试获取提交历史"""
        # 先初始化仓库并提交
        mock_git_manager.init_repo(temp_dir)
        mock_git_manager.commit_changes(temp_dir, "第一次提交")
        mock_git_manager.commit_changes(temp_dir, "第二次提交")
        
        result = mock_git_manager.get_commit_history(temp_dir)
        
        assert len(result) == 2
        assert result[0]["message"] == "第一次提交"
        assert result[1]["message"] == "第二次提交"

    def test_get_commit_history_repo_not_exists(self, mock_git_manager, temp_dir):
        """测试获取不存在仓库的提交历史"""
        result = mock_git_manager.get_commit_history(temp_dir)
        assert result == []

    def test_create_branch(self, mock_git_manager):
        """测试创建分支"""
        result = mock_git_manager.create_branch(Path("/test"), "feature")
        assert result is True

    def test_switch_branch(self, mock_git_manager):
        """测试切换分支"""
        result = mock_git_manager.switch_branch(Path("/test"), "main")
        assert result is True

    def test_merge_branch(self, mock_git_manager):
        """测试合并分支"""
        result = mock_git_manager.merge_branch(Path("/test"), "feature", "main")
        assert result is True


class TestCreateGitManager:
    """创建Git管理器测试类"""

    def test_create_git_manager_real(self):
        """测试创建真实Git管理器"""
        manager = create_git_manager(use_mock=False, git_executable="git")
        assert isinstance(manager, GitManager)
        assert manager.git_executable == "git"

    def test_create_git_manager_mock(self):
        """测试创建模拟Git管理器"""
        manager = create_git_manager(use_mock=True)
        assert isinstance(manager, MockGitManager)

    def test_create_git_manager_default(self):
        """测试使用默认参数创建Git管理器"""
        manager = create_git_manager()
        assert isinstance(manager, GitManager)
        assert manager.git_executable == "git"


class TestIGitManager:
    """Git管理器接口测试类"""

    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证接口定义了所有必需的方法
        assert hasattr(IGitManager, 'init_repo')
        assert hasattr(IGitManager, 'commit_changes')
        assert hasattr(IGitManager, 'get_commit_history')
        assert hasattr(IGitManager, 'create_branch')
        assert hasattr(IGitManager, 'switch_branch')
        assert hasattr(IGitManager, 'merge_branch')
        
        # 验证方法是抽象方法
        assert getattr(IGitManager.init_repo, '__isabstractmethod__', False)
        assert getattr(IGitManager.commit_changes, '__isabstractmethod__', False)
        assert getattr(IGitManager.get_commit_history, '__isabstractmethod__', False)
        assert getattr(IGitManager.create_branch, '__isabstractmethod__', False)
        assert getattr(IGitManager.switch_branch, '__isabstractmethod__', False)
        assert getattr(IGitManager.merge_branch, '__isabstractmethod__', False)
