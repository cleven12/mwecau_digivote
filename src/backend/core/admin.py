from django.contrib import admin
from .models import User, State, Course, CollegeData
# Register your models here.

admin.site.register(User)
admin.site.register(State)
admin.site.register(CollegeData)
admin.site.register(Course)
