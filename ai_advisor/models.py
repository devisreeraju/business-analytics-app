from django.db import models
from datasets.models import Dataset

class AIReport(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    model_used = models.CharField(max_length=50, default='mistral-large-latest')
    
    # Structured report sections
    executive_summary = models.TextField(blank=True, default='')
    business_highlights = models.TextField(blank=True, default='')
    risks = models.TextField(blank=True, default='')
    opportunities = models.TextField(blank=True, default='')
    recommendations = models.TextField(blank=True, default='')
    conclusion = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"AI Report for {self.dataset.name} ({self.generated_at.strftime('%Y-%m-%d %H:%M')})"
