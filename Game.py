
import os, ctypes, shutil, pickle
import tkinter.font as tkFont
from csv import reader
from random import randint, choice
from math import*
from tkinter import*
from tkinter import messagebox, filedialog, colorchooser
#from winsound import*
from PIL import Image
from pygame.locals import*

import pygame as pyg

class createSprite(pyg.sprite.Sprite):
   def __init__(self, x, y, carRotate=None, image=None):
      super().__init__()
      if image != None:
         self.image = image
         if carRotate == None:
            self.rect = self.image.get_rect(x=x, y=y)
         else:
            self.rect = carRotate
      else:
         self.rect = pyg.Rect(x, y, x + 1, y + 1)
         
def getPcs():
   files = ["road.png", "turn.png","checkpoint.png", "checkpoint_active.png", "maze_grid.png", "maze_wall.png", "tree1.png", "tree2.png", "tree3.png"]
   pcs = [""]
   location = "TrackPieces/"
   for name in files:
      image = pyg.image.load(location + name)
      pcs.append(image)
   return pcs

def getSounds():
   files = ["select1.wav", "select2.wav", "gate.wav", "win.wav", "countdown.wav", "go.wav", "crash1.wav", "crash2.wav", "crash3.wav", "crash4.wav", "crash5.wav", "skid1.wav", "skid2.wav", "skid3.wav", "skid4.wav"]
   snd = []
   location = "Sound/"
   for name in files:
      sound = pyg.mixer.Sound(location + name)
      snd.append(sound)
   eng = []
   location = "Sound/Engine/"
   for engNum in range(23):
      eng.append([])
      if engNum in [0, 2, 3, 11, 12, 16]:
         soundNum = 11
      elif engNum == 1:
         soundNum = 9
      elif engNum == 4:
         soundNum = 8
      elif engNum == 5:
         soundNum = 2
      elif engNum in [6, 7, 9, 14, 15]:
         soundNum = 5
      elif engNum == 8:
         soundNum = 3
      elif engNum == 10:
         soundNum = 4
      elif engNum == 13:
         soundNum = 6
      else:
         soundNum = 0
      for engPitch in range(soundNum):
         sound = pyg.mixer.Sound(location + str(engNum) + "-" + str(engPitch) + ".wav")
         eng[engNum].append(sound)
   return snd, eng

def invertCol(red, green, blue):
   rgb = (red * 0.299) + (green * 0.587) + (blue * 0.114)
   if rgb > 186:
      return 0, 0, 0
   else:
      return 255, 255, 255
   
def getFont(size, for_tk=False):
    key = (size, for_tk)
    if key not in _font_cache:
        if for_tk:
            _font_cache[key] = tkFont.Font(family="Arial", size=size)
        else:
            _font_cache[key] = pyg.font.Font("assets/font.ttf", size)
    return _font_cache[key]

