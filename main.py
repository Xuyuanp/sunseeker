#! /usr/bin/env python
# -*- coding:utf-8 -*-
# by pxy 2017-03-10 13:00:37
import hashlib
import logging
import os
import sys

import aiohttp
import bs4
import re
from aiohttp import web

import receive
import reply

WX_TOKEN = os.getenv('WX_TOKEN')
WX_AESKEY = os.getenv('WX_AESKEY', '')
LOG_FILE = os.getenv('LOG_FILE', '')

stream = open(LOG_FILE, 'a+') if LOG_FILE else sys.stdout
handler = logging.StreamHandler(stream)
fmt = '%(asctime)s %(levelname)s %(lineno)3d - %(message)s'
logging.basicConfig(level=logging.INFO, format=fmt, handlers=[handler])

logger = logging.getLogger(__name__)


async def wx_handler(request: web.Request):
    try:
        logger.info('Got auth request: %s', request.query_string)
        data = request.GET
        signature = data['signature']
        timestamp = data['timestamp']
        nonce = data['nonce']
        echostr = data['echostr']

        sha1 = hashlib.sha1()
        for s in sorted([WX_TOKEN, timestamp, nonce]):
            sha1.update(s.encode())
        hashcode = sha1.hexdigest()
        logger.info("handle/GET func: hashcode, signature: %s %s",
                    hashcode, signature)
        if hashcode == signature:
            return web.Response(text=echostr)
        else:
            return web.Response(text='failed')
    except Exception as e:
        logger.exception('Unhandled exception:')
        return web.Response(text=str(e), status=400)


async def fetch(keyword):
    url = 'https://thepiratebay.org/search/%s/0/99/0' % keyword
    async with aiohttp.ClientSession() as session:
        rsp = await session.get(url)
        if rsp.status != 200:
            return []
        content = await rsp.text()
        soup = bs4.BeautifulSoup(content, 'html.parser')
        links = (a.get('href') for a in soup.find_all('a'))
        return [link for link in links if link.startswith('magnet')]


async def message_handler(request: web.Request):
    try:
        data = await request.read()
        logger.info("Handle Post webdata: %s", data)
        recv_msg = receive.parse_xml(data)
        to_user = recv_msg.FromUserName
        from_user = recv_msg.ToUserName
        if isinstance(recv_msg, receive.TextMsg):
            keyword = recv_msg.Content.decode()
            pattern = '\w+[ -]\d+'
            if re.match(pattern, keyword):
                pass
            links = await fetch(keyword)
            if links:
                content = links[0]
            else:
                content = 'Nothing can be found'
        else:
            content = 'Unsupported message type'
        reply_msg = reply.TextMsg(to_user, from_user, content)
        return web.Response(text=reply_msg.send())
    except Exception as e:
        logger.exception('Unhandled exception:')
        return web.Response(text=str(e), status=500)


def main():
    app = web.Application(logger=logger)

    app.router.add_get('/wx', wx_handler)
    app.router.add_post('/wx', message_handler)

    web.run_app(app, port=80)


if __name__ == '__main__':
    main()
