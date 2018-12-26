from os import urandom
from base64 import b64encode
print(b64encode(urandom(24)).decode('utf-8'))