def mainMenu(win, level, cam):
   global menuMode
   pyg.mixer.Channel(2).stop()
   drawLevel(win, level, cam, True)
   r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
   r1, g1, b1 = invertCol(r, g, b)
   closeButton(win, [r, g, b])
   if menuMode not in ["TITLE_SCREEN", "MAIN_MENU"]:
      backButton(win, [r, g, b])
   if menuMode == "TITLE_SCREEN":
      font = getFont(100)
      centerTextScreen(win, font, "Car Mania", 20, r, g, b)
      font = getFont(30)
      menuButton(win, font, halfScreen[0], screen[1] - 340, "Login", r, g, b, True,"LOGIN_PAGE")
      menuButton(win, font, halfScreen[0], screen[1] - 270, "Play as Guest", r, g, b, False,"GUEST_ACCOUNT")
      menuButton(win, font, halfScreen[0], screen[1] - 200, "Instructions", r, g, b, True,"INSTRUCTIONS")
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Credits", r, g, b, True,"CREDITS")
   elif menuMode == "LOGIN_PAGE":
      font = getFont(100)
      centerTextScreen(win, font, "Login", 20, r, g, b)
      font = getFont(30)
      bg = pyg.Surface((screen[0], 240))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (0, 200))
      centerTextScreen(win, font, "Enter your username and password to continue.", 200, r, g, b)
      centerTextScreen(win, font, "You can also create an account if you do not have one.", 230, r, g, b)
      centerTextScreen(win, font, "Be aware that if you forget your password, your account cannot be restored.", 260, r, g, b)
      centerTextScreen(win, font, "Alternatively, you can play as a guest.", 320, r, g, b)
      centerTextScreen(win, font, "This is intended for those that do not want the game to keep their data.", 350, r, g, b)
      centerTextScreen(win, font, "To do this, go back to the previous menu and click \"Play as Guest\".", 380, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 200, "Enter Details", r, g, b, False,"ENTER_DETAILS")
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Create Account", r, g, b, False,"CREATE_ACCOUNT")
   elif menuMode == "INSTRUCTIONS":
      font = getFont(100)
      centerTextScreen(win, font, "Gameplay Instructions", 20, r, g, b)
      font = getFont(30)
      bg = pyg.Surface((screen[0], 450))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (0, 200))
      centerTextScreen(win, font, "Welcome to Car Mania!", 200, r, g, b)
      centerTextScreen(win, font, "This is a sandbox game that allows you to create and play with two-dimensional cars and tracks.", 260, r, g, b)
      centerTextScreen(win, font, "To win a level, you must focus on staying on the road and pass all checkpoints in the level.", 290, r, g, b)
      centerTextScreen(win, font, "Do not miss a checkpoint otherwise you cannot complete a lap.", 320, r, g, b)
      centerTextScreen(win, font, "The game encourages you to express your creativity by creating cars and levels.", 350, r, g, b)
      centerTextScreen(win, font, "The controls of the gameplay are similar to those of a traditional car racing game:", 410, r, g, b)
      centerTextScreen(win, font, "Use the arrow keys or WASD to move your car around.", 440, r, g, b)
      centerTextScreen(win, font, "Use the SPACE key to apply the brakes and slow your car down.", 470, r, g, b)
      centerTextScreen(win, font, "Use the ENTER key to pause the game.", 500, r, g, b)
      centerTextScreen(win, font, "You can drive in the main menu to practice these skills.", 560, r, g, b)
      centerTextScreen(win, font, "Good luck!", 590, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Done", r, g, b, True,"TITLE_SCREEN")
   elif menuMode == "CREDITS":
      font = getFont(100)
      centerTextScreen(win, font, "Credits", 20, r, g, b)
      font = getFont(30)
      bg = pyg.Surface((screen[0], 290))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (0, 200))
      centerTextScreen(win, font, "Programming and game design done by Harish Menon", 200, r, g, b)
      centerTextScreen(win, font, "\"Quick Silver\", trees and roads done by Patrick Bozetarnik", 260, r, g, b)
      centerTextScreen(win, font, "\"Twist and Turns\" and the corresponing soundtrack done by Anjelee Menon", 290, r, g, b)
      centerTextScreen(win, font, "Car drawings done by Anjelee Menon and Taro Bamps", 320, r, g, b)
      centerTextScreen(win, font, "Soundtrack obtained from ModArchive.org", 380, r, g, b)
      centerTextScreen(win, font, "Sound effects and engine sounds are obtained from \"The Vehicular Epic\"", 410, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Done", r, g, b, True,"TITLE_SCREEN")
   elif menuMode == "MAIN_MENU":
      bg = pyg.Surface((1000, 90))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (460, 150))
      font = getFont(100)
      centerTextScreen(win, font, "Car Mania", 20, r, g, b)
      font = getFont(30)
      centerTextScreen(win, font, "Welcome " + username + "!", 150, r, g, b)
      centerTextScreen(win, font, "Note: You can either play with the default set of cars/levels or create your own!", 190, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 410, "Play Game", r, g, b, False,"GET_CARS_DEFAULT")
      menuButton(win, font, halfScreen[0], screen[1] - 340, "Car Creator", r, g, b, True,"CAR_CREATOR_MENU")
      menuButton(win, font, halfScreen[0], screen[1] - 270, "Level Creator", r, g, b, True,"LEVEL_CREATOR_MENU")
      menuButton(win, font, halfScreen[0], screen[1] - 200, "Options", r, g, b, False,"MENU_OPTIONS")
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Sign Out", r, g, b, True,"TITLE_SCREEN")
   elif menuMode == "CAR_CREATOR_MENU":
      font = getFont(100)
      centerTextScreen(win, font, "Car Creator Menu", 20, r, g, b)
      font = getFont(30)
      menuButton(win, font, halfScreen[0], screen[1] - 270, "Create Car", r, g, b, False,"CREATE_CAR_DIRECTORY")
      menuButton(win, font, halfScreen[0], screen[1] - 200, "Edit Car", r, g, b, False,"EDIT_CAR")
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Instructions", r, g, b, True,"CAR_CREATOR_INSTRUCTIONS")
   elif menuMode == "CAR_CREATOR_INSTRUCTIONS":
      font = getFont(100)
      centerTextScreen(win, font, "Car Creator Instructions", 20, r, g, b)
      font = getFont(30)
      bg = pyg.Surface((screen[0], 320))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (0, 200))
      centerTextScreen(win, font, "The car creator has two sections:", 200, r, g, b)
      centerTextScreen(win, font, "The first section will ask you to import a car image.", 230, r, g, b)
      centerTextScreen(win, font, "Keep in mind to have an aerial image of a car facing north (preferably with resolution 190x350) in JPEG or PNG format.", 260, r, g, b)
      centerTextScreen(win, font, "The second section will let you set the car's name & performance.", 320, r, g, b)
      centerTextScreen(win, font, "This consists of Top Speed, Acceleration, Handling and Offroad.", 350, r, g, b)
      centerTextScreen(win, font, "You can also set the engine type of the car and test how the car will sound.", 380, r, g, b)
      centerTextScreen(win, font, "Good luck creating cars!", 440, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Done", r, g, b, True,"CAR_CREATOR_MENU")
   elif menuMode == "LEVEL_CREATOR_MENU":
      font = getFont(100)
      centerTextScreen(win, font, "Level Creator Menu", 20, r, g, b)
      font = getFont(30)
      menuButton(win, font, halfScreen[0], screen[1] - 270, "Create Level", r, g, b, False,"LEVEL_CREATOR_RESET")
      menuButton(win, font, halfScreen[0], screen[1] - 200, "Edit Level", r, g, b, False,"EDIT_LEVEL")
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Instructions", r, g, b, True,"LEVEL_CREATOR_INSTRUCTIONS")
   elif menuMode == "LEVEL_CREATOR_INSTRUCTIONS":
      font = getFont(100)
      centerTextScreen(win, font, "Level Creator Instructions", 20, r, g, b)
      font = getFont(30)
      bg = pyg.Surface((screen[0], 520))
      bg.set_alpha(175)
      bg.fill((r1, g1, b1))
      win.blit(bg, (0, 200))
      centerTextScreen(win, font, "The main screen of the level creator consists of the editor that you can use to make the level.", 200, r, g, b)
      centerTextScreen(win, font, "Use \"Type\" and \"Rotate\" to change the track piece and rotation respectively.", 230, r, g, b)
      centerTextScreen(win, font, "The track piece on the left hand side can be selected by clicking on it using the mouse pointer.", 260, r, g, b)
      centerTextScreen(win, font, "This can then be placed anywhere within the editor.", 290, r, g, b)
      centerTextScreen(win, font, "If you make a mistake, you can use the \"Undo\" feature.", 320, r, g, b)
      centerTextScreen(win, font, "The \"Redo\" feature will bring back any pieces that were undone.", 350, r, g, b)
      centerTextScreen(win, font, "The \"Advanced Properties\" consists of a couple of options.", 410, r, g, b)
      centerTextScreen(win, font, "There are options to set the name, number of laps and colour of a level.", 440, r, g, b)
      centerTextScreen(win, font, "The code on the right hand side of the advanced properties is an alternative method of editing a level rather than using the editor.", 470, r, g, b)
      centerTextScreen(win, font, "More information towards editing a level using code can be found within the advanced properties,", 500, r, g, b)
      centerTextScreen(win, font, "You can optionally set music to play in the background of a level.", 530, r, g, b)
      centerTextScreen(win, font, "If you are using this option, make sure to have a music file in WAV format preferably with 48000 Hz as the frequency.", 560, r, g, b)
      centerTextScreen(win, font, "For this to work, the WAV file must be 16-bit or lower.", 590, r, g, b)
      centerTextScreen(win, font, "Good luck creating levels!", 650, r, g, b)
      menuButton(win, font, halfScreen[0], screen[1] - 130, "Done", r, g, b, True,"LEVEL_CREATOR_MENU")

def carCreator(win):
   global levelProperties, carCreatorProperties, angle
   r = levelProperties["Colour"][level][0]
   g = levelProperties["Colour"][level][1]
   b = levelProperties["Colour"][level][2]
   win.fill((r, g ,b))
   r1, g1, b1 = invertCol(r, g, b)
   r2, g2, b2 = invertCol(r1, g1, b1)
   closeButton(win, [r1, g1, b1])
   backButton(win, [r1, g1, b1])
   font = getFont(100)
   centerTextScreen(win, font, carCreatorProperties["Name"], 10, r1, g1, b1)
   font = getFont(30)
   if carCreatorProperties["Image"] != None:
      angle += 1
      if angle == 360:
         angle = 0
      x = halfScreen[0] - 100
      y = halfScreen[1] - 300
      rotate, carRect = rotateCenter(x, y, carCreatorProperties["Image"], angle)
      carSprite = createSprite(x, y, carRect, rotate)
      allSprites = pyg.sprite.Group([carSprite])
      allSprites.draw(win)
   menuButton(win, font, halfScreen[0], screen[1] - 200, "Import Image", r1, g1, b1, False,"IMPORT_IMAGE")
   menuButton(win, font, halfScreen[0], screen[1] - 130, "Car Properties", r1, g1, b1, False,"CAR_OPTIONS")
   centerTextScreen(win, font, "For best results, import an image of a car from aerial view, facing north, with a resolution around (190x350)", screen[1] - 50, r1, g1, b1)
   font = getFont(20)
   size = 600
   x = halfScreen[0] - (size / 2)
   y = screen[1] - 360
   gap = 30
   textY = 8
   pyg.draw.rect(win, (0, 200, 0), (x + 2, y + 2, (carCreatorProperties["TopSpeed"] / 40) * size, 18), 0)
   pyg.draw.rect(win, (r1, g1, b1), (x, y, size + 2, 20), 2)
   if units == "METRIC":
      speed = str(carCreatorProperties["TopSpeed"] * 25) + " kph"
   else:
      speed = str(round(carCreatorProperties["TopSpeed"] * 25 / 1.609344)) + " mph"
   centerTextScreen(win, font, "Top Speed: " + speed, y - textY, r1, g1, b1)
   pyg.draw.rect(win, (0, 150, 200), (x + 2, y + gap + 2, (carCreatorProperties["Acceleration"] / 10) * size, 18), 0)
   pyg.draw.rect(win, (r1, g1, b1), (x, y + gap + 2, size + 2, 20), 2)
   centerTextScreen(win, font, "Acceleration: " + str(carCreatorProperties["Acceleration"]) + " units", y + gap - textY, r1, g1, b1)
   pyg.draw.rect(win, (200, 0, 0), (x + 2, y + (gap * 2) + 2, (carCreatorProperties["Handling"] / 30) * size, 18), 0)
   pyg.draw.rect(win, (r1, g1, b1), (x, y + (gap * 2), size + 2, 20), 2)
   centerTextScreen(win, font, "Handling: " + str(carCreatorProperties["Handling"]) + " units", y + (gap * 2) - textY, r1, g1, b1)
   pyg.draw.rect(win, (150, 150, 150), (x + 2, y + (gap * 3) + 2, (carCreatorProperties["Offroad"] / 5) * size, 18), 0)
   pyg.draw.rect(win, (r1, g1, b1), (x, y + (gap * 3), size + 2, 20), 2)
   centerTextScreen(win, font, "Offroad: " + str(carCreatorProperties["Offroad"]) + " units", y + (gap * 3) - textY, r1, g1, b1)

def importImage(location=""):
   global carCreatorProperties, editCarCreator
   if location == "":
      fakeWin = Tk()
      fakeWin.withdraw()
      location = filedialog.askopenfilename(title="Select Car Image", filetypes=(("JPG/PNG","*.jpg"), ("JPG/PNG","*.png")))
      closeTk(fakeWin)
   if location != "":
      if editCarCreator == False:
         name = location.split("/")[len(location.split("/")) - 1]
         extension = os.path.splitext(location)[1]
         carLocation = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"] + "/"
         if name not in ["car.png", "car.jpg", "tempcar.png", "tempcar.jpg"]:
            shutil.copy(location, carLocation)
            if extension == ".jpg":
               convert = Image.open(carLocation + name)
               try:
                  convert.save(carLocation + "tempcar.png")
               except FileExistsError:
                  os.remove(carLocation + "tempcar.png")
                  convert.save(carLocation + "tempcar.png")
               os.remove(carLocation + name)
            else:
               try:
                  os.rename(carLocation + name, carLocation + "tempcar.png")
               except FileExistsError:
                  os.remove(carLocation + "tempcar.png")
                  os.rename(carLocation + name, carLocation + "tempcar.png")
         else:
            fakeWin = Tk()
            fakeWin.withdraw()
            messagebox.showerror("Error importing image", "The name of the file interferes with the game\nPlease rename the file")
            closeTk(fakeWin)
            return None
      return pyg.image.load(location)
   else:
      return carCreatorProperties["Image"]

def levelCreator(win, cam):
   global levelCreatorProperties, camera, velocity, angle, menuMode, activeGate, sounds
   r = levelCreatorProperties["Colour"][0]
   g = levelCreatorProperties["Colour"][1]
   b = levelCreatorProperties["Colour"][2]
   win.fill((r, g ,b))
   sprites = []
   gateSprites = []
   for line in levelCreatorProperties["Code"]:
      if line != "":
         if line[0] == "road":
            typ = int(line[1])
            ang = int(line[4])
            img = pieces[typ] 
            x = int(line[2])
            y = -int(line[3])
            rotate = pyg.transform.rotate(img, ang)
         elif line[0] == "gate":
            ang = int(line[4])
            cpOrder = int(line[1])
            img = pieces[3]
            x = int(line[2])
            y = -int(line[3])
            rotate = pyg.transform.rotate(img, ang)
         elif line[0] == "tree":
            typ = int(line[1])
            img = pieces[typ + 6]
            x = int(line[2])
            y = -int(line[3])
            rotate = img
         gateSprites.append(createSprite(x + cam[0] - ((screen[0] // 5) - 20), y + cam[1] - ((halfScreen[1]) - 220), image=rotate))
      sprites.append(createSprite(x + cam[0] - ((screen[0] // 5) - 20), y + cam[1] - ((halfScreen[1]) - 220), image=rotate))
   combinedGateSprites = pyg.sprite.Group(gateSprites)
   allSprites = pyg.sprite.Group(sprites + gateSprites)
   allSprites.draw(win)
   r1, g1, b1 = invertCol(r, g, b)
   r2, g2, b2 = invertCol(r1, g1, b1)
   title = pyg.Surface((screen[0], 120))
   title.set_alpha(150)
   title.fill((r1, g1, b1))
   win.blit(title, (0, 0))
   font = getFont(100)
   centerTextScreen(win, font, levelCreatorProperties["Name"], 10, r2, g2, b2)
   font = getFont(30)
   panel = pyg.Surface((screen[0]//5, screen[1] - 120))
   panel.set_alpha(150)
   panel.fill((r1, g1, b1))
   win.blit(panel, (0, 120))
   img = pieces[levelCreatorProperties["Type"]]
   rotate = pyg.transform.rotate(img, levelCreatorProperties["Angle"])
   pickUpSprite = []
   pointer = createSprite(mousePos[0], mousePos[1])
   positionX = screen[0] // 13
   positionY = 200
   if levelCreatorProperties["Type"] == 1 and levelCreatorProperties["Angle"] == 90:
      positionX -= 100
   if levelCreatorProperties["Type"] == 3:
      positionY += 100
      if levelCreatorProperties["Angle"] == 90:
         positionX += 50
   pieceSelect = createSprite(positionX, positionY, image=rotate)
   pickUpSprite.append(pieceSelect)
   group = pyg.sprite.Group(pickUpSprite)
   group.draw(win)
   mouseTouch = pyg.sprite.spritecollide(pointer, group, False)
   centX = (((screen[0] - (screen[0] // 5)) // 2) - 20) - cam[0]
   centY = (((screen[1] - (screen[1] // 5)) // 2) + 8) - cam[1]
   xPos = (centX + (mousePos[0] - (screen[0]//5)))
   yPos = (-(centY + mousePos[1] - 120))
   for touch in mouseTouch:
      if clicked[0] == 1 and mouseDown:
         playSound(sounds[1])
         if levelCreatorProperties["PieceSelected"] == False:
            levelCreatorProperties["PieceSelected"] = True
         else:
            levelCreatorProperties["PieceSelected"] = False
         pyg.time.wait(200)
   if levelCreatorProperties["PieceSelected"]:
      rotate = pyg.transform.rotate(img, levelCreatorProperties["Angle"])
      win.blit(rotate, (mousePos[0], mousePos[1])) 
   if levelCreatorProperties["PieceSelected"] and (clicked[0] == 1 and mouseDown) and (mousePos[0] > screen[0]//5 and mousePos[1] > 120):
      playSound(sounds[1])
      levelCreatorProperties["Undo"] = []
      if levelCreatorProperties["Type"] in [1, 2]:
         levelCreatorProperties["Code"].append(["road", levelCreatorProperties["Type"], round(xPos), round(yPos), levelCreatorProperties["Angle"]])
      elif levelCreatorProperties["Type"] == 3:
         levelCreatorProperties["Code"].append(["gate", int(activeGate), round(xPos), round(yPos), levelCreatorProperties["Angle"]])
         activeGate += 1
      elif levelCreatorProperties["Type"] in [7, 8, 9]:
         levelCreatorProperties["Code"].append(["tree", levelCreatorProperties["Type"] - 6, round(xPos), round(yPos)])
      pyg.time.wait(200)
   if menuMode == "UNDO_PIECE":
      if len(levelCreatorProperties["Code"]) != 1:
         removedCode = levelCreatorProperties["Code"].pop(len(levelCreatorProperties["Code"]) - 1)
         levelCreatorProperties["Undo"].append(removedCode)
         if removedCode[0] == "gate":
            activeGate = int(removedCode[1])
      menuMode = "LEVEL_CREATOR_MENU"
   elif menuMode == "REDO_PIECE":
      if len(levelCreatorProperties["Undo"]) != 0:
         addedCode = levelCreatorProperties["Undo"].pop(len(levelCreatorProperties["Undo"]) - 1)
         levelCreatorProperties["Code"].append(addedCode)
         if addedCode[0] == "gate":
            activeGate = int(addedCode[1]) + 1
      menuMode = "LEVEL_CREATOR_MENU"
   if levelCreatorProperties["Type"] == 1:
      centerTextPanel(win, font, "Road", screen[0]//10, 130, r2, g2, b2)
   elif levelCreatorProperties["Type"] == 2:
      centerTextPanel(win, font, "Turn", screen[0]//10, 130, r2, g2, b2)
   elif levelCreatorProperties["Type"] == 3:
      centerTextPanel(win, font, "Checkpoint Gate", screen[0]//10, 130, r2, g2, b2)
   elif levelCreatorProperties["Type"] in [7, 8, 9]:
      centerTextPanel(win, font, "Tree", screen[0]//10, 130, r2, g2, b2)
   arrowButton(win, [r1, g1, b1], [r2, g2, b2], 30, 520, "BACK")
   arrowButton(win, [r1, g1, b1], [r2, g2, b2], 310, 520, "NEXT")
   centerTextPanel(win, font, "Type", screen[0]//10, 530, r2, g2, b2)
   if levelCreatorProperties["Type"] not in [7, 8, 9]:
      arrowButton(win, [r1, g1, b1], [r2, g2, b2], 30, 590, "ACW")
      arrowButton(win, [r1, g1, b1], [r2, g2, b2], 310, 590, "CW")
      centerTextPanel(win, font, "Rotate", screen[0]//10, 600, r2, g2, b2)
   font = getFont(20)
   menuButton(win, font, screen[0]//10, 670, "Undo", r2, g2, b2, True,"UNDO_PIECE")
   menuButton(win, font, screen[0]//10, 740, "Redo", r2, g2, b2, True,"REDO_PIECE")
   menuButton(win, font, screen[0]//10, 810, "Advanced Properties", r2, g2, b2, False,"LEVEL_OPTIONS")
   centerTextPanel(win, font, "Use the arrow keys to move around", screen[0]//10, screen[1] - 170, r2, g2, b2)
   centerTextPanel(win, font, "Select/Deselect a piece by clicking", screen[0]//10, screen[1] - 130, r2, g2, b2)
   centerTextPanel(win, font, "on the piece in the top left corner", screen[0]//10, screen[1] - 110, r2, g2, b2)
   centerTextPanel(win, font, "Place it anywhere in the level editor ", screen[0]//10, screen[1] - 70, r2, g2, b2)
   drawText(win, font, "Camera X: " + str(int(centX)), screen[0]//50, screen[1] - 40, r2, g2, b2)
   drawText(win, font, "Camera Y: " + str(int(centY)), screen[0]//50, screen[1] - 20, r2, g2, b2)
   drawText(win, font, "Mouse X: " + str(round(xPos)), screen[0]//50 + 200, screen[1] - 40, r2, g2, b2)
   drawText(win, font, "Mouse Y: " + str(round(yPos)), screen[0]//50 + 200, screen[1] - 20, r2, g2, b2)
   closeButton(win, [r2, g2, b2])
   backButton(win, [r2, g2, b2])
   ##
   if key["Left"] or key["A"]:
      camera[0] += 10
   if key["Right"] or key["D"]:
      camera[0] -= 10
   if key["Up"] or key["W"]:
      camera[1] += 10
   if key["Down"] or key["S"]:
      camera[1] -= 10

def rebuildMaze():
   global randomGates
   randomGates = []
   for line in levelProperties["Code"][5]:
      if line[0] == "maze":
         sizeX = int(line[1])
         sizeY = int(line[2])
         grid = []
         for row in range(0, sizeX):
            for column in range(0, sizeY):     
               grid.append((200 * row, 200 * column))
         walls = {"Right" : [], "Left" : [], "Up" : [], "Down" : []}
         visited = []
         stack = []
         startPos = [randint(0, sizeX) * 200, randint(0, sizeY) * 200]
         walls = generateMaze(grid, stack, visited, startPos)
      elif line[0] == "gate":
         x = (randint(0, sizeX) * 200) + 50
         y = (randint(0, sizeY) * 200) + 50
         randomGates.append((x, y))
   return walls, randomGates

def generateMaze(grid, stack, visited, pos):
   stack.append(pos)
   visited.append(pos)
   wallRemove = {"Right" : [], "Left" : [], "Up" : [], "Down" : []}
   while len(stack) > 0:
      directions = []
      if (pos[0] + 200, pos[1]) not in visited and (pos[0] + 200, pos[1]) in grid:
         directions.append("RIGHT")
      if (pos[0] - 200, pos[1]) not in visited and (pos[0] - 200, pos[1]) in grid:
         directions.append("LEFT")
      if (pos[0], pos[1] + 200) not in visited and (pos[0], pos[1] + 200) in grid:
         directions.append("DOWN")
      if (pos[0], pos[1] - 200) not in visited and (pos[0], pos[1] - 200) in grid:
         directions.append("UP")
      if len(directions) > 0:
         neighbour = choice(directions)
         if neighbour == "RIGHT":
            wallRemove["Right"].append((pos[0] + 200, pos[1]))
            grid.remove((pos[0] + 200, pos[1]))
            pos[0] = pos[0] + 200
            visited.append((pos[0], pos[1]))
            stack.append((pos[0], pos[1]))
         elif neighbour == "LEFT":
            wallRemove["Left"].append((pos[0] - 200, pos[1]))
            grid.remove((pos[0] - 200, pos[1]))
            pos[0] = pos[0] - 200
            visited.append((pos[0], pos[1]))
            stack.append((pos[0], pos[1]))
         elif neighbour == "DOWN":
            wallRemove["Down"].append((pos[0], pos[1] + 200))
            grid.remove((pos[0], pos[1] + 200))
            pos[1] = pos[1] + 200
            visited.append((pos[0], pos[1]))
            stack.append((pos[0], pos[1]))
         elif neighbour == "UP":
            wallRemove["Up"].append((pos[0], pos[1] - 200))
            grid.remove((pos[0], pos[1] - 200))
            pos[1] = pos[1] - 200
            visited.append((pos[0], pos[1]))
            stack.append((pos[0], pos[1]))
      else:
         pos[0], pos[1] = stack.pop()
   return wallRemove

def rotateCenter(x, y, image, angle):
   rect = image.get_rect(x=x, y=y)
   center = rect.center
   rotate = pyg.transform.rotate(image, angle)
   newRect = rotate.get_rect(x=x, y=y, center=center)
   return rotate, newRect

def drawTrack(win, lv, cam, move=False, scaleFactor=1):
   global carProperties, levelProperties, activeGate, gatesCleared, currentLap, walls, sounds, mode, gateSprites, randomGates
   win.fill((levelProperties["Colour"][lv][0], levelProperties["Colour"][lv][1], levelProperties["Colour"][lv][2]))
   sprites = {"Road" : [], "Tree" : [], "Maze" : {"Road" : [], "Horizontal" : [], "Vertical" : []}}
   gateSprites = []
   rndGate = 0
   for line in levelProperties["Code"][lv]:
      if line[0] == "road":
         typ = int(line[1])
         ang = int(line[4])
         img = pieces[typ]
         if scaleFactor != 1:
            width, height = img.get_size()
            resizedWidth = width // scaleFactor
            x = int(line[2]) // scaleFactor
            y = -int(line[3]) // scaleFactor
            widthPercent = resizedWidth / float(width)
            heightSize = int((float(height) * float(widthPercent)))
            resize = pyg.transform.scale(img, (resizedWidth, heightSize))
            rotate = pyg.transform.rotate(resize, ang)
         else:
            x = int(line[2])
            y = -int(line[3])
            rotate = pyg.transform.rotate(img, ang)
         sprites["Road"].append(createSprite(x + cam[0], y + cam[1], image=rotate))
      elif line[0] == "gate":
         ang = int(line[4])
         cpOrder = int(line[1])
         if cpOrder == activeGate:
            img = pieces[4]
         else:
            img = pieces[3]
         if scaleFactor != 1:
            width, height = img.get_size()
            resizedWidth = width // scaleFactor
            if level != 5:
               x = int(line[2]) // scaleFactor
               y = -int(line[3]) // scaleFactor
            else:
               x = randomGates[rndGate][0]
               y = randomGates[rndGate][1]
            widthPercent = resizedWidth / float(width)
            heightSize = int((float(height) * float(widthPercent)))
            resize = pyg.transform.scale(img, (resizedWidth, heightSize))
            rotate = pyg.transform.rotate(resize, ang)
         else:
            if level != 5:
               x = int(line[2])
               y = -int(line[3])
            else:
               x = randomGates[rndGate][0]
               y = randomGates[rndGate][1]
            rotate = pyg.transform.rotate(img, ang)
         gateSprites.append(createSprite(x + cam[0], y + cam[1], image=rotate))
         rndGate += 1
      elif line[0] == "tree":
         typ = int(line[1])
         img = pieces[typ + 6]
         if scaleFactor != 1:
            width, height = img.get_size()
            resizedWidth = width // scaleFactor
            x = int(line[2]) // scaleFactor
            y = -int(line[3]) // scaleFactor
            widthPercent = resizedWidth / float(width)
            heightSize = int((float(height) * float(widthPercent)))
            resize = pyg.transform.scale(img, (resizedWidth, heightSize))
            sprites["Tree"].append(createSprite(x + cam[0], y + cam[1], image=resize))
         else:
            x = int(line[2])
            y = -int(line[3])
            sprites["Tree"].append(createSprite(x + cam[0], y + cam[1], image=img))
      elif line[0] == "maze":
         sizeX = int(line[1])
         sizeY = int(line[2])
         imgGrid = pieces[5]
         imgRoadH = pieces[6]
         imgRoadV = pyg.transform.rotate(imgRoadH, 90)
         for row in range(-1, sizeX + 1):
            for column in range(-1, sizeY + 1):     
               sprites["Maze"]["Road"].append(createSprite((200 * row) + cam[0], (200 * column) + cam[1], image=imgGrid))
         for i in walls["Right"]:
            sprites["Maze"]["Horizontal"].append(createSprite(i[0] + cam[0], i[1] + cam[1], image=imgRoadH))
         for i in walls["Left"]:
            sprites["Maze"]["Horizontal"].append(createSprite(i[0] + cam[0], i[1] + cam[1], image=imgRoadH))
         for i in walls["Up"]:
            sprites["Maze"]["Vertical"].append(createSprite(i[0] + cam[0], i[1] + cam[1], image=imgRoadV))
         for i in walls["Down"]:
            sprites["Maze"]["Vertical"].append(createSprite(i[0] + cam[0], i[1] + cam[1], image=imgRoadV))
   collisionSprites = sprites["Maze"]["Horizontal"] + sprites["Maze"]["Vertical"] + sprites["Tree"]
   roadSprites = sprites["Road"] + sprites["Maze"]["Road"]
   if mode not in ["LEVEL_SELECT_DEFAULT", "LEVEL_SELECT_USERNAME"]:
      x = halfScreen[0]
      y = halfScreen[1]
   else:
      x = 0 + cam[0]
      y = 0 + cam[1]
   image = carProperties["Image"][car]
   width, height = image.get_size()
   resizedWidth = (width // 5) // scaleFactor
   widthPercent = resizedWidth / float(width)
   heightSize = int((float(height) * float(widthPercent)))
   resize = pyg.transform.scale(image, (resizedWidth, heightSize))
   rotate, carRect = rotateCenter(x, y, resize, -angle)
   carSprite = createSprite(x, y, carRotate=carRect, image=rotate)
   roadTouch = pyg.sprite.spritecollideany(carSprite, roadSprites, None)
   collide = pyg.sprite.spritecollideany(carSprite, collisionSprites, None)
   roadSprites.append(carSprite)
   roadSprites = roadSprites + gateSprites
   allSprites = pyg.sprite.Group(roadSprites)
   allSprites.draw(win)
   allSprites = pyg.sprite.Group(collisionSprites)
   allSprites.draw(win)
   if carSprite.rect.colliderect(gateSprites[activeGate].rect):
      playSound(sounds[2])
      activeGate += 1
      gatesCleared += 1
      if activeGate == len(gateSprites):
         activeGate = 0
         currentLap += 1
         if currentLap == int(levelProperties["Laps"][lv]) + 1:
            playSound(sounds[3])
   if collide != None:
      return "COLLIDE"
   if roadTouch == None:
      return "OFFROAD"
   else:
      return "ROAD"
     
def drawLevel(win, level, cam, move):
   onTrack = drawTrack(win, level, cam, move)
   #Car
   global camera, velocity, angle, carProperties, car
   #Physics
   if onTrack in ["ROAD", "COLLIDE"]:
      altered_speed = carProperties["Speed"][car]
      altered_acceleration = carProperties["Acceleration"][car]
   else:
      altered_speed = carProperties["Offroad"][car]
      altered_acceleration = carProperties["Acceleration"][car] / 5
   handling = carProperties["Handling"][car]
   if move:
     playEngineSound(carProperties["Engine"][car], abs(velocity))
     if key["Up"] or key["W"]:
         velocity += altered_acceleration / 100
     else:
         if velocity > 0:
             velocity -= 5 / 1000
     if key["Down"] or key["S"]:
         velocity -= altered_acceleration / 100
     else:
         if velocity < 0:
             velocity += altered_acceleration / 1000
     if velocity > 2.5 or velocity < -2.5:
         if key["Left"] or key["A"]:
             playSound(sounds[randint(11, 14)], channel=4)
             angle -= handling / velocity
         if key["Right"] or key["D"]:
             playSound(sounds[randint(11, 14)], channel=4)
             angle += handling / velocity
     elif velocity > 0.05 or velocity < -0.05:
        if velocity > 0.05:
           if key["Left"] or key["A"]:
              playSound(sounds[randint(11, 14)], channel=4)
              angle -= handling / 5
           if key["Right"] or key["D"]:
              playSound(sounds[randint(11, 14)], channel=4)
              angle += handling / 5
        elif velocity < -0.05:
           if key["Left"] or key["A"]:
              playSound(sounds[randint(11, 14)], channel=4)
              angle += handling / 5
           if key["Right"] or key["D"]:
              playSound(sounds[randint(11, 14)], channel=4)
              angle -= handling / 5
     if key["Space"]:
         if velocity > 0:
             velocity -= altered_acceleration / 50
         if velocity < 0:
             velocity += altered_acceleration / 50
     if velocity > altered_speed:
         if onTrack in ["ROAD", "COLLIDE"]:
             velocity -= altered_acceleration / 100
         else:
             velocity -= (altered_acceleration / 100) * 10
     if velocity < -altered_speed / 3:
         if onTrack in ["ROAD", "COLLIDE"]:
             velocity += altered_acceleration / 100
         else:
             velocity += (altered_acceleration / 100) * 10
     if onTrack == "COLLIDE":
        if not -1.5 <= velocity <= 1.5:
           playSound(sounds[randint(6, 10)], channel=3)
           if velocity > 0:
              velocity = -1.5
           elif velocity < 0:
              velocity = 1.5
   camera[0] += velocity * sin(radians(-angle))
   camera[1] += velocity * cos(radians(angle))

def playEngineSound(typ, speed):
   global carProperties, engines, enginePitch, keys, velocity
   carGears = carProperties["Speed"][car] / len(engines[typ])
   if 0.1 <= speed <= 0.2:
      pyg.mixer.Channel(1).play(engines[typ][0], loops=-1)
   if ((key["Up"] or key["W"]) and velocity > 0) or ((key["Down"] or key["S"]) and velocity < 0):
      for i in range(1, len(engines[typ])):
         if carGears * i <= speed <= carGears * i + 0.1:
            pyg.mixer.Channel(1).play(engines[typ][i], loops=-1)
            enginePitch = i
   else:
      for i in range(1, len(engines[typ])):
         if carGears * i <= speed <= carGears * i + 0.1:
            pyg.mixer.Channel(1).play(engines[typ][0], loops=-1)
            enginePitch = i
         
def getLevels(account, mde, load=False):
   location = "UserData/" + account + "/Levels/"
   if account == "Default":
      lvNum = getLvNum(location + "Code/")
      properties = {"Name" : [""], "Colour" : [[0 for i in range(3)] for j in range(lvNum + 1)], "Code" : [[[""]] for i in range(lvNum + 1)], "Music" : [], "Laps" : [0], "Gates" : [0] * (lvNum + 1)}
      for lv in range(1, lvNum + 1):
         try:
            music = pyg.mixer.Sound(location + "Music/" + str(lv) + ".wav")
         except:
            music = None
         properties["Music"].append(music)
         with open(location + "Code/" + str(lv) + ".txt", "r") as file:
            code = reader(file, delimiter=',')
            for line in code:
               if line[0] == "name":
                  properties["Name"].append(line[1])
               elif line[0] == "ground":
                  properties["Colour"][lv][0] = int(line[1])
                  properties["Colour"][lv][1] = int(line[2])
                  properties["Colour"][lv][2] = int(line[3])
               elif line[0] == "laps":
                  properties["Laps"].append(line[1])
               elif line[0] not in ["name", "ground", "laps"]:
                  properties["Code"][lv].append(line)
                  if line[0] == "gate":
                     properties["Gates"][level] += 1
            
   else:
      folder = getFolderItems(location + "Code/", mode="ITEM")
      properties = {"Name" : [""], "Colour" : [[0 for i in range(3)] for j in range(len(folder) + 1)], "Code" : [[[""]] for i in range(len(folder) + 1)], "Music" : [], "Laps" : [0], "Gates" : [0] * (len(folder) + 1)}
      for lv in range(0, len(folder)):
         with open(location + "Code/" + folder[lv], "r") as file:
            code = reader(file, delimiter=',')
            for line in code:
               if line[0] == "name":
                  properties["Name"].append(line[1])
               elif line[0] == "ground":
                  properties["Colour"][lv + 1][0] = int(line[1])
                  properties["Colour"][lv + 1][1] = int(line[2])
                  properties["Colour"][lv + 1][2] = int(line[3])
               elif line[0] == "laps":
                  properties["Laps"].append(line[1])
               elif line[0] not in ["name", "ground", "laps"]:
                  properties["Code"][lv + 1].append(line)
                  if line[0] == "gate":
                     properties["Gates"][level] += 1
         try:
            music = pyg.mixer.Sound(location + "Music/" + properties["Name"][lv + 1] + ".wav")
         except:
            music = None
         properties["Music"].append(music)
   if load == False and account != "Default":
      mde = "LEVEL_SELECT_USERNAME"
   return properties, mde
      
def getCreatorName(account):
   names = []
   location = "UserData/" + account + "/Levels/Code/"
   lvNum = getLvNum(location)
   for lv in range(1, lvNum + 1):
      with open(location + str(level) + ".txt", "r") as file:
         code = reader(file, delimiter=',')
         for line in code:
            if line[0] == "name":
               names.append(line[1])
   return names

def getCarCreation():
   global username, carCreatorProperties
   location = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"] + "/car.png"
   if os.path.exists(location) == False:
      location = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"] + "/car.jpg"
   carCreatorProperties["Image"] = importImage(location=location)
   location = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"]
   data = open(location + "/data.bin", "rb")
   statsArray = pickle.load(data)
   data.close()
   carCreatorProperties["TopSpeed"] = statsArray[0]
   carCreatorProperties["Acceleration"] = statsArray[1]
   carCreatorProperties["Handling"] = statsArray[2]
   carCreatorProperties["Offroad"] = statsArray[3]
   carCreatorProperties["EngineType"] = statsArray[4]
   

def getLevelCreation():
   global username, levelCreatorProperties
   resetCreator("GET_LEVEL_CREATION")
   location = "UserData/" + username + "/Levels/Code/"
   with open(location + levelCreatorProperties["Name"] + ".txt", "r") as file:
      code = reader(file, delimiter=',')
      i = 0
      for line in code:
         if line[0] == "ground":
            levelCreatorProperties["Colour"][0] = int(line[1])
            levelCreatorProperties["Colour"][1] = int(line[2])
            levelCreatorProperties["Colour"][2] = int(line[3])
         elif line[0] == "laps":
            levelCreatorProperties["Laps"] = int(line[1])
         elif line[0] not in ["name", "ground", "laps"]:
            levelCreatorProperties["Code"].append("")
            levelCreatorProperties["Code"][i] = line
         i += 1
               
def getCars(account, mde, vehicle, load=False):
   properties = {"Name" : [], "Speed" : [], "Acceleration" : [], "Handling" : [], "Offroad" : [], "Engine" : [], "Image" : []}
   location = "UserData/" + account + "/Cars/"
   folder = getFolderItems(location)
   if folder == ['']:
      location = "UserData/Default/Cars/"
   for data in range(1, len(folder)):
      if account == "Default":
         name = folder[data].replace(str(data) + " - ", "")
      else:
         name = folder[data]
      properties["Name"].append(name)
      carData = open(location + folder[data] + "/data.bin", "rb")
      statsArray = pickle.load(carData)
      carData.close()
      properties["Speed"].append(statsArray[0])
      properties["Acceleration"].append(statsArray[1])
      properties["Handling"].append(statsArray[2])
      properties["Offroad"].append(statsArray[3])
      properties["Engine"].append(statsArray[4])
      extension = ".jpg"
      if os.path.exists(location + "/" + folder[data] + "/car" + ".png"):
         extension = ".png"
      image = pyg.image.load(location + "/" + folder[data] + "/car" + extension)
      properties["Image"].append(image)
      carData.close()
   if load == False:
      vehicle = 0
      if account == "Default":
         mde = "CAR_SELECT_DEFAULT"
      else:
         mde = "CAR_SELECT_USERNAME"
   return properties, mde, vehicle

def carSelect(win, account):
   global carProperties, angle, car, mode, units
   win.fill((levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2]))
   r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
   font = getFont(100)
   centerTextScreen(win, font, "Car Select", 20, r, g, b)
   closeButton(win, [r, g, b])
   backButton(win, [r, g, b])
   angle += 1
   if angle == 360:
      angle = 0
   x = halfScreen[0] - 100
   if account == "Default" and carProperties["Name"][car] in ["Red Van", "Tesla Cybertruck", "Linear Rocket"]:
      y = halfScreen[1] - 300
   else:
      y = halfScreen[1] - 200
   rotate, carRect = rotateCenter(x, y, carProperties["Image"][car], angle)
   carSprite = createSprite(x, y, carRect, rotate)
   allSprites = pyg.sprite.Group([carSprite])
   allSprites.draw(win)
   font = getFont(30)
   centerTextScreen(win, font, "Use the LEFT or RIGHT key to change the car", screen[1] - 80, r, g, b)
   if account == "Default":
      centerTextScreen(win, font, "Default Cars", 150, r, g, b)
      location = "UserData/" + username + "/Cars/"
      folder = getFolderItems(location)
      if folder != ['']:
         menuButton(win, font, halfScreen[0], screen[1] - 160, "View Your Cars", r, g, b, False, "GET_CARS_USERNAME")
         if (key["Up"] or key["W"]) or (key["Down"] or key["S"]):
            playSound(sounds[0])
            pyg.time.wait(200)
            mode = "GET_CARS_USERNAME"
      else:
         centerTextScreen(win, font, "You can also play by creating a car", screen[1] - 50, r, g, b)
   else:
      centerTextScreen(win, font, account + "'s Cars", 150, r, g, b)
      font = getFont(25)
      menuButton(win, font, halfScreen[0], screen[1] - 160, "View Default Cars", r, g, b, False, "GET_CARS_DEFAULT")
      if (key["Up"] or key["W"]) or (key["Down"] or key["S"]):
         playSound(sounds[0])
         pyg.time.wait(200)
         mode = "GET_CARS_DEFAULT"
      font = getFont(30)
   menuButton(win, font, halfScreen[0], screen[1] - 230, "Continue", r, g, b, False, "GET_LEVELS_DEFAULT")
   centerTextScreen(win, font, carProperties["Name"][car], 190, r, g, b)
   font = getFont(20)
   size = 600
   x = halfScreen[0] - (size / 2)
   y = screen[1] - 360
   gap = 30
   textY = 8
   pyg.draw.rect(win, (0, 200, 0), (x + 2, y + 2, (carProperties["Speed"][car] / 40) * size, 18), 0)
   pyg.draw.rect(win, (r, g, b), (x, y, size + 2, 20), 2)
   if units == "METRIC":
      speed = str(carProperties["Speed"][car] * 25) + " kph"
   else:
      speed = str(round(carProperties["Speed"][car] * 25 / 1.609344)) + " mph"
   centerTextScreen(win, font, "Top Speed: " + speed, y - textY, r, g, b)
   pyg.draw.rect(win, (0, 150, 200), (x + 2, y + gap + 2, (carProperties["Acceleration"][car] / 10) * size, 18), 0)
   pyg.draw.rect(win, (r, g, b), (x, y + gap + 2, size + 2, 20), 2)
   centerTextScreen(win, font, "Acceleration: " + str(carProperties["Acceleration"][car]) + " units", y + gap - textY, r, g, b)
   pyg.draw.rect(win, (200, 0, 0), (x + 2, y + (gap * 2) + 2, (carProperties["Handling"][car] / 30) * size, 18), 0)
   pyg.draw.rect(win, (r, g, b), (x, y + (gap * 2), size + 2, 20), 2)
   centerTextScreen(win, font, "Handling: " + str(carProperties["Handling"][car]) + " units", y + (gap * 2) - textY, r, g, b)
   pyg.draw.rect(win, (150, 150, 150), (x + 2, y + (gap * 3) + 2, (carProperties["Offroad"][car] / 5) * size, 18), 0)
   pyg.draw.rect(win, (r, g, b), (x, y + (gap * 3), size + 2, 20), 2)
   centerTextScreen(win, font, "Offroad: " + str(carProperties["Offroad"][car]) + " units", y + (gap * 3) - textY, r, g, b)
   if key["Right"] or key["D"]:
      playSound(sounds[0])
      car += 1
      if car == len(carProperties["Name"]):
         car = 0
      pyg.time.wait(200)
   if key["Left"] or key["A"]:
      playSound(sounds[0])
      car -= 1
      if car == -1:
         car = len(carProperties["Name"]) - 1
      pyg.time.wait(200)
   if key["Enter"]:
      playSound(sounds[1])
      pyg.time.wait(200)
      mode = "GET_LEVELS_DEFAULT"

def playSound(sound, channel=0, loops=0):
   if channel == 0:
      pyg.mixer.Channel(channel).play(sound, loops=loops)
   else:
      if pyg.mixer.Channel(channel).get_busy() == False:
         pyg.mixer.Channel(channel).play(sound, loops=loops)
     
def levelSelect(win, account):
   global level, camera, mode, sounds
   if level != 5:
      drawTrack(win, level, camera, scaleFactor=2)
   else:
      drawTrack(win, level, camera)
   r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
   r1, g1, b1 = invertCol(r, g, b)
   bg = pyg.Surface((480, 90))
   bg.set_alpha(175)
   bg.fill((r1, g1, b1))
   win.blit(bg, (halfScreen[0] - 240, 150))
   font = getFont(100)
   centerTextScreen(win, font, "Level Select", 20, r, g, b)
   closeButton(win, [r, g, b])
   backButton(win, [r, g, b])
   font = getFont(30)
   bg = pyg.Surface((600, 70))
   bg.set_alpha(175)
   bg.fill((r1, g1, b1))
   win.blit(bg, (halfScreen[0] - 300, screen[1] - 110))
   centerTextScreen(win, font, "Use WASD to look around the level", screen[1] - 110, r, g, b)
   centerTextScreen(win, font, "Use the LEFT or RIGHT key to change the level", screen[1] - 80, r, g, b)
   location = "UserData/" + username + "/Levels/Code/"
   userLvNum = getLvNum(location)
   location = "UserData/Default/Levels/Code/"
   defaultLvNum = getLvNum(location)
   if account == "Default":
      centerTextScreen(win, font, "Default Levels", 150, r, g, b)
      centerTextScreen(win, font, "Level " + str(level) + ": " + levelProperties["Name"][level], 190, r, g, b)
      if userLvNum != 0:
         font = getFont(23)
         menuButton(win, font, halfScreen[0], screen[1] - 160, "View Your Levels", r, g, b, False, "GET_LEVELS_USERNAME")
         font = getFont(30)
         if key["Up"] or key["Down"]:
            playSound(sounds[0])
            pyg.time.wait(200)
            mode = "GET_LEVELS_USERNAME"
      else:
         bg = pyg.Surface((600, 35))
         bg.set_alpha(175)
         bg.fill((r1, g1, b1))
         win.blit(bg, (halfScreen[0] - 300, screen[1] - 40))
         centerTextScreen(win, font, "You can also play by creating a level", screen[1] - 50, r, g, b)
      if key["Right"]:
         playSound(sounds[0])
         level += 1
         if level == defaultLvNum + 1:
            level = 1
         pyg.time.wait(200)
      if key["Left"]:
         playSound(sounds[0])
         level -= 1
         if level == 0:
            level = defaultLvNum
         pyg.time.wait(200)
   else:
      centerTextScreen(win, font, account + "'s Levels", 150, r, g, b)
      centerTextScreen(win, font, levelProperties["Name"][level], 190, r, g, b)
      font = getFont(23)
      menuButton(win, font, halfScreen[0], screen[1] - 160, "View Default Levels", r, g, b, False, "GET_LEVELS_DEFAULT")
      if key["Up"] or key["Down"]:
         playSound(sounds[0])
         pyg.time.wait(200)
         mode = "GET_LEVELS_DEFAULT"
      font = getFont(30)
      if key["Right"]:
         playSound(sounds[0])
         level += 1
         if level == userLvNum + 1:
            level = 1
         pyg.time.wait(200)
      if key["Left"]:
         playSound(sounds[0])
         level -= 1
         if level == 0:
            level = userLvNum
         pyg.time.wait(200)
   menuButton(win, font, halfScreen[0], screen[1] - 230, "Continue", r, g, b, False, "RESET_TIMER")
   if level != 5:
      speed = 10
   else:
      speed = 50
   if key["D"]:
      camera[0] -= speed
   if key["A"]:
      camera[0] += speed
   if key["S"]:
      camera[1] -= speed
   if key["W"]:
      camera[1] += speed
   if key["Enter"]:
      playSound(sounds[1])
      pyg.time.wait(200)
      mode = "RESET_TIMER"

def resetLevel(lv):
   global camera, currentLap, time, velocity, angle, activeGate, gatesCleared, enginePitch
   if lv != 5:
      camera = [halfScreen[0] - 20, halfScreen[1] + 20]
   else:
      camera = [halfScreen[0] + 70, halfScreen[1] + 70]
   currentLap = 1
   time = {"Second" : -3, "Minute" : 0}
   velocity = 0
   angle = 0
   activeGate = 0
   gatesCleared = 0
   enginePitch = 0   

def resetCreator(creator):
   global camera, carCreatorProperties, activeGate, angle, levelCreatorProperties, levelProperties, level
   if creator in ["LEVEL_CREATOR", "GET_LEVEL_CREATION"]:
      camera = [(((screen[0] - (screen[0] // 5)) // 2) - 20), (halfScreen[1]) - 100]
      if creator == "LEVEL_CREATOR":
         levelCreatorProperties = {"Name" : "Unnamed Level", "Colour" : [levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2]], "Angle" : 0, "Type" : 1, "Laps" : 1, "PieceSelected" : False, "Code" : [["" for i in range(10)]], "Undo" : []}
      else:
         levelCreatorProperties = {"Name" : levelCreatorProperties["Name"], "Colour" : [0, 0, 0], "Angle" : 0, "Type" : 1, "Laps" : 1, "PieceSelected" : False, "Code" : [["" for i in range(10)]], "Undo" : [], "ScaleFactor" : 1}            
      levelCreatorProperties["Code"][0] = ["road", 1, 0, 0, 0]
   elif creator == "CAR_CREATOR":
      carCreatorProperties = {"Name" : "Unnamed Car", "Image" : None, "TopSpeed" : 1, "Acceleration" : 1, "Handling" : 1, "Offroad" : 1, "EngineType" : 0}
   activeGate = 0
   angle = 0

def pauseMenu(win, cam, col):
   global pausedVelocity, velocity, mode
   velocity = 0
   drawLevel(win, level, cam, False)
   menu = pyg.Surface((500, 400))
   menu.set_alpha(100)
   menu.fill((col[0], col[1], col[2]))
   win.blit(menu, (halfScreen[0] - 250, halfScreen[1] - 300))
   r1, g1, b1 = invertCol(col[0], col[1], col[2])
   font = getFont(50)
   centerTextScreen(win, font, "Game Paused", halfScreen[1] - 280, r1, g1, b1)
   font = getFont(30)
   menuButton(win, font, halfScreen[0], halfScreen[1] - 180, "Continue", r1, g1, b1, False,"UNPAUSE")
   menuButton(win, font, halfScreen[0], halfScreen[1] - 110, "Options", r1, g1, b1, False, "PAUSED_OPTIONS")
   menuButton(win, font, halfScreen[0], halfScreen[1] - 40, "Quit Game", r1, g1, b1, False,"MAIN_MENU", "MAIN_MENU")
   if key["Enter"] or key["Escape"]:
      playSound(sounds[1])
      pyg.time.wait(200)
      mode = "UNPAUSE"

def finishedLevel(win, cam, position):
   global level, mode, menuMode, units
   drawLevel(win, level, cam, True)
   font = getFont(50)
   r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
   font = getFont(100)
   if position == "WIN":
      centerTextScreen(win, font, "YOU WON!", 20, r, g, b)
   else:
      centerTextScreen(win, font, "YOU LOST!", 20, r, g, b)
   font = getFont(30)
   menuButton(win, font, halfScreen[0], screen[1] - 100, "Continue", r, g, b, False,"MAIN_MENU", "MAIN_MENU")
   if key["Enter"]:
      playSound(sounds[1])
      pyg.mixer.Channel(2).stop()
      menuMode = "MAIN_MENU"
      mode = "MAIN_MENU"
   font = getFont(40)
   drawText(win, font, "SPEED: ", screen[0] - 250, 3, r, g, b)
   pyg.draw.rect(win, (0, 255, 0), (screen[0] - 108, 12, (abs(velocity) / carProperties["Speed"][car]) * 88, 28), 0)
   pyg.draw.rect(win, (r, g, b), (screen[0] - 110, 10, 90, 30), 2)
   font = getFont(25)
   if units == "METRIC":
      speed = str(round(abs(velocity * 25))) + " kph"
   else:
      speed = str(round(abs((velocity * 25) / 1.609344))) + " mph"
   centerTextPanel(win, font, speed, (screen[0] - 62), 10, r, g, b)
   
def playGame(win, cam, tm):
    global time, carPos, mode, velocity, pausedVelocity, currentLap, defaultLap, carProperties, car, sounds
    time["Second"] += tm.tick_busy_loop(60) / 1000
    r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
    if round(time["Second"]) % 60 == 0 and round(time["Second"]) != 0:
       time["Minute"] += 1
       time["Second"] = 0
    if time["Second"] >= 0:
        showTime = True
        drawLevel(win, level, cam, True)
    else:
        showTime = False
        drawLevel(win, level, cam, False)
    font = getFont(50)
    if time["Second"] >= -3 and time["Second"] <= -2.5:
        playSound(sounds[4], loops=-1)
        drawText(win, font, "3", halfScreen[0], 50, r, g, b)
    elif time["Second"] >= -2 and time["Second"] <= -1.5:
        playSound(sounds[4], loops=-1)
        drawText(win, font, "2", halfScreen[0], 50, r, g, b)
    elif time["Second"] >= -1 and time["Second"] <= -0.5:
        playSound(sounds[4], loops=-1)
        drawText(win, font, "1", halfScreen[0], 50, r, g, b)
    elif (time["Second"] >= 0 and time["Second"] <= 1) and time["Minute"] == 0:
        playSound(sounds[5], loops=-1)
        drawText(win, font, "GO!", halfScreen[0], 50, r, g, b)
    else:
       pyg.mixer.Sound.stop(sounds[4])
       pyg.mixer.Sound.stop(sounds[5])
    pausedVelocity = velocity
    carPos = [(halfScreen[0] - 20) - cam[0], -((halfScreen[1] + 20) - cam[1])]
    font = getFont(40)
    if showTime:
       drawText(win, font, "Elapsed Time: " + str(time["Minute"]) + ":" + str(round(time["Second"], 2)), 5, 5, r, g, b)
    if key["Enter"] or key["Escape"]:
       pyg.mixer.Sound.stop(sounds[4])
       pyg.mixer.Sound.stop(sounds[5])
       playSound(sounds[1])
       pyg.time.wait(200)
       mode = "PAUSED"
    if currentLap >= int(levelProperties["Laps"][level]) + 1:
       mode = "WIN"
    drawText(win, font, "Lap: " + str(currentLap) + "/" + str(levelProperties["Laps"][level]), 5, 45, r, g, b)
    drawText(win, font, "Checkpoints Cleared: " + str(gatesCleared), 5, 85, r, g, b)
    drawText(win, font, "SPEED: ", screen[0] - 250, 3, r, g, b)
    drawText(win, font, "X: " + str(round(carPos[0])), 5, screen[1] - 80, r, g, b)
    drawText(win, font, "Y: " + str(round(carPos[1])), 5, screen[1] - 40, r, g, b)
    pyg.draw.rect(win, (0, 255, 0), (screen[0] - 108, 12, (abs(velocity) / carProperties["Speed"][car]) * 88, 28), 0)
    pyg.draw.rect(win, (r, g, b), (screen[0] - 110, 10, 90, 30), 2)
    font = getFont(25)
    if units == "METRIC":
      speed = str(round(abs(velocity * 25))) + " kph"
    else:
      speed = str(round(abs((velocity * 25) / 1.609344))) + " mph"
    centerTextPanel(win, font, speed, (screen[0] - 62), 10, r, g, b)

def menuButton(win, fnt, x, y, s, r, g, b, mnuMde, mde, mnuAndMde=""):
    global mode, menuMode, sounds
    r1, g1, b1 = invertCol(r, g, b)
    btn = pyg.Surface((200, 50))
    btn.set_alpha(150)
    if mousePos[0] > x - 100 and mousePos[0] < x + 100 and mousePos[1] > y and mousePos[1] < y + 50:
       btn.fill((r1, g1, b1))
       r2, g2, b2 = r, g, b
       if clicked[0] == 1 and mouseDown:
          playSound(sounds[1])
          if mnuAndMde == "":
             if mnuMde:
                menuMode = mde
             else:
                mode = mde
          else:
             menuMode = mnuAndMde
             mode = mde
          pyg.time.wait(200)
    else:
       btn.fill((r, g, b))
       r2, g2, b2 = r1, g1, b1
    win.blit(btn, (x - 100, y))
    if x == halfScreen[0]:
       centerTextScreen(win, fnt, s, y, r2, g2, b2)
    else:
       centerTextPanel(win, fnt, s, x, y + 10, r2, g2, b2)
          
def closeButton(win, col):
    global mode, sounds
    x = screen[0] - 51
    y = 26
    r, g, b = invertCol(col[0], col[1], col[2])
    btn = pyg.Surface((100, 75))
    btn.set_alpha(150)
    fnt = getFont(50)
    if mousePos[0] > x - 100 and mousePos[0] < x + 100 and mousePos[1] > y and mousePos[1] < y + 50:
        btn.fill((r, g, b))
        r1, g1, b1 = col[0], col[1], col[2]
        if clicked[0] == 1 and mouseDown:
            playSound(sounds[1])
            if mode == "CAR_CREATOR":
               discardCar(0)
            elif mode == "LEVEL_CREATOR":
               fakeWin = Tk()
               fakeWin.withdraw()
               quitCreator = messagebox.askyesnocancel("Quit Level Creator", "Are you sure that you want to quit the level creator and the entire game?\nUnsaved changes will be lost")
               closeTk(fakeWin)
               if quitCreator:
                  mode = "QUIT"
            else:
               mode = "QUIT"
    else:
       btn.fill((col[0], col[1], col[2]))
       r1, g1, b1 = r, g, b
    win.blit(btn, (x - 50, y - 25))
    centerTextPanel(win, fnt, "X", x, y / 2, r1, g1, b1)

def backButton(win, col):
    global mode, menuMode, sounds
    x = 51
    y = 26
    r, g, b = invertCol(col[0], col[1], col[2])
    btn = pyg.Surface((100, 75))
    btn.set_alpha(150)
    arrowFont =  pyg.font.SysFont("Arial", 50)
    buttonPressed = False
    if mousePos[0] > x - 100 and mousePos[0] < x + 100 and mousePos[1] > y and mousePos[1] < y + 50:
       btn.fill((r, g, b))
       r1, g1, b1 = col[0], col[1], col[2]
       if clicked[0] == 1 and mouseDown:
          buttonPressed = True
    else:
       btn.fill((col[0], col[1], col[2]))
       r1, g1, b1 = r, g, b
    win.blit(btn, (x - 50, y - 25))
    centerTextPanel(win, arrowFont, "\u2190", x, y / 2, r1, g1, b1)
    if key["Escape"] or buttonPressed:
       playSound(sounds[1])
       if mode == "MAIN_MENU":
           if menuMode in ["LOGIN_PAGE", "INSTRUCTIONS"]:
               menuMode = "TITLE_SCREEN"
           elif menuMode in ["CAR_CREATOR_MENU", "LEVEL_CREATOR_MENU"]:
              menuMode = "MAIN_MENU"
           elif menuMode == "CAR_CREATOR_INSTRUCTIONS":
              menuMode = "CAR_CREATOR_MENU"
           elif menuMode == "LEVEL_CREATOR_INSTRUCTIONS":
              menuMode = "LEVEL_CREATOR_MENU"
           elif menuMode == "CREDITS":
              menuMode = "TITLE_SCREEN"
       elif mode in ["LEVEL_SELECT_DEFAULT", "LEVEL_SELECT_USERNAME"]:
          mode = "GET_CARS_DEFAULT"
       elif mode in ["CAR_SELECT_DEFAULT", "CAR_SELECT_USERNAME"]:
          resetLevel(level)
          mode = "MAIN_MENU"
       elif mode == "LEVEL_CREATOR":
          fakeWin = Tk()
          fakeWin.withdraw()
          quitCreator = messagebox.askyesnocancel("Quit Level Creator", "Are you sure that you want to quit the level creator?\nUnsaved changes will be lost")
          closeTk(fakeWin)
          if quitCreator:
             resetLevel(level)
             mode = "MAIN_MENU"
       elif mode == "CAR_CREATOR":
          discardCar(1)
       pyg.time.wait(200)

def arrowButton(win, col, flipCol, x, y, mode):
   global levelCreatorProperties, sounds
   btn = pyg.Surface((50, 50))
   btn.set_alpha(150)
   arrowFont =  pyg.font.SysFont("Arial", 40)
   if (mousePos[0] > x - 100 and mousePos[0] < x + 100 and mousePos[1] > y and mousePos[1] < y + 50):
      btn.fill(col)
      r, g, b = flipCol
      if clicked[0] == 1 and mouseDown:
         playSound(sounds[0])
         if mode == "ACW":
            levelCreatorProperties["Angle"] -= 90
            if levelCreatorProperties["Type"] in [1, 3]:
               if levelCreatorProperties["Angle"] == 180:
                  levelCreatorProperties["Angle"] = 0
               elif levelCreatorProperties["Angle"] == 270:
                  levelCreatorProperties["Angle"] = 90
            if levelCreatorProperties["Angle"] == -90:
               levelCreatorProperties["Angle"] = 270
         elif mode == "CW":
            levelCreatorProperties["Angle"] += 90
            if levelCreatorProperties["Type"] in [1, 3]:
               if levelCreatorProperties["Angle"] == 180:
                  levelCreatorProperties["Angle"] = 0
               elif levelCreatorProperties["Angle"] == 270:
                  levelCreatorProperties["Angle"] = 90
            if levelCreatorProperties["Angle"] == 450:
               levelCreatorProperties["Angle"] = 0
         elif mode == "BACK":
            levelCreatorProperties["Type"] -= 1
            if levelCreatorProperties["Type"] in [1, 3]:
               if levelCreatorProperties["Angle"] == 180:
                  levelCreatorProperties["Angle"] = 0
               elif levelCreatorProperties["Angle"] == 270:
                  levelCreatorProperties["Angle"] = 90
            if levelCreatorProperties["Type"] == 6:
               levelCreatorProperties["Type"] = 3
            if levelCreatorProperties["Type"] == 0:
               levelCreatorProperties["Type"] = 9
         elif mode == "NEXT":
            levelCreatorProperties["Type"] += 1
            if levelCreatorProperties["Type"] in [1, 3]:
               if levelCreatorProperties["Angle"] == 180:
                  levelCreatorProperties["Angle"] = 0
               elif levelCreatorProperties["Angle"] == 270:
                  levelCreatorProperties["Angle"] = 90
            if levelCreatorProperties["Type"] == 4:
               levelCreatorProperties["Type"] = 7
            if levelCreatorProperties["Type"] == 10:
               levelCreatorProperties["Type"] = 1
         pyg.time.wait(200)
   else:
      btn.fill(flipCol)
      r, g, b = col
   win.blit(btn, (x, y))
   if mode in["ACW", "BACK"]:
      drawText(win, arrowFont, "\u2190", x + 5, y, r, g, b)
   elif mode in ["CW", "NEXT"]:
      drawText(win, arrowFont, "\u2192", x + 5, y, r, g, b)

def drawText(win, fnt, s, x, y, r, g, b):
    text = fnt.render(s, True, (r, g, b))
    win.blit(text, (x, y))

def centerTextScreen(win, fnt, s, y, r, g, b):
    x = halfScreen[0]
    text = fnt.render(s, True, (r, g, b))
    txtW = text.get_width()
    txtH = text.get_height()
    xTxt = x - txtW // 2
    yTxt = y + 7
    win.blit(text, (xTxt, yTxt))

def centerTextPanel(win, fnt, s, x, y, r, g, b):
    text = fnt.render(s, True, (r, g, b))
    txtW = text.get_width()
    xTxt = x - txtW // 2
    yTxt = y
    win.blit(text, (xTxt, yTxt))

def createTk(mde):
   window = Tk()
   window.protocol("WM_DELETE_WINDOW", lambda: closeTk(window))
   window.after(1, lambda: window.focus_force())
   window.resizable(False, False)
   if mde != "CAR_CREATOR":
      window.attributes("-topmost", True)
   frame = Frame(window)
   frame.pack()
   if mde == "ENTER_DETAILS":
      window.title("Enter Details")
      login(window, frame)
   elif mde == "CREATE_ACCOUNT":
      window.title("Create Account")
      accountCreation(window, frame)
   elif mde == "EDIT_CAR":
      window.title("Edit Car")
      editCreation(window, frame, "Car")
   elif mde == "CAR_OPTIONS":
      window.title("Car Properties")
      editCarProperties(window, frame)
   elif mde == "LEVEL_OPTIONS":
      window.title("Advanced Properties")
      editLevelProperties(window, frame)
   elif mde == "EDIT_LEVEL":
      window.title("Edit Level")
      editCreation(window, frame, "Level")
   elif mde == "SOUND":
      return window, frame
   elif mde == "MENU_OPTIONS":
      window.title("Game Options")
      gameOptions(window, frame, "MENU")
   elif mde == "PAUSED_OPTIONS":
      window.title("Game Options")
      gameOptions(window, frame, "PAUSED")
   elif mde == "CHANGE_USERNAME":
      window.title("Change Username")
      changeUsername(window, frame)
   elif mde == "CHANGE_PASSWORD":
      window.title("Change Password")
      changePassword(window, frame)  
   window.mainloop()

def login(win, frame):
    Label(frame, text="Username:").grid(row=0)
    usernameBox = createTextBox(frame, 0, 1)
    Label(frame, text="Password:").grid(row=1)
    passwordBox = createTextBox(frame, 1, 1, pword=True)
    passwordBox.bind("<Return>", lambda event:verifyUserDetails(1, win, unameBox=usernameBox, pwordBox=passwordBox))
    continueBtn = Button(frame, text="Continue", command=lambda:verifyUserDetails(1, win, unameBox=usernameBox, pwordBox=passwordBox))
    continueBtn.grid(row=2, column=1, sticky="E", padx=10, pady=5)

def accountCreation(win, frame):
    Label(frame, text="Enter a username:").grid(row=0)
    usernameBox = createTextBox(frame, 0, 1)
    Label(frame, text="Enter a password:").grid(row=1)
    passwordBox = createTextBox(frame, 1, 1, pword=True)
    Label(frame, text="Confirm password:").grid(row=2)
    confirmPasswordBox = createTextBox(frame, 2, 1, pword=True)
    confirmPasswordBox.bind("<Return>", lambda event:verifyUserDetails(2, win, unameBox=usernameBox, pwordBox=passwordBox, confirmPwordBox=confirmPasswordBox))
    btn = Button(frame, text="Continue", command=lambda:verifyUserDetails(2, win, unameBox=usernameBox, pwordBox=passwordBox, confirmPwordBox=confirmPasswordBox))
    btn.grid(row=3, column=1, sticky="E", padx=10, pady=5)

def gameOptions(win, frame, mde):
   global units, volume, username
   if username == "Guest" or mde == "PAUSED":
      offset = 1
   else:
      offset = 2
   Label(frame, text="Game Options", font=getFont(30, for_tk=True)).grid(row=0, column=0, columnspan=3)
   Label(frame, text="Game Units:").grid(row=1, column=0)
   radioFrame = Frame(frame)
   radioFrame.grid(row=1, column=offset, columnspan=2)
   unit = StringVar()
   unit.set(units)
   metricBtn = Radiobutton(radioFrame, text="Metric", value="METRIC", var=unit)
   metricBtn.grid(row=0, column=0)
   imperialBtn = Radiobutton(radioFrame, text="Imperial", value="IMPERIAL", var=unit)
   imperialBtn.grid(row=0, column=1)
   Label(frame, text="Music Volume:").grid(row=3, column=0)
   musicScale = Scale(frame, from_=0, to_=100, orient=HORIZONTAL)
   musicScale.set(volume["Music"])
   musicScale.grid(row=3, column=offset)
   Label(frame, text="Sound Volume:").grid(row=4, column=0)
   soundScale = Scale(frame, from_=0, to_=100, orient=HORIZONTAL)
   soundScale.set(volume["Sound"])
   soundScale.grid(row=4, column=offset)
   Label(frame, text="Engine Volume:").grid(row=5, column=0)
   engineScale = Scale(frame, from_=0, to_=100, orient=HORIZONTAL)
   engineScale.set(volume["Engine"])
   engineScale.grid(row=5, column=offset)
   if username != "Guest" and mde != "PAUSED":
      changeUnameBtn = Button(frame, text="Change Username", command=lambda:createTk("CHANGE_USERNAME"))
      changeUnameBtn.grid(row=6, column=0, padx=5, pady=5)
      changePwordBtn = Button(frame, text="Change Password", command=lambda:createTk("CHANGE_PASSWORD"))
      changePwordBtn.grid(row=6, column=1, padx=5, pady=5)
      deleteAccountBtn = Button(frame, text="Delete Account", command=lambda:deleteAccount(win))
      deleteAccountBtn.grid(row=6, column=2, padx=5, pady=5)
   confirmBtn = Button(frame, text="Confirm", command=lambda:setOptions(win, unit.get(), musicScale.get(), soundScale.get(), engineScale.get()))
   confirmBtn.grid(row=7, column=0, padx=5, pady=5, columnspan=3)

def changeUsername(win, frame):
    Label(frame, text="Enter a new username:").grid(row=0)
    usernameBox = createTextBox(frame, 0, 1)
    btn = Button(frame, text="Continue", command=lambda:verifyUserDetails(3, win, unameBox=usernameBox))
    btn.grid(row=1, column=1, sticky="E", padx=10, pady=5)

def changePassword(win, frame):
    Label(frame, text="Enter your old password:").grid(row=0)
    oldPasswordBox = createTextBox(frame, 0, 1, pword=True)
    Label(frame, text="Enter a new password:").grid(row=1)
    passwordBox = createTextBox(frame, 1, 1, pword=True)
    Label(frame, text="Confirm the new password:").grid(row=2)
    confirmPasswordBox = createTextBox(frame, 2, 1, pword=True)
    btn = Button(frame, text="Continue", command=lambda:verifyUserDetails(4, win, oldPwordBox=oldPasswordBox, pwordBox=passwordBox, confirmPwordBox=confirmPasswordBox))
    btn.grid(row=3, column=1, sticky="E", padx=10, pady=5)

def deleteAccount(win):
   delete = messagebox.askyesno("Delete Account", "Are you sure that you want to delete your account?\nSaved data cannot be recovered")
   if delete:
      global username, mode, menuMode
      try:
         shutil.rmtree("UserData/" + username)
         messagebox.showinfo("Account Deleted", "Your account has been successfully deleted")
         mode = "MAIN_MENU"
         menuMode = "TITLE_SCREEN"
         closeTk(win)
      except:
         messagebox.showerror("Error deleting account", "The account cannot be deleted. Make sure that any game related files/folders are closed before deleting")

def setOptions(win, unit, msc, snd, eng):
   data = open("UserData/" + username + "/data.bin", "rb")
   contents = pickle.load(data)
   data.close()
   contents[1] = unit
   contents[2] = msc
   contents[3] = snd
   contents[4] = eng
   data = open("UserData/" + username + "/data.bin", "wb")
   pickle.dump(contents, data)
   data.close()
   global units, volume
   units = unit
   volume["Music"] = msc
   volume["Sound"] = snd
   volume["Engine"] = eng
   pyg.mixer.Channel(0).set_volume(volume["Sound"] / 100)
   pyg.mixer.Channel(1).set_volume(volume["Engine"] / 100)
   pyg.mixer.Channel(2).set_volume(volume["Music"] / 100)
   pyg.mixer.Channel(3).set_volume(volume["Sound"] / 100)
   pyg.mixer.Channel(4).set_volume(volume["Sound"] / 100)
   closeTk(win)

def editCreation(win, frame, typ):
   Label(frame, text="Choose " + typ.lower() + " to edit:").grid(row=0, column=0, columnspan=3, padx=5, pady=5)
   location = "UserData/" + username + "/" + typ + "s/"
   if typ == "Car":
      folder = getFolderItems(location)
      start = 1
   else:
      folder = getFolderItems(location + "/Code", "ITEM")
      start = 0
   listBox = Listbox(frame, width=30, height=5 + len(folder))
   listBox.grid(row=1, column=0, rowspan=2, columnspan=3, padx=2, pady=5)
   for item in range(start, len(folder)):
      folder[item] = folder[item].replace(".txt", "")
      listBox.insert(item, folder[item])
   editBtn = Button(frame, text="Edit", command=lambda:openCreation(win, listBox.get(ACTIVE), typ))
   editBtn.grid(row=3, column=0, padx=5, pady=5)
   editBtn = Button(frame, text="Delete", command=lambda:deleteCreation(win, listBox.get(ACTIVE), typ))
   editBtn.grid(row=3, column=1, padx=5, pady=5)
   if typ == "Car":
      cancelBtn = Button(frame, text="Cancel", command=lambda:closeTk(win))
   else:
      win.protocol("WM_DELETE_WINDOW", lambda: closeCreationEditor(win))
      cancelBtn = Button(frame, text="Cancel", command=lambda:closeCreationEditor(win))
      cancelBtn.grid(row=3, column=2, padx=5, pady=5)

def closeCreationEditor(win):
   global mode
   closeTk(win)
   mode = "MAIN_MENU"

def openCreation(win, name, typ):
   global mode, editCarCreator
   if name != "":
      closeTk(win)
      if typ == "Car":
         global carCreatorProperties
         carCreatorProperties["Name"] = name
         editCarCreator = True
         getCarCreation()
         editCarCreator = False
         mode = "CAR_CREATOR"
      else:
         global levelCreatorProperties
         levelCreatorProperties["Name"] = name
         getLevelCreation()
         mode = "LEVEL_CREATOR"
   else:
      messagebox.showwarning(typ + " not selected", "Please select a " + typ.lower() + " to edit")

def deleteCreation(win, name, typ):
   if name != "":
      originalName = name
      if typ == "Level":
         name = name + ".txt"
      delete = messagebox.askyesnocancel("Delete " + typ, "Are you sure you want to delete " + originalName + "?")
      error = False
      if delete:
         global username
         if typ == "Car":
            location = "UserData/" + username + "/Cars/" + name
            try:
               shutil.rmtree(location)
            except:
               messagebox.showerror("Error deleting car", "The account cannot be deleted. Make sure that any game related files/folders are closed before deleting")
         else:
            location = "UserData/" + username + "/Levels/Code/" + name
            os.remove(location)
            location = "UserData/" + username + "/Levels/Music/" + originalName + ".wav"
            os.remove(location)           
         messagebox.showinfo(typ + " deleted", originalName + " has been successfully deleted")
         closeCreationEditor(win)
   else:
      messagebox.showwarning(typ + " not selected", "Please select a " + typ.lower() + " to delete")

def editCarProperties(win, frame):
   global carCreatorProperties, editCarCreator
   Label(frame, text="Car Properties", font=getFont(30, for_tk=True)).grid(row=0)
   optionsFrame = Frame(frame)
   optionsFrame.grid(row=1)
   Label(optionsFrame, text="Car Name:").grid(row=0, column=0)
   Label(optionsFrame,  text= "(maximum 20 characters)").grid(row=0, column=2)
   Label(optionsFrame, text="Top Speed:").grid(row=1, column=0)
   topSpeed = Label(optionsFrame, text="")
   topSpeed.grid(row=1, column=2)
   Label(optionsFrame, text="Acceleration:").grid(row=2, column=0)
   Label(optionsFrame, text="Handling:").grid(row=3, column=0)
   Label(optionsFrame, text="Offroad:").grid(row=4, column=0)
   Label(optionsFrame, text="Engine Type:").grid(row=5, column=0)
   if username == "Guest":
       Label(frame, text="Warning: Closing the game using a guest account will delete saved data").grid(row=3, padx=5, pady=5)
   carNameEntry = Entry(optionsFrame, width=20)
   carNameEntry.grid(row=0, column=1, padx=10, pady=5)
   topSpeedScale = Scale(optionsFrame, from_=1, to_=40, orient=HORIZONTAL, command=lambda value:updateSpeed(topSpeed, value))
   topSpeedScale.grid(row=1, column=1, padx=5, pady=5)
   accelerationScale = Scale(optionsFrame, from_=1, to_=10, orient=HORIZONTAL)
   accelerationScale.grid(row=2, column=1, padx=5, pady=5)
   handlingScale = Scale(optionsFrame, from_=1, to_=30, orient=HORIZONTAL)
   handlingScale.grid(row=3, column=1, padx=5, pady=5)
   offroadScale = Scale(optionsFrame, from_=1, to_=5, orient=HORIZONTAL)
   offroadScale.grid(row=4, column=1, padx=5, pady=5)
   engineOptions = StringVar(optionsFrame)
   engineChoices = ["Normal", "V8 Racing 1", "Retro 1", "Power", "Diesel 1", "Small Tank", "Rocket", "Diesel 2", "Street Racer", "Monster Truck", "Nuclear Truck", "Retro 2", "Military Vehicle", "Military Tank", "Electric", "Turbo",  "V8 Racing 2"]
   engineOptions.set(engineChoices[0])
   engineOptionList = OptionMenu(optionsFrame, engineOptions, *engineChoices)
   engineOptionList.config(width=12)
   engineOptionList.grid(row=5, column=1, padx=5, pady=5)
   soundButton = Button(optionsFrame, text="Test Engine", command=lambda:soundTest(engineOptions.get()))
   soundButton.grid(row=5, column=2, padx=5, pady=5)
   buttonFrame = Frame(frame)
   buttonFrame.grid(row=2)
   saveBtn = Button(buttonFrame, text="Save & Apply", command=lambda:saveCar(win, carNameEntry, topSpeedScale.get(), accelerationScale.get(), handlingScale.get(), offroadScale.get(), engineChoices.index(engineOptions.get()), editCarCreator))
   saveBtn.grid(row=0, column=0, padx=5, pady=5)
   closeBtn = Button(buttonFrame, text="Close", command=lambda:closeTk(win))
   closeBtn.grid(row=0, column=1, padx=5, pady=5)
   topSpeedScale.set(carCreatorProperties["TopSpeed"])
   updateSpeed(topSpeed, topSpeedScale.get())
   accelerationScale.set(carCreatorProperties["Acceleration"])
   handlingScale.set(carCreatorProperties["Handling"])
   offroadScale.set(carCreatorProperties["Offroad"])
   engineOptions.set(engineChoices[carCreatorProperties["EngineType"]])
                     
def updateSpeed(item, value):
   if units == "METRIC":
      speed = str(int(value) * 25) + " kph"
   else:
      speed = str(round(int(value) * 25 / 1.609344)) + " mph"
   item["text"] = speed

def soundTest(engName):
   global engines
   win, frame = createTk("SOUND")
   win.title(engName + " Engine Test")
   engineChoices = ["Normal", "V8 Racing 1", "Retro 1", "Power", "Diesel 1", "Small Tank", "Rocket", "Diesel 2", "Street Racer", "Monster Truck", "Nuclear Truck", "Retro 2", "Military Vehicle", "Military Tank", "Electric", "Turbo",  "V8 Racing 2"]
   engPos = engineChoices.index(engName)
   for pitch in range(len(engines[engPos])):
      if pitch == 0:
         name = "Idle"
      elif pitch == len(engines[engPos]) - 1:
         name = "Max"
      else:
         name = str(pitch)
      engBtn = Button(frame, text="Pitch " + name, command=lambda pitch=pitch:playTk("Sound/Engine/" + str(engPos) + "-" + str(pitch) + ".wav"))
      engBtn.grid(row=1, column=pitch, padx=5, pady=5)
   stopBtn = Button(frame, text="Stop", command=stopTk)
   stopBtn.grid(row=1, column=pitch+1, padx=5, pady=5)

def playTk(location):
   playSound(location, SND_FILENAME|SND_LOOP|SND_ASYNC)
      
def stopTk():
   playSound(None, SND_FILENAME)

def discardCar(button):
    global username, carName, quitCarCreator, carCreatorProperties, mode, menuMode
    fakeWin = Tk()
    fakeWin.withdraw()
    if button == 1:
       message = "Are you sure that you want to quit the car creator?\nUnsaved changes will be lost"
    else:
       message = "Are you sure that you want to quit the car creator and the entire game?\nUnsaved changes will be lost"
    quitCreator = messagebox.askyesnocancel("Quit Car Creator", message)
    closeTk(fakeWin)
    if quitCreator:
        location = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"]
        try:
            os.remove(location + "/tempcar.png")
        except:
            pass
        finally:
            if os.path.exists(location + "/data.bin") == False:
               shutil.rmtree(location)
            if button == 0:
               mode = "QUIT"
            else:
               menuMode = "CAR_CREATOR_MENU"
               mode = "MAIN_MENU"
            resetCreator("CAR_CREATOR")
                
def saveCar(win, carNameEntry, speed, acceleration, handling, offroad, engine, editCar):
   global username, menuMode, levelCreatorProperties, carCreatorProperties
   nameError = verifyName(carNameEntry, "Car")
   if nameError == False:
      location = "UserData/" + username + "/Cars/" + carCreatorProperties["Name"]
      if os.path.exists(location + "/car.png") and os.path.exists(location + "/tempcar.png"):
         os.remove(location + "/car.png")
         os.rename(location + "/tempcar.png", location + "/car.png")
      elif os.path.exists(location + "/tempcar.png"):
         os.rename(location + "/tempcar.png", location + "/car.png")
      carCreatorProperties["TopSpeed"] = speed
      carCreatorProperties["Acceleration"] = acceleration
      carCreatorProperties["Handling"] = handling
      carCreatorProperties["Offroad"] = offroad
      carCreatorProperties["EngineType"] = engine
      data = open(location + "/data.bin", "wb")
      dataArray = [speed, acceleration, handling, offroad, engine]
      pickle.dump(dataArray, data)
      data.close()
      messagebox.showinfo("Car Saved", "Your car has been saved successfully")
      closeTk(win)

def verifyName(entry, typ):
   global carCreatorProperties, levelCreatorProperties, username
   if typ == "Level":
      oldName = levelCreatorProperties["Name"]
      levelCreatorProperties["Name"] = entry.get()[0:20]
      nameCheck = levelCreatorProperties["Name"]
   else:
      oldName = carCreatorProperties["Name"]
      carCreatorProperties["Name"] = entry.get()[0:20]
      nameCheck = carCreatorProperties["Name"]
   entry.delete(0, END)
   invalidChar = ("<" in nameCheck) or (">" in nameCheck) or (":" in nameCheck) or ("\\" in nameCheck) or ("/" in nameCheck) or ("\"" in nameCheck) or ("|" in nameCheck) or ("?" in nameCheck) or ("*" in nameCheck)
   location = "UserData/" + username + "/" + typ + "s/"
   folder = []
   if typ == "Car":
      folder = getFolderItems(location)
      start = 1
   else:
      folder = getFolderItems(location + "Code", "ITEM")
      start = 0
   if nameCheck == "Unnamed " + typ:
      messagebox.showwarning("Cannot Set " + typ + " Name", "The " + typ.lower() + " name is invalid\nPlease change the " + typ.lower() + " name")
      if typ == "Level":
         levelCreatorProperties["Name"] = oldName
      else:
         carCreatorProperties["Name"] = oldName
      return True
   else:
      for item in range(start, len(folder)):
         if nameCheck + ".txt" == folder[item] and typ == "Level":
            replace = messagebox.askyesno("Replace Existing Level", "There is already a level with that name\nDo you want to replace that level with this?")
            if replace:
               return False
            else:
               levelCreatorProperties["Name"] = oldName
               return True
         elif nameCheck == folder[item]:
            messagebox.showwarning("Cannot Set Car Name", "The car name already matches an existing name\nPlease change the car name")
            carCreatorProperties["Name"] = oldName
            return True
   if nameCheck == "":
      if typ == "Level":
         messagebox.showwarning("Cannot Set Level Name", "Please set a level name")
         levelCreatorProperties["Name"] = oldName
         return True
      else:
         if oldName == "Unnamed Car":
            messagebox.showwarning("Cannot Set Car Name", "Please set a car name")
            carCreatorProperties["Name"] = oldName
            return True
         else:
            carCreatorProperties["Name"] = oldName
            return False
   elif (not nameCheck.startswith(" ")) and (not nameCheck.endswith(" ")) and (invalidChar == False):
      if typ == "Car":
         os.rename("UserData/" + username + "/Cars/" + oldName, "UserData/" + username + "/Cars/" + nameCheck)
         return False
      else:
         if oldName != "Unnamed Level":
            try:
               os.rename("UserData/" + username + "/Levels/Code/" + oldName + ".txt", "UserData/" + username + "/Levels/Code/" + nameCheck + ".txt")
               return False
            except:
               return False
         else:
            return False
   else:
      messagebox.showwarning("Cannot Set " + typ + " Name", "The " + typ.lower() + " name is invalid\nPlease change the " + typ.lower() + " name")
      if typ == "Level":
         levelCreatorProperties["Name"] = oldName
      else:
         carCreatorProperties["Name"] = oldName
      return True

def createTextBox(fr, r, c, pword=False):
    if pword:
        box = Entry(fr, show="•", width=25)
    else:
        box = Entry(fr, width=25)
    box.grid(row=r, column=c, padx=3, pady=5)
    return box

def verifyUserDetails(mode, win, unameBox=None, oldPwordBox=None, pwordBox=None, confirmPwordBox=None):
   global username, menuMode, units, volume
   if unameBox != None:
      uname = unameBox.get()
   if oldPwordBox != None:
      oldPword = oldPwordBox.get()
   if pwordBox != None:
      pword = pwordBox.get()
   if confirmPwordBox != None:
     confirmPword = confirmPwordBox.get()
   invalidChar = ("<" in uname) or (">" in uname) or (":" in uname) or ("\\" in uname) or ("/" in uname) or ("\"" in uname) or ("|" in uname) or ("?" in uname) or ("*" in uname)
   error = False
   if mode == 1:
      contents = " "
      try:
        data = open("UserData/" + uname + "/data.bin", "rb")
        contents = pickle.load(data)
      except:
         if uname != "":
            error = True
            messagebox.showwarning("Error", "That username does not exist")
      if uname == "":
         error = True
         messagebox.showwarning("Error", "Please enter a username")
      if pword == "" and error == False:
         error = True
         messagebox.showwarning("Error", "Please enter a password")
      elif (contents[0] != pword and contents[0] != "") and error == False:
         error = True
         messagebox.showwarning("Error", "The password is incorrect")
      elif error == False:
         closeTk(win)
         username = uname
         units = contents[1]
         volume["Music"] = int(contents[2])
         volume["Sound"] = int(contents[3])
         volume["Engine"] = int(contents[4])
         pyg.mixer.Channel(0).set_volume(volume["Sound"] / 100)
         pyg.mixer.Channel(1).set_volume(volume["Engine"] / 100)
         pyg.mixer.Channel(2).set_volume(volume["Music"] / 100)
         pyg.mixer.Channel(3).set_volume(volume["Sound"] / 100)
         pyg.mixer.Channel(4).set_volume(volume["Sound"] / 100)
         data.close()
         menuMode = "MAIN_MENU"
   else:
      if mode in [2, 3]:
         if uname == "":
            error = True
            messagebox.showwarning("Error", "Please enter a username")
         elif " " in uname:
            error = True
            messagebox.showwarning("Error", "Username contains a space")
         elif uname.upper() in ["DEFAULT", "GUEST"]:
            error = True
            messagebox.showwarning("Error", "That username cannot be used")
         elif uname.startswith(" ") or uname.endswith(" ") or invalidChar:
            error = True
            messagebox.showwarning("Error", "The username is invalid\nPlease change the username")
         location = "UserData/"
         folder = getFolderItems(location)
         for item in range(1, len(folder)):
            if uname.upper() == folder[item].upper() and (uname.upper() != "GUEST" and uname.upper() != "DEFAULT"):
               error = True
               messagebox.showwarning("Error", "This username already exists")
      if mode in [2, 4]:
         if mode == 4:
           data = open("UserData/" + username + "/data.bin", "rb")
           contents = pickle.load(data)
           if oldPword == "":
               error = True
               messagebox.showwarning("Error", "Please enter your old password")
           elif oldPword != contents[0] and error == False:
               error = True
               messagebox.showwarning("Error", "The old password is incorrect")
           newword = " new"
           data.close()
         else:
            newword = ""
         if pword == "" and error == False:
            error = True
            messagebox.showwarning("Error", "Please enter a" + newword + " password")
         elif confirmPword == "" and error == False:
            error = True
            messagebox.showwarning("Error", "Please confirm your" + newword + " password")
         elif pword != confirmPword:
            error = True
            messagebox.showwarning("Error", "The two passwords do not match")
      if mode == 2 and error == False:
         closeTk(win)
         units = "METRIC"
         volume["Music"] = 100
         volume["Sound"] = 100
         volume["Engine"] = 100
         pyg.mixer.Channel(0).set_volume(volume["Sound"] / 100)
         pyg.mixer.Channel(1).set_volume(volume["Engine"] / 100)
         pyg.mixer.Channel(2).set_volume(volume["Music"] / 100)
         pyg.mixer.Channel(3).set_volume(volume["Sound"] / 100)
         pyg.mixer.Channel(4).set_volume(volume["Sound"] / 100)
         createAccount(uname, pword)
      elif mode == 3 and error == False:
         os.rename(location + username, location + uname)
         username = uname
         messagebox.showinfo("Username Changed", username + " is now your new username")
         closeTk(win)
      elif mode == 4 and error == False:
         data = open("UserData/" + username + "/data.bin", "rb")
         contents = pickle.load(data)
         data.close()
         contents[0] = pword
         data = open("UserData/" + username + "/data.bin", "wb")
         pickle.dump(contents, data)
         data.close()
         messagebox.showinfo("Password Changed", "You have successfully changed your password")
         closeTk(win)

def createAccount(uname, pword=""):
   global username, menuMode
   if pword == "":
      try:
         shutil.rmtree("UserData/Guest")
      except OSError:
         pass
   try:
      os.mkdir("UserData/" + uname)
      os.mkdir("UserData/" + uname + "/Cars")
      os.mkdir("UserData/" + uname + "/Levels")
      os.mkdir("UserData/" + uname + "/Levels/Code")
      os.mkdir("UserData/" + uname + "/Levels/Music")
      data = open("UserData/" + uname + "/data.bin", "wb")
      dataArray = [pword, "METRIC", 100, 100, 100]
      pickle.dump(dataArray, data)
      data.close()
      username = uname
      menuMode = "MAIN_MENU"
   except:
      fakeWin = Tk()
      fakeWin.withdraw()
      messagebox.showerror("Error creating account", "The account cannot be created. Make sure that any game related files/folders are closed before creating")
      closeTk(fakeWin)
      menuMode = "TITLE_SCREEN"

def editLevelProperties(win, frame):
    global levelCreatorProperties
    Label(frame, text="Advanced Properties", font=getFont(30, for_tk=True)).grid(row=0, column=0, columnspan=2)
    innerFrame = Frame(frame)
    innerFrame.grid(row=1, column=0, rowspan=1, columnspan=2, padx=5, pady=5)
    Label(innerFrame, text="Name:").grid(row=0, column=0)
    nameBox = createTextBox(innerFrame, 0, 1)
    if levelCreatorProperties["Name"] != "Unnamed Level":
       nameBox.insert(0, levelCreatorProperties["Name"])
    Label(innerFrame, text="(maximum 20 characters)").grid(row=1, column=1)
    Label(innerFrame, text="Laps:").grid(row=2, column=0)
    lapScale = Scale(innerFrame, from_=1, to_=50, orient=HORIZONTAL)
    lapScale.set(levelCreatorProperties["Laps"])
    lapScale.grid(row=2, column=1)
    instructionFrame = Frame(frame, highlightbackground="black", highlightthickness=1)
    instructionFrame.grid(row=2, column=0, rowspan=1, columnspan=2, padx=5, pady=5)
    Label(instructionFrame, text="Using code to edit a level:\n").grid(row=0)
    Label(instructionFrame, text="To create level code, there are five\n positions that determine a piece.").grid(row=1)
    Label(instructionFrame, text="Each position is separated by a comma (,).\nDo not use spaces in the code\nWrite each code in a new line").grid(row=2)
    Label(instructionFrame, text="The first position indicates whether the piece is a\nroad (\"road\"), a checkpoint (\"gate\") or a tree (\"tree\")").grid(row=3)
    Label(instructionFrame, text="For a road, the second position indicates whether the\nroad is a straight piece (1) or a turn (2).").grid(row=4)
    Label(instructionFrame, text="For a checkpoint, the second position indicates the order\nof each checkpoint, starting at 0.").grid(row=5)
    Label(instructionFrame, text="For a tree, the second position indicates the tree type (1 - 3)").grid(row=6)
    Label(instructionFrame, text="The third and forth position indicates the x and y\ncoordinates respectively.").grid(row=7)
    Label(instructionFrame, text="For a road or checkpoint, the fifth position indictates\nthe angle of the piece, in degrees.").grid(row=8)
    codeBox = Text(frame, width=25, height=27, undo=True)
    codeBox.grid(row=1, column=2, rowspan=2, columnspan=2, padx=5, pady=5)
    line = ""
    codeBox.delete(1.0, END)
    for i in range(len(levelCreatorProperties["Code"])):
       for j in range(len(levelCreatorProperties["Code"][i])):
          if j != len(levelCreatorProperties["Code"][i]) - 1:
             line = line + str(levelCreatorProperties["Code"][i][j]) + ","
          else:
             line = line + str(levelCreatorProperties["Code"][i][j]) + "\n"
    codeBox.insert(END, line)
    undoBtn = Button(frame, text="Undo", command=lambda:undo(codeBox))
    undoBtn.grid(row=0, column=2, padx=5, pady=5)
    redoBtn = Button(frame, text="Redo", command=lambda:redo(codeBox))
    redoBtn.grid(row=0, column=3, padx=5, pady=5)
    groundColBtn = Button(frame, text="Change Ground Colour", command=changeGroundCol)
    groundColBtn.grid(row=3, column=0, padx=5, pady=5)
    musicBtn = Button(frame, text="Add Soundtrack", command=addMusic)
    musicBtn.grid(row=3, column=1, padx=5, pady=5)
    applyBtn = Button(frame, text="Save & Apply", command=lambda:verifyCode(codeBox.get("1.0",END), nameBox, lapScale.get(), win))
    applyBtn.grid(row=3, column=2, padx=5, pady=5)
    closeBtn = Button(frame, text="Close", command=lambda:closeTk(win))
    closeBtn.grid(row=3, column=3, padx=5, pady=5)

def changeGroundCol():
   global levelCreatorProperties
   newCol = colorchooser.askcolor()
   if newCol != (None, None):
      levelCreatorProperties["Colour"] = newCol[0]

def addMusic():
   global levelCreatorProperties, mode
   if levelCreatorProperties["Name"] == "Unnamed Level":
      messagebox.showwarning("Set a level name", "Please set a level name before adding music")
   else:   
      win, frame = createTk("SOUND")
      win.title("Add Music")
      Label(frame, text="Import a WAV soundtrack that will play in the background of your level.\nFor best quality, make sure that the frequency is 48000 Hz.\nFor this to work, the WAV file must be 16-bit or lower.\nThis feature is optional.").grid(row=0, column=0, padx=5, pady=5, columnspan=5)
      importBtn = Button(frame, text="Import Soundtrack", command=lambda:importMusic(win))
      importBtn.grid(row=1, column=0, padx=5, pady=5)
      location = "UserData/" + username + "/Levels/Music/" + levelCreatorProperties["Name"] + ".wav"
      if os.path.exists(location):
         clearBtn = Button(frame, text="Remove Soundtrack", command=lambda:clearMusic(win))
         clearBtn.grid(row=1, column=1, padx=5, pady=5)
         playBtn = Button(frame, text="Play", command=lambda:playTk(location))
         playBtn.grid(row=1, column=2, padx=5, pady=5)
         stopBtn = Button(frame, text="Stop", command=stopTk)
         stopBtn.grid(row=1, column=3, padx=5, pady=5)
      closeBtn = Button(frame, text="Close", command=lambda:closeTk(win))
      closeBtn.grid(row=1, column=4, padx=5, pady=5)
      
def importMusic(win):
   global levelCreatorProperties, username
   location = filedialog.askopenfilename(title="Select Music Track", filetypes=[("WAVE Files (wav)","*.wav")])
   if location != "":
      try:
         os.remove("UserData/" + username + "/Levels/Music/" + levelCreatorProperties["Name"] + ".wav")
      except:
         pass
      name = location.split("/")[len(location.split("/")) - 1]
      shutil.copy(location, "UserData/" + username + "/Levels/Music/")
      os.rename("UserData/" + username + "/Levels/Music/" + name, "UserData/" + username + "/Levels/Music/" + levelCreatorProperties["Name"] + ".wav")
      closeTk(win)
      addMusic()

def clearMusic(win):
   global levelCreatorProperties, username
   os.remove("UserData/" + username + "/Levels/Music/" + levelCreatorProperties["Name"] + ".wav")
   closeTk(win)
   addMusic()
   
def undo(textWidget):
    try:
        textWidget.edit_undo()
    except Exception as e:
        pass

def redo(textWidget):
    try:
        textWidget.edit_redo()
    except Exception as e:
        pass
    
def verifyCode(code, entry, laps, win):
   global levelCreatorProperties, activeGate
   oldName = levelCreatorProperties["Name"]
   nameError = verifyName(entry, "Level")
   if nameError == False:
      entry.insert(0, levelCreatorProperties["Name"])
      codeList = []
      gateOrder = []
      line = code.split("\n")
      for position in line:
         if position != "":
            comma = position.split(",")
            codeList.append(comma)
      error = []
      if codeList == []:
         error.append("!code")
      else:
         if codeList[0] != ["road", "1", "0", "0", "0"]:
            error.append("!start")
         else:         
            for line in codeList:
               try:
                  if line[0] != "tree":
                     for position in range(5):
                        errorCheck = line[position]
                  else:
                     for position in range(4):
                        errorCheck = line[position]
               except:
                  error.append("!pos")
               if "!pos" not in error:
                  try:
                     if line[0] != "tree":
                        errorCheck = line[5]
                     else:
                        errorCheck = line[4]
                     error.append("!pos+")
                  except:
                     pass
                  if line[0] == "road":
                     if line[1] not in ["1", "2"]:
                        error.append("!piece")
                     if "!piece" not in error:
                        for position in range(2, 5):
                           try:
                              test = int(line[position])
                           except:
                              error.append("!int" + str(position))
                  elif line[0] == "gate":
                     gateOrder.append(int(line[1]))
                     for position in range(1, 5):
                        try:
                           test = int(line[position])
                        except:
                           error.append("!int" + str(position))
                  elif line[0] == "tree":
                     if line[1] not in ["1", "2", "3"]:
                        error.append("!piece")
                     if "!piece" not in error:
                        for position in range(2, 4):
                           try:
                              test = int(line[position])
                           except:
                              error.append("!int" + str(position))
                  else:
                     error.append("!track")
            if gateOrder == []:
               error.append("!gates")
            elif gateOrder != list(range(gateOrder[-1] + 1)):
               error.append("!gateorder")
      if error != []:
         message = ""
         if "!code" in error:
            message = message + "Please enter level code\n"
         if "!start" in error:
            message = message + "(road, 1, 0, 0, 0) must be the starting piece.\n"
         if "!pos" in error:
            message = message + "In order to place a track piece, there must be five positions. A tree must have four positions.\n"
         if "!pos+" in error:
            message = message + "Too many positions found. There must be five positions for all pieces except for trees, which have four positions.\n"
         if "!track" in error:
            message = message + "\"road\" must be used to add a new piece. \"gate\" must be used to add a checkpoint.\"tree\" must be used to add a tree\n"
         for position in range(1, 5):
            if "!int" + str(position) in error:
               message = message + "Position " + str(position) + " must be an integer.\n"
         if "!piece" in error:
            message = message + "Position 2 must indicate a straight road (1) or a turn (2). For a tree, Position 2 must indicate the type of tree being used (1-3).\n"
         if "!gates" in error:
            message = message + "There must be checkpoint gates in the level.\n"
         if "!gateorder" in error:
            message = message + "The gates are not in order properly. You can order gates by checking Position 2.\n"
         messagebox.showwarning("Error in Code", message)
      else:
         levelCreatorProperties["Code"] = codeList
         saveLevel(codeList, laps)
         location = "UserData/" + username + "/Levels/Music/"
         if os.path.exists(location + oldName + ".wav"):
            os.rename(location + oldName + ".wav", location + levelCreatorProperties["Name"] + ".wav")
         messagebox.showinfo("Level Saved", "Your level has been saved successfully")
         activeGate = 0
         levelCreatorProperties["Undo"] = []
         for line in codeList:
            if line[0] == "gate":
               activeGate += 1

def saveLevel(codeList, laps):
   global username, menuMode, levelCreatorProperties
   location = "UserData/" + username + "/Levels/Code/"
   file = open(location + levelCreatorProperties["Name"] + ".txt", "w")
   for position in codeList:
      if position[0] != "tree":
         line = str(position[0] + "," + position[1] + "," + position[2] + "," + position[3] + "," + position[4])
      else:
         line = str(position[0] + "," + position[1] + "," + position[2] + "," + position[3])
      file.write(line + "\n")
   file.write("name," + levelCreatorProperties["Name"])
   file.write("\n" + "ground," + str(int(levelCreatorProperties["Colour"][0])) + "," + str(int(levelCreatorProperties["Colour"][1])) + "," + str(int(levelCreatorProperties["Colour"][2])))
   file.write("\n" + "laps," + str(laps))
   file.close()
   
def getFolderItems(location, mode="DIRECTORY"):
   folder = []
   for d, i, r in os.walk(location):
      if mode == "DIRECTORY":
         folder.append(d.split("/")[len(location.split("/")) - 1])
      else:
         folder = r
   return folder

def getLvNum(location):
   lvNum = 0
   for path in os.listdir(location):
       if os.path.isfile(os.path.join(location, path)):
           lvNum += 1
   return lvNum

def closeTk(tkWin):
   stopTk()
   tkWin.destroy()

#MAIN PROGRAM STARTS HERE
           
run = True
key = {"Up" : False, "Down" : False, "Left" : False, "Right" : False, "Space" : False, "Enter" : False, "Escape" : False, "W" : False, "A" : False, "S" : False, "D" : False}
mode = "MAIN_MENU"
menuMode = "TITLE_SCREEN"
pieces = getPcs()
username = ""
units = "METRIC"
volume = {"Music" : 100, "Sound" : 100, "Engine" : 100}
level = randint(1, 5)
car = randint(0, 7)
carProperties, mode, car = getCars("Default", mode, car, load=True)
currentLap = 1
activeGate = 0
gatesCleared = 0
gateSprites = []
camera = [0, 0]
carPos = [0, 0]
velocity = 0
angle = 0
time = {"Second" : -3, "Minute" : 0}
quitCarCreator = False
editCarCreator = False
carCreatorProperties = {"Name" : "Unnamed Car", "Image" : None, "TopSpeed" : 1, "Acceleration" : 1, "Handling" : 1, "Offroad" : 1, "EngineType" : 0}
levelCreatorProperties = {"Name" : "Unnamed Level", "Colour" : [64, 201, 62], "Angle" : 0, "Type" : 1, "Laps" : 1, "PieceSelected" : False, "Code" : [["" for i in range(10)]], "Undo" : [], "ScaleFactor" : 1}
levelCreatorProperties["Code"][0] = ["road", 1, 0, 0, 0]
pausedVelocity = 0
enginePitch = 0
randomGates = []

pyg.mixer.init(48000, -16, 2, 4096)
pyg.init()
_font_cache = {}
sounds, engines = getSounds()
pyg.mixer.Channel(0).set_volume(volume["Sound"] / 100)
pyg.mixer.Channel(1).set_volume(volume["Engine"] / 100)
pyg.mixer.Channel(2).set_volume(volume["Music"] / 100)
pyg.mixer.Channel(3).set_volume(volume["Sound"] / 100)
pyg.mixer.Channel(4).set_volume(volume["Sound"] / 100)
levelProperties, mode = getLevels("Default", mode, load=True)
if level == 5:
   walls, randomGates = rebuildMaze()
#ctypes.windll.user32.SetProcessDPIAware()
#monitor = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
monitor = (1920, 1080)
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)
screen = (1920, 1080)
halfScreen = (screen[0] / 2, screen[1] / 2)
if monitor != screen:
   adjustedHeight = (screen[1] / screen[0]) * monitor[0]
   newMonitor = (monitor[0], int(adjustedHeight))
   window = pyg.Surface(screen)
   render = pyg.display.set_mode(newMonitor, pyg.NOFRAME | pyg.DOUBLEBUF)
else:
   window = pyg.display.set_mode(monitor, pyg.NOFRAME | pyg.DOUBLEBUF)
   newMonitor = screen
pyg.display.set_caption("Car Mania")
clock = pyg.time.Clock()
mousePos = pyg.mouse.get_pos()
clicked = pyg.mouse.get_pressed()
resetLevel(level)
timer = pyg.time.Clock()

while run:
   for event in pyg.event.get():
      if event.type == pyg.QUIT or mode == "QUIT":
         if username in ["Guest", ""]:
            try:
               shutil.rmtree("UserData/Guest")
            except OSError:
               pass
         run = False
      if event.type == pyg.MOUSEBUTTONDOWN:
         mouseDown = True
      elif event.type == pyg.MOUSEBUTTONUP:
         mouseDown = False
      if event.type == pyg.KEYDOWN:
         if event.key == pyg.K_UP:
             key["Up"] = True
         elif event.key == pyg.K_DOWN:
             key["Down"] = True
         elif event.key == pyg.K_LEFT:
             key["Left"] = True
         elif event.key == pyg.K_RIGHT:
             key["Right"] = True
         elif event.key == pyg.K_w:
             key["W"] = True
         elif event.key == pyg.K_s:
             key["S"] = True
         elif event.key == pyg.K_a:
             key["A"] = True
         elif event.key == pyg.K_d:
             key["D"] = True
         elif event.key == pyg.K_SPACE:
             key["Space"] = True
         elif event.key == pyg.K_RETURN:
             key["Enter"] = True
         elif event.key == pyg.K_ESCAPE:
            key["Escape"] = True
      if event.type == pyg.KEYUP:
         if event.key == pyg.K_UP:
             key["Up"] = False
         elif event.key == pyg.K_DOWN:
             key["Down"] = False
         elif event.key == pyg.K_LEFT:
             key["Left"] = False
         elif event.key == pyg.K_RIGHT:
             key["Right"] = False
         elif event.key == pyg.K_w:
             key["W"] = False
         elif event.key == pyg.K_s:
             key["S"] = False
         elif event.key == pyg.K_a:
             key["A"] = False
         elif event.key == pyg.K_d:
             key["D"] = False
         elif event.key == pyg.K_SPACE:
             key["Space"] = False
         elif event.key == pyg.K_RETURN:
             key["Enter"] = False
         elif event.key == pyg.K_ESCAPE:
            key["Escape"] = False
   if mode == "MAIN_MENU":
       if menuMode == "TITLE_SCREEN":
          username = ""
       mainMenu(window, level, camera)
   elif mode == "ENTER_DETAILS":
      pyg.mixer.Channel(1).stop()
      createTk(mode)
      mode = "MAIN_MENU"
   elif mode == "CREATE_ACCOUNT":
      pyg.mixer.Channel(1).stop()
      createTk(mode)
      mode = "MAIN_MENU"
   elif mode == "GUEST_ACCOUNT":
      units = "METRIC"
      volume["Music"] = 100
      volume["Sound"] = 100
      volume["Engine"] = 100
      pyg.mixer.Channel(0).set_volume(volume["Sound"] / 100)
      pyg.mixer.Channel(1).set_volume(volume["Engine"] / 100)
      pyg.mixer.Channel(2).set_volume(volume["Music"] / 100)
      pyg.mixer.Channel(3).set_volume(volume["Sound"] / 100)
      pyg.mixer.Channel(4).set_volume(volume["Sound"] / 100)
      createAccount("Guest")
      mode = "MAIN_MENU"
   elif mode == "MENU_OPTIONS":
      pyg.mixer.Channel(1).stop()
      createTk(mode)
      mode = "MAIN_MENU"
   elif mode == "PAUSED_OPTIONS":
      createTk(mode)
      mode = "PAUSED"      
   elif mode == "CREATE_CAR_DIRECTORY":
      os.mkdir("UserData/" + username + "/Cars/Unnamed Car/")
      editCarCreator = False
      mode = "CAR_CREATOR"
   elif mode == "CAR_CREATOR":
      pyg.mixer.Channel(1).stop()
      carCreator(window)
   elif mode == "IMPORT_IMAGE":
      carCreatorProperties["Image"] = importImage()
      mode = "CAR_CREATOR"
   elif mode == "CAR_OPTIONS":
      if carCreatorProperties["Image"] == None:
         fakeWin = Tk()
         fakeWin.withdraw()
         messagebox.showwarning("Cannot Open Properties", "Import a car image before editing the properties")
         closeTk(fakeWin)
      else:
         createTk(mode)
      mode = "CAR_CREATOR"
   elif mode == "EDIT_CAR":
      pyg.mixer.Channel(1).stop()
      createTk(mode)
      if mode != "CAR_CREATOR":
         mode = "MAIN_MENU"
   elif mode == "LEVEL_OPTIONS":
      createTk(mode)
      mode = "LEVEL_CREATOR"
   elif mode == "LEVEL_CREATOR_RESET":
      resetCreator("LEVEL_CREATOR")
      mode = "LEVEL_CREATOR"
   elif mode == "LEVEL_CREATOR":
      pyg.mixer.Channel(1).stop()
      levelCreator(window, camera)
   elif mode == "EDIT_LEVEL":
      pyg.mixer.Channel(1).stop()
      createTk(mode)
   elif mode == "GET_CARS_DEFAULT":
      pyg.mixer.Channel(1).stop()
      carProperties, mode, car = getCars("Default", mode, car)
   elif mode == "GET_CARS_USERNAME":
      carProperties, mode, car = getCars(username, mode, car)
   elif mode == "CAR_SELECT_DEFAULT":
      carSelect(window, "Default")
   elif mode == "CAR_SELECT_USERNAME":
      carSelect(window, username)
   elif mode == "GET_LEVELS_DEFAULT":
      level = 1
      levelProperties, mode = getLevels("Default", mode)
      resetLevel(level)
      walls, randomGates = rebuildMaze()
      mode = "LEVEL_SELECT_DEFAULT"
   elif mode == "GET_LEVELS_USERNAME":
      level = 1
      levelProperties, mode = getLevels(username, mode)
   elif mode == "LEVEL_SELECT_DEFAULT":
      levelSelect(window, "Default")
   elif mode == "LEVEL_SELECT_USERNAME":
      levelSelect(window, username)
   elif mode == "RESET_TIMER":
      resetLevel(level)
      pyg.mixer.Channel(1).play(engines[carProperties["Engine"][car]][0], loops=-1)
      if levelProperties["Music"][level - 1] != None:
         pyg.mixer.Channel(2).play(levelProperties["Music"][level - 1], loops=-1)
      timer = pyg.time.Clock()
      mode = "PLAY_GAME"
   elif mode == "PLAY_GAME":
      playGame(window, camera, timer)
   elif mode == "PAUSED":
      pyg.mixer.Channel(1).stop()
      pyg.mixer.Channel(2).pause()
      r, g, b = invertCol(levelProperties["Colour"][level][0], levelProperties["Colour"][level][1], levelProperties["Colour"][level][2])
      pauseMenu(window, camera, [r, g, b])
   elif mode == "UNPAUSE":
      velocity = pausedVelocity
      pyg.mixer.Channel(1).play(engines[carProperties["Engine"][car]][enginePitch], loops=-1)
      pyg.mixer.Channel(2).unpause()
      timer = pyg.time.Clock()
      mode = "PLAY_GAME"
   elif mode == "WIN":
      finishedLevel(window, camera, mode)
   if monitor != (1920, 1080):
      scale = pyg.transform.scale(window, newMonitor)
      scaleNum = (1920 / newMonitor[0], 1080 / newMonitor[1])
      mp = pyg.mouse.get_pos()
      mousePos = (mp[0] * scaleNum[0], mp[1] * scaleNum[1])
      render.blit(scale, (0, 0))
   else:
      mousePos = pyg.mouse.get_pos()  
   clicked = pyg.mouse.get_pressed()
   pyg.display.update()
   clock.tick(60) #FPS
pyg.quit()
