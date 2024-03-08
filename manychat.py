import os
import openai
import json
import requests

flow_id = "content20240121115201_780259"
manychatKEY = os.getenv("MANYCHAT_KEY")
# apiUrl = 1028541149
apiUrl =  "http://fash1.pythonanywhere.com"
# apiUrl =  os.getenv("API_URL")http://fash1.pythonanywhere.com/

print("mk: ", manychatKEY)
print("api_url: ", apiUrl)


def sendFlow(contactId):
    manychatSendFlowUrl = "https://api.manychat.com/fb/sending/sendFlow"

    headers = {
     "Authorization": f"Bearer {manychatKEY}"  # Use f-string formatting for clarity
    }

    body = {
        "subscriber_id": contactId,
        "flow_ns": flow_id
    }

    response = requests.post(manychatSendFlowUrl, data=body, headers=headers)

    if response.status_code == 200:

        # Access JSON content:
        json_content = response.json()
        print("JSON content:", json_content)
        return json_content
    else:
        print("Error:", response)
        return None