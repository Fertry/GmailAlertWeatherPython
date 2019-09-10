from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Librerias de Adafruit y otras:
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

# Hemos añadido esta libreria para los posibles errores:
import httplib2

# Variables editables rapidamente:
GMAIL_QUERY = "in:inbox is:unread"
EMAIL_ADDRESS = "youremail@gmail.com"
TEXT = "Sin leer: "
DELAY_TIME = 10 
SCREENSAVER_TIME_BEGIN = "00:00:00" 
SCREENSAVER_TIME_END = "07:30:00"
OPEN_WEATHER_MAP_API_KEY = "NUESTRA API"
OPEN_WEATHER_MAP_LOCATION = "seville,es"
OPEN_WEATHER_MAP_TEMP_SCALE = "celsius"

# Configuracion de pins de la Raspberry:
# Este pin no se usa.
RST = None    

# Tipo de pantalla:
display = Adafruit_SSD1306.SSD1306_128_64(rst = RST) 

# Inicializamos la pantalla:
display.begin()
display.clear()
display.display()

# Creamos una imagen en "blanco" para dibujar:
width = display.width
height = display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Creamos un rectangulo negro para llenar la pantalla:
draw.rectangle((0,0,width,height), outline = 0, fill = 0)

# Fuente que usaremos para escribir:
font = ImageFont.truetype("Arial.ttf", 16)
font_email = ImageFont.truetype("Arial.ttf", 11)
font_sky = ImageFont.truetype("Arial", 12)

# Constantes:
padding = -2
top = padding
bottom = height - padding
x = 0

# IP de la Raspberry:
cmd = "hostname -I | cut -d\' \' -f1"
IP = subprocess.check_output(cmd, shell = True )
IP = re.search( r'[0-9]+(?:\.[0-9]+){3}', str(IP) ).group()

# Creamos una instacion de pyowm y le pasamos nuestra API:
owm = pyowm.OWM(OPEN_WEATHER_MAP_API_KEY) 

# Obtenemos los datos para nuestra ubicacion:
observation = owm.weather_at_place(OPEN_WEATHER_MAP_LOCATION)
w = observation.get_weather()

# Obtenemos la temperatura (importante el redondeo):
temperature = round(w.get_temperature(OPEN_WEATHER_MAP_TEMP_SCALE)['temp'])

# Obtenemos la informacion del tiempo:
sky = w.get_detailed_status()

# Almacenamos el tiempo de mañana:
tomorrows_sky = ''
tomorrows_temp = ''

# Actualizamos el tiempo actual:
current_time = datetime.datetime.now()
current_time_adjusted = current_time + datetime.timedelta(days =+ 1)

# Obtenemos la prevision para 3 dias:
prevision_3_dias = owm.three_hours_forecast(OPEN_WEATHER_MAP_LOCATION)
prevision = prevision_3_dias.get_forecast()

for weather in prevision:
    
  ref_time = weather.get_reference_time('date').replace(tzinfo = None)
  compare = current_time_adjusted > ref_time
    
  if (compare is False):
        
    tomorrows_sky = weather.get_detailed_status()
    tomorrows_temp = round(weather.get_temperature(OPEN_WEATHER_MAP_TEMP_SCALE)['temp'])
    print(weather.get_temperature(OPEN_WEATHER_MAP_TEMP_SCALE))
    print("tomorrows_sky", tomorrows_sky)
    print("tomorrows_temp", tomorrows_temp)
    print("weather.get_reference_time('iso')", weather.get_reference_time('iso'))
    break

print("Temperatura:", temperature)
print("Estado:", sky)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Funcion contadora:
def contadorMensajes(service, user_id, query = ''):
    
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
  
  try:
      
    response = service.users().mensajes().list(userId = user_id, q = query).execute()
    mensajes = []
    
    if 'mensajes' in response:
        
      mensajes.extend(response['mensajes'])

    while 'nextPageToken' in response:
        
      page_token = response['nextPageToken']
      response = service.users().mensajes().list(userId = user_id, q = query, pageToken = page_token).execute()
      mensajes.extend(response['mensajes'])

    return mensajes
    
  except:
      
    print('Ha ocurrido un error.')

# Funcion principal:
def main():
    
  """
  Muestra el uso básico de la API de Gmail.
  Enumera las etiquetas de Gmail del usuario.
  """
    
  credenciales = None
    
  # El archivo token.pickle almacena los tokens de acceso y actualización del usuario, y es
  # creado automáticamente cuando se completa el proceso de autorización por primera vez.
  # Hablaremos de esto luego.
    
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
  api = build('gmail', 'v1', credentials = credenciales)
	
  contador = len(contadorMensajes(api, "me", GMAIL_QUERY))
  text_modified = TEXT

  if (int(contador) is 1 and TEXT.endswith('s')):
    
		text_modified = TEXT[:-1]

	# Creamos un rectangulo negro para llenar la pantalla:
  draw.rectangle((0,0,width,height), outline = 0, fill = 0)

	# Dibujamos cada linea de texto que hemos definido antes:
  draw.text((x, top), str(contador) + " " + text_modified, font = font, fill = 255)
  draw.text((x, top + 19), str(temperature) + "°" + " / " + str(tomorrows_temp) + "°", font = font, fill = 255)
  draw.text((x, top + 38), str(sky.title() + " / " + tomorrows_sky.title()), font = font_sky, fill = 255)
  draw.text((x, top + 54), "IP: " + str(IP), font = font_email, fill = 255)

	# Mostramos la imagen:
  display.image(image)
  display.display()

	# Mostramos el contador en la consola:
  print("Sin leer: ", contador)

if __name__ == '__main__':
    
    # Ejecuta el script de forma indefinida hasta que encuentre un error:
    
	while True:
	    
		current_time = datetime.datetime.now()
		
		t1_begin = datetime.datetime.now()
		t2_end = datetime.datetime.now()

		t1_begin_list = SCREENSAVER_TIME_BEGIN.split(":") # "05:30:00" -> ["05", "30", "00"]
		t2_end_list = SCREENSAVER_TIME_END.split(":") # "08:00:00" -> ["08", "00", "00"]

		t1_begin = t1_begin.replace(hour = int(t1_begin_list[0]), minute = int(t1_begin_list[1]), second = int(t1_begin_list[2]))
		t2_end = t2_end.replace(hour = int(t2_end_list[0]), minute = int(t2_end_list[1]), second = int(t2_end_list[2]))

		time_delta = t2_end - t1_begin

		if (time_delta.total_seconds() < 0):
		    
			t2_end_adjusted = t2_end + datetime.timedelta(days =+ 1)
			
		else:
		    
			t2_end_adjusted = time_delta + t1_begin

		if (current_time <= t1_begin or current_time >= t2_end_adjusted):
			
			try:

				main()
				
			except:

				print("Se encontro un error")

		else:

			# Dibuja un rectangulo negro:
			draw.rectangle((0,0, width, height), outline = 0, fill = 0)
			display.image(image)
			display.display()
			print("Durmiendo...")
	
		time.sleep(DELAY_TIME)
