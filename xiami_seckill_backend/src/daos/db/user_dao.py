from models.user_model import User
from django.db import connection

class UserDao(object):
    
    def create_enduser(self, username, password, level=1):
        try:
            user_model = User(username=username,password=password,level=level)
            user_model.save()
            return user_model
        finally:
            connection.close()

    def find_by_username_password(self, username, password):
        try:
            user_data_qs = User.objects.filter(username=username, password=password)
            return user_data_qs
        finally:
            connection.close()

    def find_by_username(self, username):
        try:
            user_data_qs = User.objects.filter(username=username)
            return user_data_qs
        finally:
            connection.close()