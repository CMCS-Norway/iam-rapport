from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_service(path):
    resp = requests.request(
        method=request.method,
        url=f'http://user-service:5000/user/{path}',
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)
    return (resp.content, resp.status_code, resp.headers.items())

@app.route('/access/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def access_service(path):
    resp = requests.request(
        method=request.method,
        url=f'http://access-service:5000/access/{path}',
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)
    return (resp.content, resp.status_code, resp.headers.items())

@app.route('/customer/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def customer_service(path):
    resp = requests.request(
        method=request.method,
        url=f'http://customer-service:5000/customer/{path}',
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)
    return (resp.content, resp.status_code, resp.headers.items())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)