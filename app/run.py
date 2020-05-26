from flask import Flask, jsonify, render_template, url_for, request, redirect, json
from flask_sqlalchemy import SQLAlchemy, functools
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta

import pymysql, os, math, requests, uuid

import cherrypy
from cherrypy import log

import logging
from logging.handlers import *

# Directory imports
from routes.v1 import app

if __name__ == '__main__':
    app.run(port=5001, host='0.0.0.0',debug=True)
