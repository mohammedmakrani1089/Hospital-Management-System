from flask import Blueprint


home_bp = Blueprint("home", __name__)


from .home_features import overview
from .home_features import doctors
from .home_features import appointments
from .home_features import payments