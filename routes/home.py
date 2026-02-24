"""Home: index, privacy."""
from flask import Blueprint, render_template
from auth import login_required

home = Blueprint("home", __name__)

@home.route("/")
@login_required
def index():
    return render_template("home/index.html")

@home.route("/Home/Privacy")
@login_required
def privacy():
    return render_template("home/privacy.html")
