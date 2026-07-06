def paginate_query(query, page, per_page=20):
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


def paginate_dict(items, page, per_page=20):
    total = len(items)
    pages = (total + per_page - 1) // per_page if per_page else 1
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
