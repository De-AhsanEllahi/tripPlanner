from django.db import models

# Create your models here.
from django.db import models

class Trip(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    destination = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title