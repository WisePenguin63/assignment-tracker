from flask import Flask, redirect, render_template, session
from functools import wraps
from datetime import datetime


app = Flask(__name__)

def apology(message, code=400):
    """
    Render message as an apology to user.

    https://cs50.harvard.edu/x/psets/9/finance/
    """

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def logged_in():

    if session.get("user_id") is None:
        app.logger.debug("Returning false")
        return False
    app.logger.debug("Returning true")
    return True


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def datetime_convert(date: datetime):
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    return date.strftime(f"%-d{get_ordinal_suffix(date.day)} %b %Y, %H:%M")

def get_ordinal_suffix(day: int) -> str:
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
