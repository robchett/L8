#!/usr/bin/env python

from data.data import Data
from data.conf import args
from flask import Flask, jsonify

app = Flask(__name__)

errors = Data(args)

def list_routes():
    import urllib
    output = {}
    for rule in app.url_map.iter_rules():
        doc = app.view_functions[rule.endpoint].__doc__
        if rule.rule.startswith('/api/') and doc != None:
            output[rule.rule] = doc.strip()

    return output

base_path = '/api/v1.0/'

@app.route(base_path)
def api():
    """
    List the api calls
    """

    return jsonify({
            'success' : True,
            'version' : 1.0,
            'methods' : list_routes()
            })

@app.route(base_path + 'domains/')
def domains():
    """
    List the domains that have errors
    """
    
    return jsonify(errors.domains())

@app.route(base_path + 'errors/<string:host>/<string:mode>/')
def errors(host, mode):
    """
    List the errors for a domain
    """

    return jsonify(errors.errors(host, mode))


if __name__ == '__main__':
    app.run(debug=True)
