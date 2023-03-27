from fastapi import HTTPException, Request

from core.config import TemplateResponse

# серверная программа работает с внутренними ошибками на стороне сервера.
async def server_error(request: Request, exc: HTTPException):
    return TemplateResponse('error_pages/page_500.jinja2',
                            {'request': request})
