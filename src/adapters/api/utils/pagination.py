"""分页工具"""
from typing import List, Any, Dict, Tuple


def paginate_list(items: List[Any], page: int, page_size: int) -> List[Any]:
    """对列表进行分页"""
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def calculate_pagination(total: int, page: int, page_size: int) -> Dict[str, Any]:
    """计算分页信息"""
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }


def get_page_offset(page: int, page_size: int) -> int:
    """获取偏移量"""
    return (page - 1) * page_size


def validate_page_params(page: int, page_size: int, max_page_size: int = 100) -> Tuple[int, int]:
    """验证分页参数"""
    if page < 1:
        page = 1
    
    if page_size < 1:
        page_size = 20
    
    if page_size > max_page_size:
        page_size = max_page_size
    
    return page, page_size