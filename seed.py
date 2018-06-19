#!/usr/bin/env python
import os
import sys
from app.models import *
from django.contrib.auth.models import Permission, Group, ContentType

if __name__ == "__main__":
    Permission.objects.all().delete()
    ContentType.objects.all().delete()
    Group.objects.all().delete()
    
    
