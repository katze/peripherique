from vidgear.gears import CamGear
import cv2
import numpy as np
import pygame
import time
import random

from pygame import mixer


mixer.pre_init()
mixer.init()
pygame.init()

# Fabrication de la fenêtre Pygame
screen = pygame.display.set_mode((1280,720))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 40)
pygame.display.set_caption("Partition urbaine - Périphérique nord - Lyon - Porte du Valvert")

# Ajout d'une musique d'ambiance
pygame.mixer.music.load('sounds/lyon/looperman-l-4853273-0296439-2023-bass-part-3.wav')
pygame.mixer.music.play(-1)

# Chargement du flux vidéo
options = {"STREAM_RESOLUTION": "720p"}
stream = CamGear(source='https://youtu.be/WdgZIE0T4Gs', stream_mode = True, logging=True, **options).start() # YouTube Video URL as input
#stream = CamGear(source='videos/lyon_1500.mp4', stream_mode = False, logging=True, **options).start() # YouTube Video URL as input
#stream = CamGear(source='videos/lyon_midi.mp4', stream_mode = False, logging=True, **options).start() # YouTube Video URL as input


showDebugInfos = True
frame_count = 0
previous_frame = None
previousContours = 0
prev_frame_time = 0
new_frame_time = 0

# Définition d'une classe permettant de définir un son et la zone dans laquelle il est joué
class Sound:
    def __init__(self, name, channel, coords, radius, file_path, volume, durationTimeout, solo=True, debounce=0.5, mute=False, picture_path=None, picture_size=None):
        self.name = name                        # Nom du son
        self.channel = channel                  # Channel du son
        self.file_path = file_path              # Chemin vers le fichier audio (peut être un tableau pour choisir un son aléatoirement)
        self.coords = coords                    # Coordonnées du centre du cercle
        self.radius = radius                    # Rayon du cercle
        self.volume = volume                    # Volume du son (peut être un tuple pour (left, right))
        self.durationTimeout = durationTimeout  # Durée avant de stopper le son (0 pour ne pas stopper)
        self.solo = solo                        # Si True, le son interrompt les autres sons du meme channel
        self.debounce = debounce                # Temps avant de rejouer le son
        self.mute = mute                        # Mute le son
        self.picture_path = picture_path        # Image permettant de représenter le son
        self.picture_size = picture_size        # Taille de l'image


        self.last_touched = time.time()
        self.last_played = time.time()

        self.isPlaying = False
       
        self.instrumentOn = False
        self.instrumentOff = False

        if self.picture_path:
            instrumentPicture = pygame.image.load(self.picture_path)
            instrumentPicture = pygame.transform.scale(instrumentPicture, (self.picture_size[0], self.picture_size[1]))

            self.instrumentOn = instrumentPicture
            self.instrumentOff = instrumentPicture.copy()
            self.instrumentOff.set_alpha(128)
            

    # Une voiture touche le son
    def over(self):

        if self.mute:
            return

        # Si le son est affecté à un channel, on le joue uniquement si le channel n'est pas en cours de lecture
        self.last_touched = time.time()
        #Si le channel n'est pas en cours de lecture ou self.solo is False on joue le son
        if not pygame.mixer.Channel(self.channel).get_busy() or not self.solo:

            # Joue le son seulement si il a été joué plus de self.debounce secondes
            if (time.time() - self.last_played) > self.debounce:
                pygame.mixer.Channel(self.channel).set_volume(*self.volume)
                self.isPlaying = True

                # Si self.file_path est un tableau, on choisit un son aléatoirement
                if isinstance(self.file_path, list):
                    audio_file = random.choice(self.file_path)
                else:
                    audio_file = self.file_path

                pygame.mixer.Channel(self.channel).play(pygame.mixer.Sound(audio_file))
                self.last_played = time.time()
            
    # Aucune voiture ne touche le son
    def notOver(self):

        # Si self.solo is True, on ne stoppe pas le channel
        if not self.solo:
            if (time.time() - self.last_touched) > self.debounce:
                self.isPlaying = False
        if self.durationTimeout and (time.time() - self.last_touched) > self.durationTimeout:
            pygame.mixer.Channel(self.channel).stop()
            self.isPlaying = False



    def draw(self, frame):

        if showDebugInfos:
            if self.mute:
                pygame.draw.circle(frame, (125, 125, 125), self.coords, self.radius, 2)
            elif self.isPlaying:
                 pygame.draw.circle(frame, (255, 255, 255), self.coords, self.radius)
            else:
                pygame.draw.circle(frame, (255, 255, 255), self.coords, self.radius, 2)
            
            text = font.render(self.name, True, (0, 0,0))
            frame.blit(text, (int(self.coords[0]-text.get_rect().width/2), int(self.coords[1]-text.get_rect().height/2)))


        else:

            if self.instrumentOn:
                width, height = self.instrumentOn.get_rect().size   
                if pygame.mixer.Channel(self.channel).get_busy():
                    frame.blit(self.instrumentOn, ( int(self.coords[0]-width/2), int(self.coords[1]-height/2)))
                else:
                    frame.blit(self.instrumentOff, ( int(self.coords[0]-width/2), int(self.coords[1]-height/2)))
            else:
                if self.isPlaying:
                    pygame.draw.circle(frame, (255, 255, 255), self.coords, self.radius)
                else:
                    pygame.draw.circle(frame, (255, 255, 255), self.coords, self.radius, 2)
                    # Write the name of the sound in the circle

    def mute(self):
        self.mute = True
    
    def unmute(self):
        self.mute = False

    def toggle_mute(self):
        self.mute = not self.mute



