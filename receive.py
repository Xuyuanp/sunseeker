#! /usr/bin/env python
# -*- coding:utf-8 -*-
# by pxy 2017-03-10 15:40:18
from xml.etree.ElementTree import fromstring


def parse_xml(web_data):
    if len(web_data) == 0:
        return None
    xml_data = fromstring(web_data)
    msg_type = xml_data.find('MsgType').text
    if msg_type == 'text':
        return TextMsg(xml_data)
    elif msg_type == 'image':
        return ImageMsg(xml_data)
    elif msg_type == 'event':
        return EventMsg(xml_data)


class Msg(object):
    def __init__(self, xml_data):
        self.ToUserName = xml_data.find('ToUserName').text
        self.FromUserName = xml_data.find('FromUserName').text
        self.CreateTime = xml_data.find('CreateTime').text
        self.MsgType = xml_data.find('MsgType').text


class TextMsg(Msg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.Content = xml_data.find('Content').text
        self.MsgId = xml_data.find('MsgId').text


class ImageMsg(Msg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.PicUrl = xml_data.find('PicUrl').text
        self.MediaId = xml_data.find('MediaId').text


class EventMsg(Msg):
    def __init__(self, xml_data):
        super().__init__(xml_data)
        self.Event = xml_data.find('Event').text
        self.EventKey = xml_data.find('EventKey').text
