"""
Utility module for handling pagination and formatting responses.

This module provides a reusable function to paginate data and format 
it into a consistent structure for API responses.
"""
from typing import List, Dict, Any, Callable


def paginate_and_format(
    data: List[Any],
    skip: int,
    limit: int,
    transform: Callable[[Any], Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Paginate and format a list of data.
    Applies pagination and formats the data for a standard response.
    :param data: Complete list of data.
    :param skip: Number of items to skip.
    :param limit: Maximum number of items per page.
    :param transform: Optional function to transform each item.
    :return: Dictionary with paginated data and pagination information.
    """
    total = len(data)
    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1
    has_next = page < pages
    has_prev = page > 1

    paginated_data = data[skip:skip + limit]

    if transform:
        paginated_data = [transform(item) for item in paginated_data]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": has_next,
        "has_prev": has_prev,
        "page": page,
        "size": limit,
        "pages": pages,
        "data": paginated_data,
    }
