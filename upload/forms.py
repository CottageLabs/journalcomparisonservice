
from django import forms

from upload.models import UploadFile, frameworks

excelMimeTypes = ".xls," \
                 ".xlsx," \
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet," \
                 "application/vnd.ms-excel"


class UploadFileForm(forms.ModelForm):
    framework = forms.ChoiceField(choices=frameworks, widget=forms.RadioSelect())

    class Meta:
        model = UploadFile
        exclude = ('time', 'original_file_name', 'user', 'data_year', 'journals')
        widgets = {
            'upload_file': forms.FileInput(attrs={'accept': excelMimeTypes})
        }


class DeleteFileForm(forms.Form):
    delete_file_id = forms.HiddenInput()
