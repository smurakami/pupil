#coding: utf-8
'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''
from plugin import Plugin

import numpy as np
from pyglui import ui
import zmq

# for web socket
import tornado.ioloop
import tornado.web
import tornado.websocket
# from tornado.ioloop import PeriodicCallback
from tornado.options import define, options, parse_command_line

import threading


import logging
logger = logging.getLogger(__name__)

web_sockets = []

class Pupil_Server(Plugin):
    """pupil server plugin"""
    def __init__(self, g_pool,address="tcp://127.0.0.1:5000",menu_conf = {'collapsed':True,'pos':(300,300),'size':(300,300)}):
        super(Pupil_Server, self).__init__(g_pool)
        self.order = .9
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.address = ''
        self.set_server(address)
        # self.set_websocket_server()
        self.set_websocket_client()
        self.menu = None
        self.menu_conf = menu_conf

        self.exclude_list = ['ellipse','pos_in_roi','major','minor','axes','angle','center']

    def init_gui(self):
        help_str = "Pupil Message server: Using ZMQ and the *Publish-Subscribe* scheme"
        self.menu = ui.Growing_Menu("Pupil Broadcast Server")
        self.menu.append(ui.Info_Text(help_str))
        self.menu.append(ui.Text_Input('address',self,setter=self.set_server,label='Address'))
        self.menu.append(ui.Button('Close',self.close))
        if self.g_pool.app == 'capture':
            self.menu.configuration = {'collapsed':self.menu_conf['collapsed']}
            self.g_pool.sidebar.append(self.menu)
        elif self.g_pool.app == 'player':
            self.menu.configuration = self.menu_conf

            self.g_pool.gui.append(self.menu)

    def deinit_gui(self):
        if self.menu:
            self.menu_conf = self.menu.configuration
            if self.g_pool.app == 'capture':
                self.g_pool.sidebar.remove(self.menu)
            elif self.g_pool.app == 'player':
                self.g_pool.gui.remove(self.menu)
            self.menu = None


    def set_server(self,new_address):
        try:
            self.socket.unbind(self.address)
            logger.debug('Detached from %s'%self.address)
        except:
            pass
        try:
            self.socket.bind(new_address)
            self.address = new_address
            logger.debug('Bound to %s'%self.address)

        except zmq.ZMQError as e:
            logger.error("Could not set Socket: %s. Reason: %s"%(new_address,e))

    def update(self,frame,events):
        for p in events['pupil_positions']:
            msg = "Pupil\n"
            for key,value in p.iteritems():
                if key not in self.exclude_list:
                    msg +=key+":"+str(value)+'\n'
            self.socket.send( msg )
            # for s in web_sockets:
            #     s.send_message( msg )

        for g in events.get('gaze',[]):
            msg = "Gaze\n"
            for key,value in g.iteritems():
                if key not in self.exclude_list:
                    msg +=key+":"+str(value)+'\n'
            self.socket.send( msg )

            # send gaze pos to browser
            pos = g['norm_pos']
            pos_in_display_key = 'realtime gaze on display'
            if pos_in_display_key in g:
                in_display = 1
                pos_in_display = g[pos_in_display_key]
            else:
                in_display = 0
                pos_in_display = (-1, -1)
            msg = '{"msg": "pupil_pos", "pos": {"x": %f, "y": %f}, "pos_in_display": {"x": %f, "y": %f}, "player": %d, "in_display": %d}' % (pos[0], pos[1], pos_in_display[0], pos_in_display[1], self.torado_client.player_id, in_display)
            for s in web_sockets:
                s.send_message( msg )

            self.torado_client.write_message(msg)
            print "player_id", self.torado_client.player_id

        # for e in events:
        #     msg = 'Event'+'\n'
        #     for key,value in e.iteritems():
        #         if key not in self.exclude_list:
        #             msg +=key+":"+str(value).replace('\n','')+'\n'
        #     self.socket.send( msg )

    def close(self):
        self.alive = False


    def get_init_dict(self):
        d = {}
        d['address'] = self.address
        if self.menu:
            d['menu_conf'] = self.menu.configuration
        else:
            d['menu_conf'] = self.menu_conf
        return d

    def set_websocket_client(self):
        self.torado_client = TornadoClient("ws://192.168.10.11:8181")
        parse_command_line()
        t = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
        t.start()

    def set_websocket_server(self):
        define("port", default = 8080, help = "run on the given port", type = int)

        app = tornado.web.Application([
            (r"/", IndexHandler),
            (r"/ws", SendWebSocket),
        ])
        parse_command_line()
        app.listen(options.port)
        t = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
        t.start()

    def cleanup(self):
        """gets called when the plugin get terminated.
        This happens either voluntarily or forced.
        """
        self.deinit_gui()
        self.context.destroy()
        tornado.ioloop.IOLoop.instance().stop()

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")

class SendWebSocket(tornado.websocket.WebSocketHandler):
    #on_message -> receive data
    #write_message -> send data

    #index.htmlでコネクションが確保されると呼び出される
    def open(self):
        self.i = 0
        self.callback = PeriodicCallback(self._send_message, 400) #遅延用コールバック
        self.callback.start()
        print "WebSocket opened"
        web_sockets.append(self)

    #クライアントからメッセージが送られてくると呼び出される
    def on_message(self, message):
        print message

    def send_message(self, message):
        self.write_message(message)

    #コールバックスタートで呼び出しが始まる
    # def _send_message(self):
    #     self.i += 1
    #     self.write_message(str(self.i))

    #ページが閉じ、コネクションが切れる事で呼び出し
    def on_close(self):
        # self.callback.stop()
        web_sockets.remove(self)
        print "WebSocket closed"

from tornado import ioloop, websocket, web
import time
import wsaccel
import json
patched = 0

class TornadoClient(object):
    def __init__(self, url):
        websocket.websocket_connect(url, callback=self.on_connect)
        self.url = url
        self.client = None
        self.cnt = 0
        self.started_at = time.time()
        self.player_id = 0

    def on_connect(self, client):
        self.client = client.result()
        self.client.on_message = self.on_received
        self.client.write_message('{"msg": "new_player"}')

    def write_message(self, msg):
        if self.client:
            self.client.write_message(msg)

    def on_received(self, message):
        if not message:
            return
        #print("client received:", message[:20])
        self.cnt += 1

        print message

        try:
            msg = json.loads(message)
            if msg['msg'] == 'new_player':
                print "new_player!"
                print msg['player']
                self.player_id = msg['player']

        except:
            pass

        if self.cnt < 1000:
            # self.client.write_message('{"msg": "hello"}')
            pass
        else:
            print(self.cnt, time.time() - self.started_at)
            self.client.protocol.close()
            global patched
            if not patched:
                patched += 1
                wsaccel.patch_tornado()
                TornadoClient(self.url)
