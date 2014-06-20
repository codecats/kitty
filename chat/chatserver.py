# -*- coding: utf-8 -*-
#http://ferretfarmer.net/2013/09/05/tutorial-real-time-chat-with-django-twisted-and-websockets-part-2/
'''
#checkout the twisted project
git clone https://github.com/twisted/twisted.git twisted-websocket

#switch to the most up to date websocket branch
cd twisted-websocket
git fetch
git checkout websocket-4173-4

#install it - preferably do this in a virtualenv
python setup.py install



#after install twistd -n -y chatserver.py
'''
import json
import datetime

'''
Add path to run django app
'''
import os
import sys
os.getcwd()
path = os.path.join(os.getcwd(), '..')
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitty.settings")


from twisted.internet.protocol import connectionDone
from twisted.protocols import basic
from twisted.web.websockets import WebSocketsResource, WebSocketsProtocol, lookupProtocolForFactory
from collections import deque

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.http import request
from django.contrib.sessions.backends.db import SessionStore

class MyChat(basic.LineReceiver):
    DEFAULT_USERNAME = 'guest'
    def connectionMade(self):
        self.username = self.DEFAULT_USERNAME + str(len(self.factory.clients))
        self.factory.clients.append(self)
        Messenger().connected_message(self)
        iterator = 0
        for message in self.factory.messages:
            Messenger().message(self, self.factory.authors[iterator], message, self.factory.time[iterator])
            iterator += 1
        Messenger().send_users(self.factory.clients)

    def connectionLost(self, reason=connectionDone):
        print 'Lost client!'
        Messenger().send_lost_user(self.factory.clients, self)
        self.factory.clients.remove(self)

    def dataReceived(self, data):
        try:
            data = json.loads(data)
        except:
            pass
        print data
        if 'key' in data:
            try:
                session = Session.objects.get(session_key=data['key'])
                session_data = session.get_decoded()
                uid = session_data.get('_auth_user_id')
                user = User.objects.get(id=uid)
                username = self.username
                self.username = str(user)
                Messenger().changed_username(self.factory.clients, self.username, username)
                # for c in self.factory.clients:
                #     c.message('joined: ' + str(user))
            except:
                pass

        else:
            print 'received', repr(data)
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.factory.messages.append(data)
            self.factory.authors.append(self)
            self.factory.time.append(time)
            Messenger().to_all(self.factory.clients, self, data)
            # for c in self.factory.clients:
            #     c.message(time + ', ' + self.username + ': ' + data)

    def message(self, message):
        self.transport.write(message + '\n')
    def messageUTF8(self, message):
        '''
        use it from server site when message is utf8
        '''
        self.message(message.encode('utf8'))

from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import protocol
from twisted.application import service, internet

from twisted.internet.protocol import Factory

class ChatFactory(Factory):
    protocol = MyChat
    clients = []
    messages = deque(maxlen=20)
    authors = deque(maxlen=20)
    time = deque(maxlen=20)

class Messenger(object):
    def to_all(self, clients, sender, message, time=None):
        if not time:
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for c in clients:
            self.message(c, sender, message, time)

    def message(self, receiver, sender, message, time):
        pack = json.dumps({'msg': message, 'time': time, 'sender': sender.username, 'receiver': receiver.username})
        receiver.message(pack)

    def send_users(self, clients, users=None):
        if not users:
            users = clients
        all_clients = json.dumps({'all_clients': [user.username for user in users]})
        self.propagate(clients, all_clients)

    def send_lost_user(self, clients, user):
        self.propagate(clients, json.dumps({'client_lost': user.username}))

    def changed_username(self, clients, new_username, old_username):
        self.propagate(clients, json.dumps({'username_changed':{'new': new_username, 'old': old_username}}))

    def propagate(self, clients, message):
        for c in clients:
            c.message(message)

    def connected_message(self, user):
        user.message(json.dumps({'connection_status': True}))


resource = WebSocketsResource(lookupProtocolForFactory(ChatFactory()))
root = Resource()

root.putChild('ws', resource)
application = service.Application('chatserver')
internet.TCPServer(1025, Site(root)).setServiceParent(application)