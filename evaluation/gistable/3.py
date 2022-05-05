from timeit import timeit
import asyncio
import requests
from threading import Thread

import aiohttp

client = aiohttp.ClientSession()


def call_threaded():
    threads = [Thread(target=call_google_normal) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def call_async():
    responses = [call_google() for i in range(10)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(responses))


async def call_google():

    async with client.get('http://google.com') as resp:
        return resp.status


def call_google_normal():
    resp = requests.get('http://google.com')
    return resp.status_code


def call_normal():
    responses = [call_google_normal() for i in range(10)]


def myfunc(a):
    a = ' '.join(['hello', a])


num = 5
a = timeit(call_normal, number=num)
b = timeit(call_async, number=num)
c = timeit(call_threaded, number=num)

print('normal:', a)
print('async:', b)
print('threaded:', c)

client.close()
