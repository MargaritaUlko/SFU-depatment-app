from pprint import pprint

import httpx
from fastapi import HTTPException


async def get_schedule(arg: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://edu.sfu-kras.ru/api/timetable/get", params={"target": arg}
        )
        data = response.json()
        pprint(data)
        return data


async def validate(arg: str):
    data = await get_schedule(arg)
    if len(data["timetable"]) == 0:
        raise HTTPException(400, f"группа или преподаватель '{arg}' не найдены в СФУ")
    else:
        print(data)


# asyncio.run(validate("Кушнаренко А. В."))
