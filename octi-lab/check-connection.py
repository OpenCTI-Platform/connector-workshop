from pycti import OpenCTIApiClient

client = OpenCTIApiClient(
    url="http://localhost:8080",   # your platform URL
    token="flgrn_octi_tkn_TV-ecuyWhtPWp2-PsuKAaeMjqodaHyuMbMZYHuONzP1nVPHlnepea3_Yf2C2qLSe",            # your API token
)
print(client.query("query { about { version } }"))