
import requests

def verifyPayments(reference):
    purl = f"https://api.paystack.co/transaction/verify/{reference}"

    print("purl: ", purl)


    headers = {
            "Authorization": f"Bearer sk_test_de93288b38ea5cbd9b946c34ef92308cfe7d32b8"  # Replace with your actual token
        }
    response = requests.get(purl, headers=headers)

    if response.status_code == 200:

            # Access JSON content:
        json_content = response.json()
        if json_content["data"] and json_content["data"]["status"] == "success":
            return 1
        else:
            return 0
    else:
        print("Error:", response)
        return None
