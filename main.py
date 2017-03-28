#! /usr/bin/env python
# -*- coding:utf-8 -*-
# by pxy 2017-03-10 13:00:37
import hashlib
import logging
import os
import re
import sys

import aiohttp
import bs4
from aiohttp import web

import receive
import reply

WX_TOKEN = os.getenv('WX_TOKEN')
WX_AESKEY = os.getenv('WX_AESKEY', '')
LOG_FILE = os.getenv('LOG_FILE', '')

handler = logging.FileHandler(LOG_FILE) if LOG_FILE \
    else logging.StreamHandler(sys.stdout)
fmt = '%(asctime)s %(levelname)s %(lineno)3d - %(message)s'
logging.basicConfig(level=logging.INFO, format=fmt, handlers=[handler])

logger = logging.getLogger(__name__)


async def auth_handler(request: web.Request):
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
    url = 'https://thepiratebay.org/search/{}/0/99/0'.format(keyword)
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
        reply_msg = await handle_message(recv_msg)
        return web.Response(text=reply_msg.send())
    except Exception as e:
        logger.exception('Unhandled exception:')
        return web.Response(text=str(e), status=500)


async def handle_message(msg: receive.Msg) -> reply.Msg:
    if isinstance(msg, receive.TextMsg):
        reply_msg = await on_text_message(msg)
    elif isinstance(msg, receive.ImageMsg):
        reply_msg = await on_image_message(msg)
    elif isinstance(msg, receive.EventMsg):
        reply_msg = await on_event_message(msg)
    else:
        reply_msg = await on_other_message(msg)
    return reply_msg


async def on_other_message(msg: receive.Msg) -> reply.Msg:
    to_user = msg.FromUserName
    from_user = msg.ToUserName
    return reply.TextMsg(to_user, from_user, 'Fuck you!')


async def on_text_message(msg: receive.TextMsg) -> reply.Msg:
    to_user = msg.FromUserName
    from_user = msg.ToUserName
    keyword = msg.Content
    pattern = r'[a-zA-Z]+[ \-]?\d+'
    if re.match(pattern, keyword):
        links = await fetch(keyword)
        if links:
            content = links[0]
        else:
            content = 'Nothing can be found'
    else:
        content = 'Illegal keyword'
    return reply.TextMsg(to_user, from_user, content)


async def on_event_message(msg: receive.EventMsg) -> reply.Msg:
    to_user = msg.FromUserName
    from_user = msg.ToUserName
    if msg.Event == 'subscribe':
        content = "I'm an easy way to find your precious."
    else:
        content = 'Unsupported message type'
    return reply.TextMsg(to_user, from_user, content)


async def on_image_message(msg: receive.ImageMsg) -> reply.Msg:
    to_user = msg.FromUserName
    from_user = msg.ToUserName
    content = 'I have no idea.'
    return reply.TextMsg(to_user, from_user, content)


def main():
    app = web.Application(logger=logger)

    app.router.add_get('/wx', auth_handler)
    app.router.add_post('/wx', message_handler)

    web.run_app(app, port=80)


if __name__ == '__main__':
    main()
