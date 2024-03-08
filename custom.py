from fuzzywuzzy import fuzz
import os
import openai
import json
import requests
import redis

os.environ['MANYCHAT_KEY'] = '376259:06deb193ce1ffafcf0db8e6adeb1ed3d'
os.environ['OPENAI_API_KEY'] = ''


openai_api_key = os.environ.get("OPENAI_API_KEY")

print("key: ", openai_api_key)

apiUrl =  'http://fash1.pythonanywhere.com'

# print("mk: ", manychatKEY)
print("api_url: ", apiUrl)


functions = [
    {
        "name": "get_pizza_info",
        "description": "Get name and price of a pizza of the restaurant",
        "parameters": {
            "type": "object",
            "properties": {
                "pizza_name": {
                    "type": "string",
                    "description": "The name of the pizza, e.g. Hawaii",
                },
            },
            "required": ["pizza_name"],
        },
    },
    {
        "name": "get_pizza_menu",
        "description": "Get name, ingredients and price of all pizza in the restaurant",
        "parameters": {
            "type": "object",
            "properties": {
                # "pizza_name": {
                #     "type": "string",
                #     "description": "The name of the pizza, e.g. Hawaii",
                # },
            },
            "required": [],
        },
    },
    {
        "name": "get_user_info",
        "description": "Get email address of customer",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The email of the customer",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_merchant_list",
        "description": "Get names and ids of all merchants in the system",
        "parameters": {
            "type": "object",
            "properties": {
                # "pizza_name": {
                #     "type": "string",
                #     "description": "The name of the pizza, e.g. Hawaii",
                # },
            },
            "required": [],
        },
    },
    {
        "name": "get_merchant_details",
        "description": "Get name and id of a merchant in the system based on an identifier that is the name or id and ask if a paymnet is to be made",
        "parameters": {
            "type": "object",
            "properties": {
                "merchant_identifier": {
                    "type": "string",
                    "description": "The name of the merchant or the merchant id which is a 3 digit number",
                },
            },
            "required": ['merchant_identifier'],
        },
    },
    {
        "name": "get_transaction_details",
        "description": "Get amount and status of a transaction based on the id provided",
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "integer",
                    "description": "The transaction id which is a 4 digit number",
                },
            },
            "required": ['transaction_id'],
        },
    },
    {
        "name": "pay_merchant",
        "description": "Collect the email address, amount to pay and merchant id or merchant name to use in making payments to merchants on the system. Ask for email if not given by customer",
        "parameters": {
            "type": "object",
            "properties": {
                "merchant_identifier": {
                    "type": "string",
                    "description": "The name of the merchant or the merchant id which is a 3 digit number to identify the merchant",
                },
                "amount": {
                    "type": "number",
                    "description": "The amount to be paid to the merchant",
                },
                "email": {
                    "type": "string",
                    "description": "The email address of the customer making the payment, request input from user if email is not initially provided",
                },
            },
            "required": ['amount', 'merchant_identifier', 'email'],
        },
    },
    {
        "name": "place_order",
        "description": "Place an order for a pizza from the restaurant",
        "parameters": {
            "type": "object",
            "properties": {
                "pizza_name": {
                    "type": "string",
                    "description": "The name of the pizza you want to order, e.g. Margherita",
                },
                "quantity": {
                    "type": "integer",
                    "description": "The number of pizzas you want to order",
                    "minimum": 1
                },
                "address": {
                    "type": "string",
                    "description": "The address where the pizza should be delivered",
                },
            },
            "required": ["pizza_name", "quantity", "address"],
        },
    }
]


# import openai
# import json

flow_id = "content20240121115201_780259"


