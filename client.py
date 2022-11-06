import aiohttp
from asyncio import run


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8080/advert/',
                                json={"title": "dogs", "description": "2 puppies, black and white",
                                      "owner": "A.Kalinin"}) as resp:
            print(resp.status)
            print(await resp.json())
        async with session.get('http://127.0.0.1:8080/advert/1') as resp:
            print(resp.status)
            print(await resp.json())
        async with session.post('http://127.0.0.1:8080/advert/',
                                json={"title": "cats", "description": "special bride", "owner": "S.Ivanov"}) as resp:
            print(resp.status)
            print(await resp.json())
        async with session.get('http://127.0.0.1:8080/advert/2') as resp:
            print(resp.status)
            print(await resp.json())
        async with session.delete('http://127.0.0.1:8080/advert/2') as resp:
            print(resp.status)
            print(await resp.json())
        async with session.get('http://127.0.0.1:8080/advert/2') as resp:
            print(resp.status)
            print(await resp.json())


run(main())