# Création d'une liste de sons
sounds = [

    Sound(  name="1",                           # Nom du son
            channel=0,                          # Canal de lecture du son
            solo=True,                          # Si le son peut être joué en même temps que d'autres sons du même canal
            coords=(40, 50),                    # Coordonnées de la zone de lancement du son
            radius=10,                          # Rayon de la zone de lancement du son
            file_path="sounds/lyon/cloche.wav", # Chemin du son
            volume=(1.0, 0.0),                  # Volume du son
            durationTimeout=1),                 # Durée après lequel le son s'arrete si la zone n'est pas touchée de nouveau

    Sound(  name="2",
            channel=1,
            solo=True,
            coords=(150, 70),
            radius=20,
            file_path="sounds/lyon/clochette.wav",
            volume=(1.0, 0.0),
            durationTimeout=1),
            
    Sound(  name="3",
            channel=2,
            solo=False,
            coords=(236, 183),
            radius=20,
            file_path= [ "sounds/lyon/170_BsphrsMsVn20In_262_10.wav"],
            volume=(1.0, 0.0),
            durationTimeout=1,
            debounce=1,
            picture_path="images/instruments/cymbals.png",
            picture_size=(100, 100),
            mute=False),

    Sound(  name="4",
            channel=3,
            solo=True,
            coords=(108, 645),
            radius=60,
            file_path= "sounds/lyon/conga.wav",
            picture_path="images/instruments/conga.png",
            picture_size=(100, 100),
            volume=(1.0, 0.0),
            durationTimeout=1),


   Sound(  name="5",
            channel=4,
            solo=False,
            coords=(680, 100),
            radius=20,
            file_path= "sounds/glockenspiel/glockenspiel_00003.wav",
            volume=(0.2, 0.2),
            durationTimeout=False,
            picture_path="images/instruments/xylophone.png",
            picture_size=(50, 50),

            debounce=1),
   
   Sound(  name="5",
            channel=4,
            solo=False,
            coords=(626, 127),
            radius=20,
            file_path= "sounds/glockenspiel/glockenspiel_00009.wav",
            volume=(0.2, 0.2),
            durationTimeout=False,
            picture_path="images/instruments/xylophone.png",
            picture_size=(50, 50),
            debounce=1),

   Sound(  name="5",
            channel=4,
            solo=False,
            coords=(571, 160),
            radius=20,
            file_path= "sounds/glockenspiel/glockenspiel_00001.wav",
            volume=(0.2, 0.2),
            durationTimeout=False,
            picture_path="images/instruments/xylophone.png",
            picture_size=(50, 50),
            debounce=1),

   Sound(  name="5",
            channel=4,
            solo=False,
            coords=(441, 241),
            radius=40,
            file_path= "sounds/glockenspiel/glockenspiel_00007.wav",
            volume=(0.2, 0.2),
            durationTimeout=False,
            picture_path="images/instruments/xylophone.png",
            picture_size=(80, 80),
            debounce=1),

    Sound(  name="6",
            channel=5,
            solo=True,
            coords=(680, 250),
            radius=40,
            #file_path= ["sounds/lyon/Choir/G#2.wav", "sounds/lyon/Choir/A#2.wav", "sounds/lyon/Choir/A2.wav" ],
            file_path= ["sounds/lyon/124_Em_Floating_SP_91_01.wav", "sounds/lyon/Choir/A#2.wav",  "sounds/lyon/120_Dm_Jazz_A1_229_Trumpet.wav" ],
            volume=(0.5, 0.5),
            picture_path="images/instruments/chorale.png",
            picture_size=(100, 100),
            durationTimeout=3.5),

    Sound(  name="7",
            channel=6,
            solo=True,
            coords=(660, 520),
            radius=50,
            file_path= ["sounds/lyon/120bmp_guitare.wav"],
            volume=(0.3, 1.5),
            durationTimeout=3),

    Sound(  name="8",
            channel=7,
            solo=True,
            coords=(1213, 120),
            radius=40,
            file_path= ["sounds/lyon/120_Shakerloop_SP_14_406.wav"], #, "sounds/lyon/looperman-l-0747210-0112014-ferryterry-90-bpm-latin-guitar.wav"
            picture_path="images/instruments/maracas.png",
            picture_size=(100, 100),
    
            volume=(0.0, 0.5),
            durationTimeout=2),

]