class ChatBot:

    def __init__(self, database):
        self.fake_db = database
        self.redis_db = redis.Redis(
  host='redis-11093.c321.us-east-1-2.ec2.cloud.redislabs.com',
  port=11093,
  password='redis345')



    def chat(self, query, contactId=None):
        initial_response = self.make_openai_request(query)

        message = initial_response["choices"][0]["message"]

        respData = {}

        if message.get("function_call"):
            print("msg: ", message)
            function_name = message["function_call"]["name"]
            print("fn name: "+ function_name)
            arguments = json.loads(message["function_call"]["arguments"])


            if function_name == 'pay_merchant':
                print("args: ", arguments)
                print("email: ", arguments["email"])
                print("amount: ", arguments["amount"])
                print("mid: ", arguments["merchant_identifier"])

                if arguments["email"]:
                    function_response = self.pay_merchant(arguments["amount"], arguments["merchant_identifier"], arguments["email"], contactId)
                    return function_response
                else:
                    self.redis_db.set("p_function", function_name)
                    self.redis_db.set("pay_amount", arguments["amount"])
                    self.redis_db.set("m_id", arguments["merchant_identifier"])
                    return {
                        "msg": "Please provide your email address"
                    }

            if function_name == 'get_user_info' and arguments["email"]:
                try:
                    self.redis_db.ping()
                    print("mid: ", self.redis_db.get("m_id").decode("utf-8"))
                    print("amount: ", self.redis_db.get("pay_amount").decode("utf-8"))

                    if self.redis_db.get("m_id").decode("utf-8") and self.redis_db.get("pay_amount").decode("utf-8"):
                        function_response = self.pay_merchant(self.redis_db.get("pay_amount").decode("utf-8"), self.redis_db.get("m_id").decode("utf-8"), arguments["email"], contactId)
                        return function_response
                    else:
                        return {
                            "msg": "I encountered an error please make your request again"
                        }
                except Exception as error:
                    print("redis error: ", error)
                    return {
                            "msg": "I encountered an error please make your request again"
                        }


            function_response = getattr(self, function_name)(**arguments)

            # print("fn resp: ", function_response)

            follow_up_response = self.make_follow_up_request(query, message, function_name, function_response)
            return {
                "msg": follow_up_response["choices"][0]["message"]["content"]
            }
        else:
            return {
                "msg": message["content"]
            }

    def make_openai_request(self, query):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "system", "content": "If any required paramters for the functions are not provided by the user, prompt them"},
                {"role": "user", "content": query}
                ],
            functions=functions,
            max_tokens=500,
            temperature=.1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            n=1,
            # functions=functions,
            function_call="auto",
            stop=None
        )
        return response

    def make_follow_up_request(self, query, initial_message, function_name, function_response):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": query},
                initial_message,
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                },
            ],
        )
        return response

    def place_order(self, pizza_name, quantity, address):
        if pizza_name not in self.fake_db["pizzas"]:
            return f"We don't have {pizza_name} pizza!"

        if quantity < 1:
            return "You must order at least one pizza."

        order_id = len(self.fake_db["orders"]) + 1
        order = {
            "order_id": order_id,
            "pizza_name": pizza_name,
            "quantity": quantity,
            "address": address,
            "total_price": self.fake_db["pizzas"][pizza_name]["price"] * quantity
        }

        self.fake_db["orders"].append(order)

        return f"Order placed successfully! Your order ID is {order_id}. Total price is ${order['total_price']}."

    def get_pizza_info(self, pizza_name):
        if pizza_name in self.fake_db["pizzas"]:
            pizza = self.fake_db["pizzas"][pizza_name]
            return f"Pizza: {pizza['name']}, Price: ${pizza['price']}"
        else:
            return f"We don't have information about {pizza_name} pizza."

    def get_merchant(self, merchant_identifier):
        merchants = self.fake_db.get("merchants", [])
        # print(merchants)
        best_match = None
        best_similarity = 0

        try:
            merchant_identifier = int(merchant_identifier)
        except:
            print("id is string")

        # Check if identifier is a name or an ID
        if isinstance(merchant_identifier, str):
            # print(f"id: {merchant_identifier} is string")
            # Search by name
            for merchant in merchants:
                similarity = fuzz.ratio(merchant_identifier.lower(), merchant.get("name").lower())
                if similarity > 60 and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = merchant

        else:
            # print("not string: ", type(merchant_identifier))
            # Search by ID
            found_merchant = next((merchant for merchant in merchants if merchant.get("id") == merchant_identifier), None)
            if found_merchant:
                return found_merchant
                # return found_merchant.get("name")

        if best_match:
            return best_match
        else:
            return None


    def get_merchant_details(self, merchant_identifier):
        merchant = self.get_merchant(merchant_identifier)


        if merchant:
            merchant_name = merchant.get("name")
            merchant_id = merchant.get("id")
            return f"Merchant: {merchant_name} ; Merchant ID: {merchant_id}"
        else:
            return "Merchant not found in the database"


    def get_pizza_menu(self):
        menu_items = self.fake_db.get("pizzas")
        if not menu_items:
            menu_items = "Menu not found."

        if isinstance(menu_items, str):
            return menu_items
        else:
            menu_list = "Menu Items:\n"
            for pizza, details in menu_items.items():
                menu_list += f"- {pizza}: Price - ${details['price']}, Ingredients - {', '.join(details['ingredients'])}\n"
            return menu_list

    def get_merchant_list(self):
        merchants = self.fake_db.get("merchants", [])
        merchant_details = "\n".join([f"Merchant: {merchant['name']}, ID: {merchant['id']}" for merchant in merchants])
        return merchant_details

    def get_pay_link(self, email, amount, cid):
        purl = "https://api.paystack.co/transaction/initialize"
        data = {
            "amount": int(amount)*100, 
            "email": email,
            "callback_url": f"{apiUrl}/manychat-callback/user/{cid}"                                                                                                                                                                                                                                                                                                                                                                                                                               
            } 
        print("pld: ", data)
        headers = {
            "Authorization": f"Bearer sk_test_de93288b38ea5cbd9b946c34ef92308cfe7d32b8"  # Replace with your actual token
        }
        response = requests.post(purl, data=data, headers=headers)

        if response.status_code == 200:

            # Access JSON content:
            json_content = response.json()
            print("JSON content:", json_content)
            return json_content
        else:
            print("Error:", response)
            return None

    def pay_merchant(self, amount, merchant_identifier, email, cid):
        merchant = self.get_merchant(merchant_identifier)

        print("merchant: ", merchant)

        resp_data = {}

        if merchant:
            pay_response = self.get_pay_link(email=email, amount=amount, cid=cid)
            if pay_response and pay_response['status'] == True:
                print('in success generate')
                checkout_url = pay_response['data']['authorization_url']
                resp_data["msg"] = f"please visit this url {checkout_url} to make Payment of NGN {amount} to {merchant['name']}."
                resp_data["success"] = False
                resp_data["data"] = pay_response['data']
            else:
                resp_data["msg"] = "Error generating checkout page"
                resp_data["success"] = False
        else:
            resp_data["msg"] = "Merchant not found in the database, please give us the merchant ID"
            resp_data["success"] = True

        return resp_data


    def get_transaction(self, transaction_id):
        transactions = self.fake_db.get("transactions", [])

        try:
            transaction_id = int(transaction_id)
        except:
            return None

        found_transaction = next((transaction for transaction in transactions if transaction.get("id") == transaction_id), None)
        if found_transaction:
            return found_transaction
        else:
            return None


    def get_transaction_details(self, transaction_id):
        transaction = self.get_transaction(transaction_id)

        if transaction:
            transaction_status = transaction.get("status")
            transaction_amount = transaction.get("amount")
            return f"Transaction Status: {transaction_status} ; Amount: NGN {transaction_amount}"
        else:
            return "transaction not found in the database"

