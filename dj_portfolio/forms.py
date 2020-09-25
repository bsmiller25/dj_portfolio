from django import forms
from .models import *

import pdb

   
class HoldingForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = ['stock', 'quantity']
        widgets = {
            'stock': forms.TextInput,
            }

