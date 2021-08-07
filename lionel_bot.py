# importing the requests library
import requests
import json
import socket, string
import time
import re
import threading
import chat_plays_go as cpg
import queue
import time

class Chatbot:
    def __init__(self, channel):
        # Some basic variables used to configure the bot
        self.server = "irc.chat.twitch.tv" # Server
        self.channel = "#" + channel # Channel
        self.botnick = # Your bots nick
        self.password = # OAuth
        self.connected = False
        self.start = time.time()
        self.streamers = []
        self.connect()
        self.last_ping = time.time()

        self.cpg_flag = 1

        if self.cpg_flag:
            self.cpgUi = cpg.ChatPlaysGoUi()

        # self.joinchan()

    def connect(self):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.connect((self.server, 6667)) # Here we connect to the server using the port 6667

        self.send_data("PASS " + self.password)
        self.send_data("NICK "+ self.botnick)

    def send_data(self,msg):
        msg = msg + "\r\n"
        self.ircsock.send(msg.encode())

    def check_buffer(self):
        buffer = self.ircsock.recv(2048)
        buffer = buffer.decode()
        buffer = buffer.rstrip("\r\n")
        msg = buffer.split()

        if not self.connected:
            if buffer.endswith("End of /NAMES list"):
                print("Connected to channel %s" % self.channel)
                self.connected = True

        if not msg:
            print("ERROR in channel %s" % self.channel)
            self.connected = False
            self.connect()
            # self.joinchan()

        elif msg[0] == "PING":
            self.send_data("PONG %s" % msg[1])
            print("PONG %s" % self.channel)

    def ping(self): # respond to server Pings.
        self.send_data("PONG :pingis\n")

    def sendmsg(self, msg): # sends messages to the channel.
        self.send_data("PRIVMSG "+ self.channel +" :"+ msg +"\n")

    def joinchan(self, chan): # join channel(s).
        self.send_data("JOIN "+ "#" + chan +"\n")
        print("Joining channel: " + chan)

    def partchan(self, chan): # part channel(s).
        self.send_data("PART "+ "#" + chan +"\n")

    def whisper(self, msg, user): # whisper a user
        self.send_data("PRIVMSG " + user + ' :' + msg.strip('\n\r') + '\n')
    
    def getUserAndMessage(self, buffer):
        msg = buffer.split()
        user = re.findall("(?<=@)(.*)(?=.tmi.twitch)", msg[0])
        message = (" ").join(msg[3:])
        
        return user[0], message[1:]

    def parseMessage(self, buffer):
        
        user, msg = self.getUserAndMessage(buffer)
        print(user + "::" + msg)
        if self.cpg_flag:
            list_coords = self.cpgUi.getCoordsFromMsg(msg)
            if list_coords:
                self.cpgUi.addToHighlightQueue(list_coords)
            if self.cpgUi.isCoordinate(msg) or self.cpgUi.isCommand(msg):
                self.cpgUi.addToQueue(user, msg)

    def bot_main(self):
        self.joinchan("t4rquin")

        # start infinite loop to continually check for and receive new info from server
        while 1:
            if time.time() - self.last_ping > 500:
                print("sending ping")
                self.send_data("PING :tmi.twitch.tv")
                self.last_ping = time.time()

            try:
                buffer = self.ircsock.recv(2048)
                buffer = buffer.decode()
                buffer = buffer.rstrip("\r\n")
                msg = buffer.split()
            except:
                continue
            try:
                self.parseMessage(buffer)
            except:
                pass 

            if buffer.endswith(" :End of /NAMES list"):
                buffer.rstrip(" :End of /NAMES list")
                msg = buffer.split()
                print("Connected to channel %s" % msg[-5])

            elif msg[0] == "PING":
                self.send_data("PONG %s" % msg[1])
                print("PONG %s" % msg[1])
                self.last_ping = time.time()
                #print(time.time() - self.start)

    def sendmsg_main(self):
        time.sleep(1)
        while (1):
            msg = self.cpgUi.getChatbotMsgFromQueue()
            if msg:
                self.sendmsg(msg)
            time.sleep(0.2)

    def time_elapsed(self):
        return time.time() - self.start

    def run_bot(self):
        if self.cpg_flag:
            cb_sendmsg_thread = threading.Thread(target=cb.sendmsg_main)
            cb_sendmsg_thread.start()
        self.bot_main()

if __name__ == "__main__":
    time.sleep(1)
    cb = Chatbot("t4rquin")
    cb_thread = threading.Thread(target=cb.run_bot)
    cb_thread.start()
    if cb.cpg_flag:
        cb.cpgUi.run()

