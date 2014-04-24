from flask import g, render_template, request, redirect, url_for, jsonify

from charat2.model.connections import use_db

@use_db
def feed():
    return "ok"
