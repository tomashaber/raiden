# -*- coding: utf8 -*-
from __future__ import print_function

import gevent

from raiden.messages import decode
from raiden.network.transport import DummyTransport
from raiden.utils import pex

gevent.get_hub().SYSTEM_ERROR = BaseException


def setup_messages_cb():
    messages = []

    def callback(sender_raiden, host_port, msg):  # pylint: disable=unused-argument
        messages.append(msg)

    DummyTransport.network.on_send_cbs.extend([callback])

    return messages


def dump_messages(message_list):
    print('dumping {} messages'.format(len(message_list)))

    for message in message_list:
        print(message)


class MessageLog(object):

    SENT = '>'
    RECV = '<'

    def __init__(self, address, msg, direction):
        self.address = address
        self.msg = msg
        self.direction = direction
        self.is_decoded = False

    def is_recv(self):
        return self.direction == self.RECV

    def is_sent(self):
        return self.direction == self.SENT

    @property
    def decoded(self):
        if self.is_decoded:
            return self.msg
        self.is_decoded = True
        self.msg = decode(self.msg)
        return self.msg


class MessageLogger(object):

    """Register callbacks to collect all messages. Messages can be queried"""

    def __init__(self):
        self.messages_by_node = {}

        def sent_msg_cb(sender_raiden, host_port, msg):
            self.collect_message(sender_raiden.address, msg, MessageLog.SENT)
        DummyTransport.network.on_send_cbs.extend([sent_msg_cb])

        def recv_msg_cb(receiver_raiden, host_port, msg):
            self.collect_message(receiver_raiden.address, msg, MessageLog.RECV)
        DummyTransport.on_recv_cbs.extend([recv_msg_cb])

    def collect_message(self, address, msg, direction):
        msglog = MessageLog(address, msg, direction)
        key = pex(address)
        self.messages_by_node.setdefault(key, [])
        self.messages_by_node[key].append(msglog)

    def get_node_messages(self, node_address, only=None):
        """ Return list of node's messages.

        Args:
            node_messages: The hex representation of the data
            only: Flag to filter messages, valid values are sent and recv.

        Returns:
            List[message]: The relevante messages that involved the node.
        """
        node_messages = self.messages_by_node.get(node_address, [])

        if only == 'sent':
            result = [
                message
                for message in node_messages
                if message.is_sent()
            ]
        elif only == 'recv':
            result = [
                message
                for message in node_messages
                if message.is_recv()
            ]
        else:
            result = node_messages

        return [
            message.decoded
            for message in result
        ]