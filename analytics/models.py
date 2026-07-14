from django.db import models
from django.contrib.auth.models import User
from datasets.models import Dataset

class DashboardState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_states')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='dashboard_states')
    chart_type = models.CharField(max_length=50, default='bar')
    x_axis = models.CharField(max_length=100, blank=True, null=True)
    y_axis = models.CharField(max_length=100, blank=True, null=True)
    filters = models.JSONField(default=dict, blank=True) # Column -> List of selected values

    class Meta:
        unique_together = ('user', 'dataset')

    def __str__(self):
        return f"Dashboard State for {self.user.username} - {self.dataset.name}"
