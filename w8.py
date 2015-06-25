#!/usr/bin/env python

import json
import hashlib

from data.data import Data
from data.config import args
from flask import Flask, jsonify

app = Flask(__name__)

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

@app.route(base_path + 'domain/list/')
def domains():
    """
    List the domains that have errors
    """
    errors_obj = Data(args)
    domains = errors_obj.domains()
    json_domains = []

    for d in domains:
        json_domains.append(d.__dict__)

    return jsonify({'domains':json_domains, 'hash': hashlib.md5(str(json_domains)).hexdigest()})


@app.route(base_path + 'domain/<string:host>/errors/')
@app.route(base_path + 'domain/<string:host>/errors/<string:mode>/')
def errors(host, mode=1):
    """
    List the errors for a domain
    """

    errors_obj = Data(args)
    errs = errors_obj.errors(host, mode)
    json_errs = []

    for e in errs:
        json_errs.append(e.__dict__)

    return jsonify({'errors':json_errs, 'hash': hashlib.md5(str(json_errs)).hexdigest()})

@app.route('/')
def template():
    return open('template.html').read(100000)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
