from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    # Pre-calculated metadata cache for performance
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    missing_values_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    
    numeric_columns = models.JSONField(default=list, blank=True)
    categorical_columns = models.JSONField(default=list, blank=True)
    column_types = models.JSONField(default=dict, blank=True)
    preview_data = models.JSONField(default=list, blank=True) # List of dicts representing the first 10 rows

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"
