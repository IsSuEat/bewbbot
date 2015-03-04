# -*- coding: utf-8 -*-
import sys

__author__ = 'issue'
import os
import random
import praw
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl, task
from ConfigParser import ConfigParser

UA = "bewbs4irc:v1"
r = praw.Reddit(user_agent=UA)


class Config(object):
    config = ConfigParser()

    def __init__(self):
        self.channel = ""
        self.port = None
        self.hostname = ""
        self.subs = []
        self.ssl = None
        self.interval = None

    def create_default_config(self):
        self.config.add_section("config")
        self.config.set("config", "hostname", "")
        self.config.set("config", "port", "")
        self.config.set("config", "channel", "")
        self.config.set("config", "subs", "")
        self.config.set("config", "ssl", "")
        self.config.set("config", "interval", "")
        with open("settings.cfg", "wb") as cfgfile:
            self.config.write(cfgfile)

    def read_config(self, cfgfile):
        self.config.read(cfgfile)
        self.channel = self.config.get("config", "channel")
        self.hostname = self.config.get("config", "hostname")
        self.port = self.config.getint("config", "port")
        self.ssl = self.config.getboolean("config", "ssl")
        self.interval = self.config.getint("config", "interval")
        self.subs = self.config.get("config", "subs").split(',')

    def add_sub(self, msg):
        self.subs.append(msg)
        sub_string = ",".join(self.subs)
        self.config.set("config", "subs", sub_string)
        with open("settings.cfg", "wb") as cfgfile:
            self.config.write(cfgfile)

    def remove_sub(self, sub):
        self.subs.remove(sub)
        sub_string = ",".join(self.subs)
        self.config.set("config", "subs", sub_string)
        with open("settings.cfg", "wb") as cfgfile:
            self.config.write(cfgfile)


def get_bewbs():
    next_sub = random.choice(botcfg.subs)
    try:
        subreddit = r.get_subreddit(next_sub)
        hot = subreddit.get_hot(limit=20)
        submission = [c for c in hot]
        content = random.choice(submission)
        msg = "RANDOM DEPF: {} {} from {}".format(content.title.encode("ascii", "replace"), content.url, next_sub)

        return msg
    except (TypeError, praw.errors.RedirectException, praw.errors.APIException):
        print("Removing sub from list because bad sub is bad ", next_sub)
        botcfg.remove_sub(next_sub)


class BewbBot(irc.IRCClient):
    nickname = "bewbbot"
    password = ""
    hint = "moar"

    def __init__(self):
        pass

    def post_bewbs(self, channel):

        msg = get_bewbs()

        if msg is not None:
            self.say(channel, msg)

    def signedOn(self):
        self.join(self.factory.channel)

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        print("Connected")

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        print("Dropped " + str(reason))

    def privmsg(self, user, channel, message):
        if self.nickname.lower() in message.lower() and self.hint in message.lower():
            print("> USER NEEDS TITS")
            self.post_bewbs(channel)

        if self.nickname.lower() in message.lower() and "add" in message.lower():
            msg = message.lower().split("add")[1].strip()
            if msg == "":
                self.say(channel, "That didnt look readable to me")
            else:
                if msg in botcfg.subs:
                    print("Duplicate entry submitted")
                    self.say(channel, "We already have that")
                else:
                    botcfg.add_sub(msg)
                    print(botcfg.subs)
                    print("> Adding {}".format(msg))
                    self.say(channel, msg + " shows its goods now aswell")

        if self.nickname.lower() in message.lower() and "remove" in message.lower():
            msg = message.lower().split("remove")[1].strip()
            if msg == "":
                self.say(channel, "That didnt look readable to me")
            else:
                if msg in botcfg.subs:
                    botcfg.remove_sub(msg)
                    self.say(channel, "Removed dat shit")
                print(botcfg.subs)
        if self.nickname.lower() in message.lower() and "list" in message.lower():
            self.say(channel, ",".join(botcfg.subs))


    def joined(self, channel):
        print("Joined channel " + channel)

        lc = task.LoopingCall(self.post_bewbs, channel)
        lc.start(botcfg.interval)


class BewbBotFactory(protocol.ClientFactory):
    protocol = BewbBot

    def __init__(self, channel):
        self.channel = channel


    def clientConnectionLost(self, connector, reason):
        print("connection lost " + str(reason))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("connection failed " + str(reason))
        reactor.stop()


if __name__ == "__main__":
    botcfg = Config()
    if not os.path.isfile("settings.cfg"):
        print(">>No config found, creating default")
        botcfg.create_default_config()
        print("edit settings.cfg and rerun")
        sys.exit(0)
    botcfg.read_config("settings.cfg")

    print("Connecting to {} at {}:{} ".format(botcfg.channel, botcfg.hostname, botcfg.port))

    f = BewbBotFactory(botcfg.channel)
    if botcfg.ssl:
        reactor.connectSSL(botcfg.hostname, botcfg.port, f, ssl.ClientContextFactory())
    else:
        reactor.connectTCP(botcfg.hostname, botcfg.port, f)
    reactor.run()




