from starlette.responses import JSONResponse
class RequestBodyLimitMiddleware:
    """Reject declared oversized bodies, and bound streaming bytes before downstream consumes them."""
    def __init__(self,app,max_bytes: int): self.app=app; self.max_bytes=max_bytes
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http": return await self.app(scope,receive,send)
        raw=dict(scope.get("headers",[])).get(b"content-length")
        if raw:
            try:
                if int(raw)>self.max_bytes:
                    return await JSONResponse({"detail":"Request body too large"},status_code=413)(scope,receive,send)
            except ValueError:
                return await JSONResponse({"detail":"Invalid Content-Length"},status_code=400)(scope,receive,send)
        total=0
        async def limited_receive():
            nonlocal total
            message=await receive()
            if message["type"]=="http.request":
                total+=len(message.get("body",b""))
                if total>self.max_bytes: raise BodyTooLarge()
            return message
        try: await self.app(scope,limited_receive,send)
        except BodyTooLarge: return
class BodyTooLarge(Exception): pass
