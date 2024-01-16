from flask import Flask, request, jsonify

# from utils import query_data, embed_OPENAI
from custom import get_response
from dotenv.main import load_dotenv
import os


openai_api_key = os.environ.get("OPENAI_API_KEY")

print("key: ", openai_api_key)

load_dotenv()

app = Flask(__name__)

@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    return 'Hello World'

@app.post('/test')
def query_test():
    print("In test query req")
    query = request.json['query']

    print("In test query req: Query - ", query)
    response = get_response(query)

    response_data = {
        "query" : query,
        "response" : response
    }

    return jsonify(response_data)


# if __name__ == '__main__':

#     # run() method of Flask class runs the application
#     # on the local development server.
#     app.run(debug=True)
    
if __name__ == '__main__':
    app.run(debug=True, port=5001)