database = {
    "pizzas": {
        "Hawaii": {"price": 15.00, "ingredients": ["ham", "pineapple", "cheese"]},
        "Margherita": {"price": 10.00, "ingredients": ["tomato", "mozzarella", "basil"]},
        "Pepperoni": {"price": 12.50, "ingredients": ["pepperoni", "mozzarella", "tomato sauce"]},
        "Veggie": {"price": 11.00, "ingredients": ["bell peppers", "onions", "olives", "mushrooms"]},
    },
    "merchants": [
        { "name": "Sam's Autos", "balance": 20, "id": 331 },
        { "name": "Intiqo SoftLink", "balance": 40, "id": 102 },
        { "name": "Indigo Stores", "balance":20, "id": 105 },
        { "name": "Analyxt Wears", "balance": 30, "id": 101 },
        { "name": "Slot Stores", "balance": 0, "id": 113 },
        { "name": "Varygold Stores", "balance": 10, "id": 201 },
    ],
    "transactions": [
        { "status": "Success", "amount": 40000, "id": 1003 },
        { "status": "Success", "amount": 50000, "id": 1001 },
        { "status": "Failed", "amount": 100000, "id": 1005 },
        { "status": "Failed", "amount": 120000, "id": 1007 },
        { "status": "Reversed", "amount": 780000, "id": 1002 },
    ],
    "orders": []
}


bot = ChatBot(database=database)

def get_response(query, contactId = None):
    response = bot.chat(query, contactId)
    print("Query: ", query)
    print("Response: ", response)
    return response

# response= get_response("I want to pay NGN 400,000 to Slot Phones")
# print(response)

# r  = redis.Redis(
#   host='redis-11093.c321.us-east-1-2.ec2.cloud.redislabs.com',
#   port=11093,
#   password='redis345')

# try:
#     r.ping()  # Send a PING command to check connectivity
#     print("Connected to Redis successfully!")
# except redis.ConnectionError:
#     print("Connection to Redis failed.")

# Set a value with an expiration time
# r.setex("user:123:name", 300, "Alice")

# Retrieve the value
# name = r.get("user:123:name").decode("utf-8")
# print(name)  # Output: Alice