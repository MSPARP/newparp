from flask import render_template

def error_403(e):
    return render_template("errors/403.html"), 403

def error_404(e):
    return render_template("errors/404.html"), 404

def error_500(e):
    return render_template("errors/500.html"), 500

