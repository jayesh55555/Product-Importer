from django import forms
from .models import Product, Webhook


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'active']
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SKU'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.upper()
            # Check for case-insensitive uniqueness
            existing = Product.objects.filter(sku__iexact=sku)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('A product with this SKU already exists.')
        return sku


class ProductFilterForm(forms.Form):
    sku = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by SKU'})
    )
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by name'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by description'})
    )
    active = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )



class WebhookForm(forms.ModelForm):
    class Meta:
        model = Webhook
        fields = ['name', 'target_url', 'event_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Slack Notification'}),
            'target_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/webhook'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
