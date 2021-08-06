from django.db import models

# Create your models here.
class Notification(models.Model):
    chat_id = models.IntegerField(unique=True, null=False)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)

    last_command = models.TextField(null=True)
    last_message_id = models.IntegerField(null=True)
    last_message_text = models.TextField(null=True)

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)