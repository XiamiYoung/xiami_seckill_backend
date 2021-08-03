from models.user_model import User

class UserDao(object):
    
    def create_enduser(self, username, password, level=1):
        user_model = User(username=username,password=password,level=level)
        user_model.save()
        return user_model

    def find_by_username_password(self, username, password):
        user_data_qs = User.objects.filter(username=username, password=password)
        return user_data_qs

    def find_by_username(self, username):
        user_data_qs = User.objects.filter(username=username)
        return user_data_qs