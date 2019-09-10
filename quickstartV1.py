from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
      
    response = service.users().messages().list(userId = user_id, q = query).execute()
    mensajes = []
    
    if 'mensajes' in response:
        
      mensajes.extend(response['mensajes'])

    while 'nextPageToken' in response:
        
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId = user_id, q = query, pageToken = page_token).execute()
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
    
    # Contador de emails + condición:
    contador = len(contadorMensajes(api, "me", "in:inbox is:unread"))

    print("Sin leer: ", contador)

# Ejecutamos nuestro script:
if __name__ == '__main__':
    
    main()
