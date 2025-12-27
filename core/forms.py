from django import forms
from .models import ProductCatalog
class ProductCatalogForm(forms.ModelForm):
    class Meta:
        model = ProductCatalog
        exclude = (
            "created_by",
            "is_platform_owned",  # 👈 NEVER expose to users
        )
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_product_id(self):
        product_id = self.cleaned_data.get("product_id")

        if ProductCatalog.objects.filter(
            created_by=self.user,
            product_id=product_id,
            is_deleted=False,
        ).exists():
            raise forms.ValidationError(
                "A product with this Product ID already exists."
            )

        return product_id

    # def clean_product_id(self):
    #     return self.instance.product_id