from django.template import Library
from . import custom_filters

register = Library()

register.filter('censor', custom_filters.censor)