import threading
import time
import tkinter as tk
from tkinter import font
from PIL import Image
from PIL import ImageTk as itk
import random
import re
import queue
import numpy as np
import pyautogui
from collections import defaultdict
import win32gui
import json

FOX = 0
OGS = 1
KGS = 2

ASCEND = 10
DESCEND = 11

ATOS = 20
ATOT = 21

def recordCoordinateEntry(user, msg):
    pass

class ChatPlaysGoUi:
    def __init__(self):
        # Root initialization
        self.root = tk.Tk()
        self.root.title("Chat Plays Go Overlay")
        self.root.geometry("+2200+50")

        # Control panel
        self.cp = tk.Toplevel()
        self.cp.title("Control Panel")
        self.cp.geometry("300x200+1500+100")

        # Info panel
        self.info_panel = tk.Toplevel()
        self.info_panel.title("Info Panel")
        self.info_panel.geometry("+1300+500")
        self.info_panel.configure(bg="black")
        self.info_show_top_n = 5
        
        # Voter panel
        self.voter_panel = tk.Toplevel()
        self.voter_panel.title("Voter Panel")
        self.voter_panel.geometry("+1500+450")
        self.voter_panel.configure(bg="black")
        self.voter_show_top_n = 5
        self.voter_panel.columnconfigure([1], minsize=130)

        # Daily voter panel
        self.daily_voter_panel = tk.Toplevel()
        self.daily_voter_panel.title("Daily voter Panel")
        self.daily_voter_panel.geometry("+1300+600")
        self.daily_voter_panel.configure(bg="black")
        self.daily_voter_show_top_n = 5
        self.daily_voter_panel.columnconfigure([1], minsize=130)

        self.alignmentModeVar = tk.BooleanVar(self.cp)
        self.highlightModeVar = tk.BooleanVar(self.cp)
        self.autoModeVar = tk.BooleanVar(self.cp)
        self.pairGoModeVar = tk.BooleanVar(self.cp)
        self.colorVar = tk.BooleanVar(self.cp)
        self.gameClientVar = tk.IntVar()

        #Styles
        self.default_font = font.Font(family="Source Code Pro Semibold", size=28, weight="bold")
        self.small_font = font.Font(family="Source Code Pro Semibold", size=15, weight="bold")
        self.grey_color = '#9F9F9F'

        self.clock_frame = []
        self.countdown_label = []
        # self.countdown_label = tk.Label(self.info_panel, fg=self.grey_color, bg="black", text="42", font=self.default_font)

        self.chatbot_queue = queue.Queue()

        self.queue = queue.Queue()
        self.queueHighlight = queue.Queue()
        self.img_size = 45

        self.label_list = []
        self.info_coord_list = []
        self.info_vote_list = []
        self.top_voter_list = []
        self.voter_votes_list = []
        self.daily_top_voter_list = []
        self.daily_voter_votes_list = []

        self.dict = defaultdict(int)
        self.highlight_dict = defaultdict(float)
        self.voters_dict = defaultdict(int)
        self.daily_voters_dict = defaultdict(int)
        self.list_of_users_voted_per_move = defaultdict(list)
        self.list_of_users_voted_this_turn = []

        self.loadVoterStats()
        self.list_of_images = []
        self.total_votes = 0
        self.turn_start_time = 0
        self.time_per_turn = 24
        self.time_elapsed = 0
        self.last_highlight_time = 0
        self.highlight_time_on_screen = 5

        self.isOppoTurn = True
        self.autoMode = False
        self.pairGoMode = False
        self.alignmentMode = False
        self.highlightMode = True
        self.vertAxisOrder = ASCEND
        self.horzAxis = ATOS
        self.boardSize = 19
        self.gameClient = FOX

        self.game_color = "White"

        self.top_left_mouse_position = (278, 64)
        self.board_spacing = 50

        self.isRunning = False
        self.reminder_flag = False
        # self.root.wm_attributes("-transparentcolor", "black")
        # self.image_shades = 20

        self.loadImages()

        # DEBUG ONLY
        win_img = Image.open('win.png')
        win_img = win_img.resize((self.img_size, self.img_size), Image.ANTIALIAS)
        self.win = itk.PhotoImage(win_img)
        # Loss img
        loss_img = Image.open('loss.png')
        loss_img = loss_img.resize((self.img_size, self.img_size), Image.ANTIALIAS)
        self.loss = itk.PhotoImage(loss_img)
        # Blank img
        blank_img = Image.open('blank.png')
        blank_img = blank_img.resize((self.img_size, self.img_size), Image.ANTIALIAS)
        self.blank = itk.PhotoImage(blank_img)
        
        self.initializeDisplay()

        self.loadControlPanel()
        self.loadInfoPanel()
        self.loadVoterPanel()
        self.loadDailyVoterPanel()

        self.reset()

    def isCoordinate(self, msg):
        print(self.horzAxis)
        if self.horzAxis == ATOS:
            isMatch = re.fullmatch("^[(A-S)|(a-s)]([1-9]|([1][0-9]))$", msg)
        elif self.horzAxis == ATOT:
            isMatch = re.fullmatch("^[(A-H)|(J-T)|(a-h)|(j-t)]([1-9]|([1][0-9]))$", msg)
        if isMatch:
            return True
        else:
            return False

    def isCommand(self, msg):
        command_list = ["resign", "pass"]
        if msg in command_list:
            return True
        else:
            return False

    def getCoordsFromMsg(self, msg):
        list_coords = []
        split_msg = re.split(',|\\*|\\?|-| ', msg)
        # split_msg = msg.split(' ')
        print(split_msg)
        for m in split_msg:
            if len(m) >= 2:
                # if m[-1] == '?':
                #     m = m[0:-1]
                if self.isCoordinate(m):
                    list_coords.append(m.lower())

        return list_coords

    def reset(self):
        self.saveVoterStatsToFile()
        self.list_of_users_voted_per_move = defaultdict(list)
        self.dict = defaultdict(int)
        self.list_of_users_voted_this_turn = []
        self.total_votes = 0
        self.time_elapsed = 0
        self.turn_start_time = time.time()
        img = self.blank
        for label in self.label_list:
            label.configure(image=img)
            label.image = img
        self.updateInfoPanel()
        self.updateVoterPanel()
        self.updateDailyVoterPanel()
        print("Resetting")

    def start(self):
        self.isRunning = True
        self.addChatbotMsgToQueue("Voting has started!")

    def stop(self):
        self.isRunning = False
        self.addChatbotMsgToQueue("Voting has ended!")

    def addChatbotMsgToQueue(self, msg):
        self.chatbot_queue.put(msg)

    def getChatbotMsgFromQueue(self):
        try:
            msg = self.chatbot_queue.get(0)
            return msg
        except queue.Empty:
            return None

    def getMostVotedMove(self):
        if not self.total_votes:
            return 0
        max_value = max(self.dict.values())
        moves = [k for k,v in self.dict.items() if v == max_value]
        move = random.choice(moves)
        if self.isCoordinate(move):
            return move
        else:
            return None

    def getCoordMousePosition(self, coord):
        row, col, _ = self.getCoordRowCol(coord)
        mouse_x = self.top_left_mouse_position[0] + col * self.board_spacing
        mouse_y = self.top_left_mouse_position[1] + row * self.board_spacing
        return mouse_x, mouse_y

    def play(self):
        self.stop()
        coord = self.getMostVotedMove()
        if not coord:
            return
        mouse_x, mouse_y = self.getCoordMousePosition(coord)
        curr_x, curr_y = pyautogui.position()
        pyautogui.click(x=mouse_x, y=mouse_y)
        time.sleep(0.02)
        pyautogui.moveTo(x=curr_x, y=curr_y)
        self.isOppoTurn = True
        self.reset()
    
    def setAutomode(self):
        self.isOppoTurn = True
        self.autoMode = self.autoModeVar.get()

    def setPairGoMode(self):
        self.pairGoMode = self.pairGoModeVar.get()

    def setAlignmentMode(self):
        self.alignmentMode = self.alignmentModeVar.get()

    def setHighlightMode(self):
        self.highlightMode = self.highlightModeVar.get()

    def setGameClient(self):
        v = self.gameClientVar.get()
        self.gameClient = v
        if v == FOX:
            self.vertAxisOrder = ASCEND
            self.horzAxis = ATOS
            self.boardSize = 19
        if v == OGS:
            self.vertAxisOrder = DESCEND
            self.horzAxis = ATOT
            self.boardSize = 19
        if v == KGS:
            self.vertAxisOrder = DESCEND
            self.horzAxis = ATOT
            self.boardSize = 13
        
        

    def setColor(self):
        if self.colorVar.get():
            self.game_color = "Black"
        else:
            self.game_color = "White"

    def setTimePerMove(self, ent):
        self.time_per_turn = int(ent.get())

    def resetDailyVotes(self):
        self.daily_voters_dict = defaultdict(int)
        self.updateDailyVoterPanel()

    def loadControlPanel(self):        
        reset_button = tk.Button(self.cp, text="Reset", command=self.reset)
        start_button = tk.Button(self.cp, text="Start", command=self.start)
        stop_button = tk.Button(self.cp, text="Stop", command=self.stop)
        play_button = tk.Button(self.cp, text="Play", command=self.play)
        automode_check = tk.Checkbutton(self.cp, text="automode", variable=self.autoModeVar, command=self.setAutomode)
        pairgo_check = tk.Checkbutton(self.cp, text="pairGoMode", variable=self.pairGoModeVar, command=self.setPairGoMode)
        color_check = tk.Checkbutton(self.cp, text="isBlack?", variable=self.colorVar, command=self.setColor)
        alignmentmode_check = tk.Checkbutton(self.cp, text="alignmentMode", variable=self.alignmentModeVar, command=self.setAlignmentMode)
        highlightmode_check = tk.Checkbutton(self.cp, text="highlightMode", variable=self.highlightModeVar, command=self.setHighlightMode)
        highlightmode_check.select()
        ent_label = tk.Label(self.cp, text="Time per move: ", anchor="w")
        ent = tk.Entry(self.cp)
        ent_button = tk.Button(self.cp, text="Set time", command=(lambda e=ent: self.setTimePerMove(e)))
        reset_daily_votes_button = tk.Button(self.cp, text="Reset daily votes", command=self.resetDailyVotes)

        R1 = tk.Radiobutton(self.cp, text="Fox", variable=self.gameClientVar, value=FOX, command=self.setGameClient)
        R2 = tk.Radiobutton(self.cp, text="OGS", variable=self.gameClientVar, value=OGS, command=self.setGameClient)
        R3 = tk.Radiobutton(self.cp, text="KGS", variable=self.gameClientVar, value=KGS, command=self.setGameClient)

        reset_button.grid(column=0, row=0, sticky='w')
        start_button.grid(column=1, row=0, sticky='w')
        stop_button.grid(column=2, row=0, sticky='w')
        play_button.grid(column=3, row=0, sticky='w')

        R1.grid(row=1, column=3, sticky='w')
        R2.grid(row=2, column=3, sticky='w')
        R3.grid(row=3, column=3, sticky='w')
        
        automode_check.grid(row=1, column=0, columnspan=4, sticky='w')
        pairgo_check.grid(row=2, column=0, columnspan=4, sticky='w')
        alignmentmode_check.grid(row=3, column=0, columnspan=4, sticky='w')
        highlightmode_check.grid(row=4, column=0, columnspan=4, sticky='w')
        color_check.grid(row=4, column=0, columnspan=4, sticky='w')
        # side=tk.LEFT side=tk.RIGHT
        
        ent_label.grid(row=5, column=0, columnspan=3, sticky='w')
        ent.grid(row=5, column=3, columnspan=1, sticky='w')
        ent_button.grid(row=5, column=4, columnspan=1, sticky='w')
        reset_daily_votes_button.grid(row=6, column=0, columnspan=4, sticky='w')

    def loadInfoPanel(self):
        
        self.clock_frame = tk.Frame(self.info_panel, highlightthickness=4, highlightbackground="black")
        self.clock_frame.columnconfigure([1], minsize=60)
        # vote_label = tk.Label(self.info_panel, fg=self.grey_color, bg="black", text="Clock: ", font=self.default_font)
        vote_label = tk.Label(self.clock_frame, fg=self.grey_color, bg="black", text="Clock: ", font=self.default_font)
        self.countdown_label = tk.Label(self.clock_frame, fg=self.grey_color, bg="black", text="42", font=self.default_font)

        for i in range(self.info_show_top_n):
            coord_label = tk.Label(self.info_panel, fg=self.grey_color, bg="black", text="coord", font=self.small_font)
            num_votes_label = tk.Label(self.info_panel, fg=self.grey_color, bg="black", text=str(i), font=self.small_font)
            self.info_coord_list.append(coord_label)
            self.info_vote_list.append(num_votes_label)
            coord_label.grid(row=i+1, column=0, sticky="ew")
            num_votes_label.grid(row=i+1, column=1, sticky="ew")

        vote_label.grid(row=0, column=0, sticky="ew")
        self.countdown_label.grid(row=0, column=1, sticky="ew")
        self.clock_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

    def loadVoterPanel(self):
        title_label = tk.Label(self.voter_panel, fg=self.grey_color, bg="black", text="Top 5 (alltime)", font=self.default_font)
        for i in range(self.voter_show_top_n):
            voter_name_label = tk.Label(self.voter_panel, fg=self.grey_color, bg="black", text="coord", font=self.small_font)
            voter_votes_label = tk.Label(self.voter_panel, fg=self.grey_color, bg="black", text=str(i), font=self.small_font)
            self.top_voter_list.append(voter_name_label)
            self.voter_votes_list.append(voter_votes_label)
            voter_name_label.grid(row=i+1, column=0)
            voter_votes_label.grid(row=i+1, column=1)

        title_label.grid(row=0, column=0, columnspan=2)
    
    def loadDailyVoterPanel(self):
        title_label = tk.Label(self.daily_voter_panel, fg=self.grey_color, bg="black", text="Top 5 (daily)", font=self.default_font)
        for i in range(self.daily_voter_show_top_n):
            voter_name_label = tk.Label(self.daily_voter_panel, fg=self.grey_color, bg="black", text="coord", font=self.small_font)
            voter_votes_label = tk.Label(self.daily_voter_panel, fg=self.grey_color, bg="black", text=str(i), font=self.small_font)
            self.daily_top_voter_list.append(voter_name_label)
            self.daily_voter_votes_list.append(voter_votes_label)
            voter_name_label.grid(row=i+1, column=0)
            voter_votes_label.grid(row=i+1, column=1)

        title_label.grid(row=0, column=0, columnspan=2)

    def updateInfoPanel(self):
        self.countdown_label.configure(text=str(int(self.time_per_turn - self.time_elapsed)))
        top_coords = sorted(self.dict, key=self.dict.get, reverse=True)[:self.info_show_top_n]

        for i in range(self.info_show_top_n):
            coord_label = self.info_coord_list[i]
            num_votes_label = self.info_vote_list[i]
            try:
                coord_fill = top_coords[i]
                num_votes_fill = str(self.dict[top_coords[i]])
            except:
                coord_fill = ''
                num_votes_fill = ''

            coord_label.configure(text=coord_fill)
            num_votes_label.configure(text=num_votes_fill)

    def updateVoterPanel(self):
        top_voters = sorted(self.voters_dict, key=self.voters_dict.get, reverse=True)[:self.voter_show_top_n]

        for i in range(self.voter_show_top_n):
            voter_name_label = self.top_voter_list[i]
            voter_votes_label = self.voter_votes_list[i]
            try:
                voter_name = top_voters[i]
                voter_votes = str(self.voters_dict[voter_name])
            except:
                voter_name = ''
                voter_votes = ''

            voter_name_label.configure(text=voter_name)
            voter_votes_label.configure(text=voter_votes)

    def updateDailyVoterPanel(self):
        top_voters = sorted(self.daily_voters_dict, key=self.daily_voters_dict.get, reverse=True)[:self.daily_voter_show_top_n]

        for i in range(self.daily_voter_show_top_n):
            voter_name_label = self.daily_top_voter_list[i]
            voter_votes_label = self.daily_voter_votes_list[i]
            try:
                voter_name = top_voters[i]
                voter_votes = str(self.daily_voters_dict[voter_name])
            except:
                voter_name = ''
                voter_votes = ''

            voter_name_label.configure(text=voter_name)
            voter_votes_label.configure(text=voter_votes)

    def loadVoterStats(self):
        try:
            with open('data.txt') as json_file:
                data = json.load(json_file)
                self.voters_dict = defaultdict(int, data)
            
            with open('data_daily.txt') as json_file:
                data = json.load(json_file)
                self.daily_voters_dict = defaultdict(int, data)
        except:
            pass

    def saveVoterStatsToFile(self):
        print("Saving voter stats")
        oldDD = []
        try:
            with open('data.txt', 'w') as outfile:
                json.dump(self.voters_dict, outfile)
            with open('data_daily.txt', 'w') as outfile:
                json.dump(self.daily_voters_dict, outfile)
        except:
            pass

    def run(self):
        self.root.after(100, self.update)
        self.root.mainloop()

    def loadImages(self):
        start_ind = 30
        end_ind = 68
        while(start_ind <= end_ind):
            filename = "images/%d.png" % start_ind
            img = Image.open(filename)
            img = img.resize((self.img_size, self.img_size), Image.ANTIALIAS)
            img = itk.PhotoImage(img)
            self.list_of_images.append(img)
            start_ind += 1

    def getWeightedImage(self, weight):
        # weight is from 0 to 1
        n_shades = len(self.list_of_images)
        ind = np.round((n_shades-1) * weight)
        return self.list_of_images[int(ind)]

    def winEnumHandler(self, hwnd, ctx ):
        if win32gui.IsWindowVisible( hwnd ):
            ctx.append((hex(hwnd), win32gui.GetWindowText( hwnd )))

    def itIsOurTurn(self):
        open_windows = []
        win32gui.EnumWindows(self.winEnumHandler, open_windows)
        move = -1
        for h, title in open_windows:
            regex_res = re.findall("(?<=\[move )([0-9]*)(?=\])", title)
            if regex_res:
                move = int(regex_res[0])
        if move == -1:
            print("Move number not detected in active windows")
            return False

        if not self.pairGoMode:
            if (move % 2) == 0 and self.game_color == "Black":
                print("our turn")
                return True
            elif (move % 2) == 1 and self.game_color == "White":
                print("our turn")
                return True
            else:
                print("not our turn")
                return False
        else:
            print((move + 2) % 4)
            print((move + 1) % 4)
            if ((move + 2) % 4) == 0 and self.game_color == "Black":
                print("our turn")
                return True
            elif ((move + 1) % 4) == 0 and self.game_color == "White":
                print("our turn")
                return True
            else:
                print("not our turn")
                return False

    def initializeDisplay(self):
        for i in range(19):
            for j in range(19):
                img = self.blank
                label = tk.Label(master=self.root, bg="red", image=img, anchor="s")
                label.image = img
                label.grid(row=i, column=j, sticky="nsew")
                self.label_list.append(label)
    
    def addVote(self, user, msg):
        # Add 1 vote count to total per turn
        if user not in self.list_of_users_voted_this_turn:
            self.list_of_users_voted_this_turn.append(user)
            self.voters_dict[user] += 1
            self.daily_voters_dict[user] += 1

        # Prevent duplicate votes on same coord by same user
        key = msg.lower()
        if user not in self.list_of_users_voted_per_move[key]:
            self.list_of_users_voted_per_move[key].append(user)
            self.dict[key] += 1
            self.total_votes += 1
            print("Recorded vote for " + user + ": " + msg)

    def getCoordRowCol(self, coord):
        # subtract 1 to start at 0
        col = ord(coord[0]) - 96 - 1
        if self.horzAxis == ATOT:
            if col >= 10:
                col = col - 1

        if self.vertAxisOrder == ASCEND:
            row = int(coord[1:]) - 1
        elif self.vertAxisOrder == DESCEND:
            row = 19 - int(coord[1:])
        ind = row * 19 + col
        return row, col, ind

    def updateDisplay(self, msg):
        print("Total votes: %d" % self.total_votes)
        max_votes = max(self.dict.values())
        min_votes = min(self.dict.values())

        for key in self.dict:
            if self.isCoordinate(key):
                row, col, ind = self.getCoordRowCol(key)
                val = self.dict[key]

                if max_votes == min_votes:
                    weight = 1
                else:
                    weight = (val - min_votes) / (max_votes - min_votes)

                img = self.getWeightedImage(weight)
                label = self.label_list[ind]
                label.configure(image=img)
                label.image = img

    def updateHighlightDict(self, list_coord):
        for coord in list_coord:
            self.highlight_dict[coord] = time.time()
            print(coord)
            print("added coord")

    def updateHighlightDisplay(self):
       
        for c in list(self.highlight_dict):
            t = self.highlight_dict[c]
            row, col, ind = self.getCoordRowCol(c)
            label = self.label_list[ind]
            
            if time.time() - t > self.highlight_time_on_screen:
                img = self.blank
                del self.highlight_dict[c]
            else:
                img = self.getWeightedImage(1)

            label.configure(image=img)
            label.image = img

        # for coord in list_coord:
        #     row, col, ind = self.getCoordRowCol(coord)
        #     img = self.getWeightedImage(1)
        #     label = self.label_list[ind]
        #     label.configure(image=img)
        #     label.image = img

    def addToQueue(self, user, msg):
        if self.isRunning:
            self.queue.put((user, msg))

    def addToHighlightQueue(self, list_coord):
        if self.highlightMode and self.queueHighlight.empty() and not self.alignmentMode:
            self.queueHighlight.put(list_coord)

    def autoPlayMode(self):
        if self.isOppoTurn and self.itIsOurTurn():
            # Moment of switching states
            self.turn_start_time = time.time()
            self.isOppoTurn = False
            self.start()

        if self.itIsOurTurn():
            self.clock_frame.configure(highlightbackground="red")
            self.time_elapsed = time.time() - self.turn_start_time

            time_reminder = 5 # sec
            if self.time_per_turn - self.time_elapsed < time_reminder and not self.reminder_flag:
                self.addChatbotMsgToQueue("Voting ends in %d seconds!" % time_reminder)
                self.reminder_flag = True
            
            if self.time_elapsed > self.time_per_turn:
                # self.stop()
                self.clock_frame.configure(highlightbackground="black")
                self.play()
                self.reset()
                self.isOppoTurn = True
                self.reminder_flag = False
                time.sleep(0.1)
        else:
            self.clock_frame.configure(highlightbackground="black")

    def update(self):
        self.updateInfoPanel()
        try:
            # last_time = time.time() - self.last_highlight_time
            if self.highlightMode:
                # if last_time > self.highlight_time_on_screen + 1:
                #     self.reset()
                try: 
                    if self.alignmentMode:
                        if self.boardSize == 19:
                            if self.horzAxis == ATOS:
                                list_coord = ['d4', 'd10', 'd16', 'j4', 'j10', 'j16', 'p4', 'p10', 'p16']
                            elif self.horzAxis == ATOT:
                                list_coord = ['d4', 'd10', 'd16', 'k4', 'k10', 'k16', 'q4', 'q10', 'q16']

                        elif self.boardSize == 13:
                            list_coord = ['g7','d10','k10','k4','d4']
                    else:
                        list_coord = self.queueHighlight.get(0)
                    self.updateHighlightDict(list_coord)
                except queue.Empty:
                    pass
                self.updateHighlightDisplay()
                
                # self.last_highlight_time = time.time()

            else:
                user, msg = self.queue.get(0)
                self.addVote(user, msg)
                self.updateDisplay(msg)
        except queue.Empty:
            pass
        
        if (self.autoMode):
            self.autoPlayMode()

        self.root.after(500, self.update)