from fastapi import HTTPException, Request

from core.config import TemplateResponse

# сервер не может найти данные согласно запросу
async def not_found(request: Request, exc: HTTPException):
    return TemplateResponse('error_pages/page_not_found.jinja2',
                            {'request': request})
