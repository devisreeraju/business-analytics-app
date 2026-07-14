from django import forms
from .models import Dataset

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control form-control-premium',
                'accept': '.csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            extension = file.name.split('.')[-1].lower()
            if extension not in ['csv', 'xls', 'xlsx']:
                raise forms.ValidationError("Unsupported file extension. Only CSV and Excel (.xls, .xlsx) files are supported.")
        return file