def update_fps():
	fps = str(int(clock.get_fps()))
	fps_text = font.render(fps, 1, pygame.Color("coral"))
	return fps_text


loop = 1
while loop:
    frame_count += 1
    
    # On skip une frame sur 3 pour rester fluide sur un raspberry pi
    if frame_count % 3 == 0:
        continue

    frame = stream.read()

    out =  cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    out = pygame.image.frombuffer(out.tobytes(), frame.shape[1::-1], "RGB")


    # Pas la peine d'avoir une image en full hd, on se contente de 720p
    frame = cv2.resize(frame, (1280, 720))

    # Prépare une frame de travail en niveau de gris de la moitée de la taille de l'image pour alléger le traitement
    prepared_frame = cv2.resize(frame, (int(1280/2), int(720/2)))
    prepared_frame = cv2.cvtColor(prepared_frame, cv2.COLOR_BGR2GRAY)
    prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5, 5), sigmaX=0)

    if (previous_frame is None):
      previous_frame = prepared_frame
      continue
    
    # On calcule la différence entre la frame précédente et la frame courante
    diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)
    previous_frame = prepared_frame

    # On dilue un peu l'image pour rendre les différences plus visibles et améliorer la détection de contour
    kernel = np.ones((5, 5))
    diff_frame = cv2.dilate(diff_frame, kernel, 1)

    # On ne garde que les zones qui ont des différentes importantes (>20 / 255)
    thresh_frame = cv2.threshold(src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

    # On cherche les contour de ces zones
    contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
    # cv2.drawContours(image=frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
    for contour in contours:

      # Si l'air du contour est trop petit, on ne le traite pas 
      if cv2.contourArea(contour) < 250:
        # trop petit: skip!
          continue
      (x, y, w, h) = cv2.boundingRect(contour)

      #On recalcule les coordonnées du contour en fonction de la taille de l'image
      x = int(x * 2)
      y = int(y * 2)
      w = int(w * 2)
      h = int(h * 2)

      pygame.draw.rect(out, (0, 255, 0), (x, y, w, h), 2);
      cv2.rectangle(img=frame, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)
      for sound in sounds:
        # On regarde si le rectangle est dans la zone d'activation du son
        if (x < sound.coords[0] + sound.radius and x + w > sound.coords[0] - sound.radius and y < sound.coords[1] + sound.radius and y + h > sound.coords[1] - sound.radius):
          sound.over()
        else:
          sound.notOver()


    # Remove duplicate Frame (YT semble dupliquer une frame toutes les 5 frames)
    if(len(contours) == 0 and previousContours != 0):
        previousContours = len(contours)
        continue
    previousContours = len(contours)


    # show sounds
    for sound in sounds:
        sound.draw(out)

    screen.blit(out, (0,0))


    #screen.blit(update_fps(), (10,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop = 0

        if event.type == pygame.KEYDOWN :
            if event.key == pygame.K_ESCAPE:
                loop = 0

            if event.key == pygame.K_d:
                showDebugInfos = not showDebugInfos

            if event.key in range(48, 58):

                for sound in sounds:
                    if sound.name == str(event.key-48):
                        sound.toggle_mute()

    clock.tick(25)
    pygame.display.update()
 
stream.stop()
pygame.quit()
