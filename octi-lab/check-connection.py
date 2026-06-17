from pycti import OpenCTIApiClient

client = OpenCTIApiClient(
    url="http://localhost:8080",   # your platform URL
    token="REPLACE_ME",            # your API token
)
print(client.query("query { about { version } }"))