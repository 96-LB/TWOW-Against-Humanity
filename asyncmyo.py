async def ensure(coro, repeat=10):
    i = 1
    while(i < repeat):
        try:
            return await coro()
        except:
            i += 1
    return await coro()