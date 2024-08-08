from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPTokenAuth

from smart_cdss_api.api import load


load.download()

application = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')
api = Api(application, decorators=[auth.login_required])
api = Api(application)
base = '/smartcdss/api/v1.0'


@application.errorhandler(400)
def client_error(error, msg):
    return {'error': msg}, 400


@application.errorhandler(403)
def auth_error():
    return {'error': 'Unauthorized'}, 403


@application.errorhandler(500)
def server_error(error):
    return {'error': 'It might be my fault (^^;)'}, 500


@auth.verify_token
def verify_token(token):
    if load.validate_token(token):
        return True


def _post(data):
    if load.verify_request(data, all_fields=True):
        try:
            return load.application(data)
        except Exception as e:
            print(e)
            return server_error(500)
    else:
        return client_error(400, "Wrong JSON parameters (x_x)")


class SimpleModel(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'text', type=str, default='',
            location='json'
        )
        super(SimpleModel, self).__init__()

    def post(self):
        try:
            data = request.get_json()
            return _post(data)
        except:
            return client_error(400, "JSON format excepted (x_x)")


endpoint = (f'{base}/')
api.add_resource(
    SimpleModel, endpoint, methods=['POST'])


class ValidParameter(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'text', type=str, default='',
            location='json'
        )
        super(ValidParameter, self).__init__()

    def post(self):
        try:
            data = request.get_json()
            if ('filtro' in data.keys()
                    and 'parametro' in data.keys()):
                if load.verify_request(data['filtro'], all_fields=False):
                    try:
                        return load.get_parameters(data)
                    except Exception as e:
                        print(e)
                        return server_error(500)

            return client_error(400, "JSON format excepted (x_x)")

        except:
            print('Error')
            return client_error(400, "JSON format excepted (x_x)")


endpoint = (f'{base}/get_parameter/')
api.add_resource(
    ValidParameter, endpoint, methods=['POST'])


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8010, debug=True)
