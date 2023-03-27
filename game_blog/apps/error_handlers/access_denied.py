from fastapi import HTTPException, Request
from core.config import TemplateResponse

# 403 - доступ к запрошенному ресурсу запрещен. Сервер понял запрос, но не выполнит его
async def no_access(request: Request, exc: HTTPException):
    return TemplateResponse('error_pages/page_403.jinja2',
                            {'request': request})
