"""
Here models are in different modules and the models.py imports them from different modules like this

from model1 import *        # or the name of models you want to import
from model2 import User

or you might write all your models in models.py 
"""


from django.db.models.base import ModelBase
from django.contrib import admin
import models


for model_name in dir(models):
    model = getattr(models, model_name)
    if isinstance(model, ModelBase):
        admin.site.register(model)