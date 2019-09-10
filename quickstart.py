###################################################################################
###################################################################################
#ALEJANDRO FDEZ - fertry.tech
###################################################################################
###################################################################################

from __future__ import print_function
import pickle
import os.path
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess
import re
import time
import datetime
import pyowm

# Variables editables rapidamente:
GMAIL_QUERY = "in:inbox is:unread"
EMAIL_ADDRESS = "NUESTRO_EMAIL"
TEXT = "Sin leer"
DELAY_TIME = 60 
OPEN_WEATHER_MAP_API_KEY = "NUESTRA_API"
OPEN_WEATHER_MAP_LOCATION = "seville,es"
OPEN_WEATHER_MAP_TEMP_SCALE = "celsius"

# Tipo de pantalla e inicialización de la misma:
RST = None  # Este pin no se usa.
display = Adafruit_SSD1306.SSD1306_128_64(rst = RST) 
display.begin()
display.clear()
display.display()

# Creamos una imagen en "blanco" para dibujar y
# un rectangulo negro para llenar la pantalla:
width = display.width
height = display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline = 0, fill = 0)

# Fuentes que usaremos para escribir:
font = ImageFont.truetype("Arial.ttf", 16)
font_email = ImageFont.truetype("Arial.ttf", 11)
font_sky = ImageFont.truetype("Arial.ttf", 12)

# Constantes para la posicion en pantalla:
padding = -2
top = padding
bottom = height - padding
x = 0

# IP de la Raspberry formateado con re:
cmd = "hostname -I | cut -d\' \' -f1"
IP = subprocess.check_output(cmd, shell = True )
IP = re.search( r'[0-9]+(?:\.[0-9]+){3}', str(IP) ).group()

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Funcion contadora:
def contadormessages(service, user_id, query = ''):
    
  """
  Cuenta el numero de emails que cumplen una condición.

  Argumentos:
    *service: API autorizada de Gmail.
    *user_id: nuestro email. Usamos la etiqueta "me" que representa a todos
    los emails dirigidos a nuestra cuenta.
    *query: condición que han de cumplir dichos emails para que sean contados.

  Salida:
    *Numero de emails que cumplen dicha condición (query).
  """

  ###################################################################################
  ###################################################################################
  #ESTE BLOQUE CORRESPONDE AL CONTADOR DE EMAILS NO LEIDOS
  ###################################################################################
  ###################################################################################
  
  try:
      
    response = service.users().messages().list(userId = user_id, q = query).execute()
    messages = []
    
    if 'messages' in response:
        
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
        
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId = user_id, q = query, pageToken = page_token).execute()
      messages.extend(response['messages'])

    return messages
    
  except:
      
    print('Ha ocurrido un error')

# Funcion principal:
def main():
  
  ###################################################################################
  ###################################################################################
  #ESTE BLOQUE CORRESPONDE A LA AUTENTICACIÓN DEL USUARIO
  ###################################################################################
  ###################################################################################

  credenciales = None
    
  # El archivo token.pickle almacena los tokens de acceso y actualización del usuario, y es
  # creado automáticamente cuando se completa el proceso de autorización por primera vez.
  # Documentacion: https://developers.google.com/gmail/api/quickstart/python
    
  if os.path.exists('token.pickle'):
        
    with open('token.pickle', 'rb') as token:
            
      credenciales = pickle.load(token)
    
  # Si no hay credenciales validas permite al usuario hacer log-in:
  if not credenciales or not credenciales.valid:
        
    if credenciales and credenciales.expired and credenciales.refresh_token:
            
      credenciales.refresh(Request())
            
    else:
            
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
      credenciales = flow.run_local_server(port = 0)
        
    # Guarda las credenciales para la siguiente ejecución:
    with open('token.pickle', 'wb') as token:
            
      pickle.dump(credenciales, token)
    
  # API de Gmail:
  api = discovery.build('gmail', 'v1', credentials = credenciales)
	
  # Contador de emails no leidos:
  contador = len(contadormessages(api, "me", GMAIL_QUERY))

  ###################################################################################
  ###################################################################################
  #ESTE BLOQUE CORRESPONDE A LA INFORMACION DEL TIEMPO
  ###################################################################################
  ###################################################################################

  # Creamos una instacion de pyowm y le pasamos nuestra API:
  owm = pyowm.OWM(OPEN_WEATHER_MAP_API_KEY) 

  # Obtenemos los datos para nuestra ubicacion:
  observation = owm.weather_at_place(OPEN_WEATHER_MAP_LOCATION)
  w = observation.get_weather()

  # Obtenemos la temperatura (importante el redondeo):
  temperature = round(w.get_temperature(OPEN_WEATHER_MAP_TEMP_SCALE)['temp'])

  # Obtenemos la informacion del tiempo:
  sky = w.get_detailed_status()

  ###################################################################################
  ###################################################################################
  #IMPRIMIMOS LOS DATOS EN CONSOLA PARA DEBUGGING
  ###################################################################################
  ###################################################################################

  print("Temperatura:", temperature)
  print("Estado:", sky)
  print("Sin leer: ", contador)

  ###################################################################################
  ###################################################################################
  #MOSTRAMOS LOS DATOS POR PANTALLA
  ###################################################################################
  ###################################################################################

  # Creamos un rectangulo negro para llenar la pantalla:
  draw.rectangle((0,0,width,height), outline = 0, fill = 0)

  # Dibujamos cada linea de texto que hemos definido antes:
  # El contador
  # La temperatura
  # El estado del tiempo
  # La IP de la Raspberry
  draw.text((x, top), str(contador) + " " + TEXT, font = font, fill = 255)
  draw.text((x, top + 19), str(temperature) + "°", font = font, fill = 255)
  draw.text((x, top + 38), str(sky.title()), font = font_sky, fill = 255)
  draw.text((x, top + 54), "IP: " + str(IP), font = font_email, fill = 255)

  # Mostramos la imagen:
  display.image(image)
  display.display()

###################################################################################
###################################################################################
#BUCLE DEL PROGRAMA
###################################################################################
###################################################################################

if __name__ == '__main__':

  while True:

    if (datetime.datetime.now().hour >= 24 and datetime.datetime.now().hour <= 6):

      draw.rectangle((0,0, width, height), outline = 0, fill = 0)
      display.image(image)
      display.display()
      print("Durmiendo.....")
      
    else:

      try:

        main()

      except:

        print("Se encontro un error")

    time.sleep(DELAY_TIME)
