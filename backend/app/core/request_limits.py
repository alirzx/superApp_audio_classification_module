from starlette.responses import JSONResponse

class RequestBodyLimitMiddleware:
    """Bound request body, including chunked uploads, before multipart parsing."""
    def __init__(self,app,max_bytes: int):
        self.app=app
        self.max_bytes=max_bytes

    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope.get("method")!="POST" or scope.get("path")!="/v1/classify":
            return await self.app(scope,receive,send)
        raw=dict(scope.get("headers",[])).get(b"content-length")
        if raw:
            try:
                declared=int(raw)
                if declared<0: raise ValueError()
                if declared>self.max_bytes:
                    return await JSONResponse({"detail":"Request body too large"},status_code=413)(scope,receive,send)
            except ValueError:
                return await JSONResponse({"detail":"Invalid Content-Length"},status_code=400)(scope,receive,send)
        messages=[]
        total=0
        while True:
            message=await receive()
            if message["type"]=="http.disconnect": return
            if message["type"]!="http.request": continue
            total+=len(message.get("body",b""))
            if total>self.max_bytes:
                return await JSONResponse({"detail":"Request body too large"},status_code=413)(scope,receive,send)
            messages.append(message)
            if not message.get("more_body",False): break
        iterator=iter(messages)
        async def replay():
            return next(iterator,{"type":"http.request","body":b"","more_body":False})
        return await self.app(scope,replay,send)
