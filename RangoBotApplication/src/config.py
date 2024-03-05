from os import environ as env

from dotenv import load_dotenv
load_dotenv()

TOKEN = env['TOKEN']
MANIFEST_URL = env['MANIFEST_URL']
RANGO_API_KEY = env['RANGO_API_KEY']
RANGO_BASE_URL = env['RANGO_BASE_URL']