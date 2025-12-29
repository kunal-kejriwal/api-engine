from django import forms
from .models import ProductCatalog
from core.validators import enforce_record_quota


class ProductCatalogForm(forms.ModelForm):
    class Meta:
        model = ProductCatalog
        exclude = (
            "created_by",
            "is_platform_owned",  # NEVER expose to users
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # 🔐 Enforce quota ONLY on create
        if self.user and self.instance.pk is None:
            enforce_record_quota(
                self.user,
                incoming_count=1
            )

        return cleaned_data

    def clean_product_id(self):
        product_id = self.cleaned_data.get("product_id")

        if not product_id or not self.user:
            return product_id

        # Allow same product_id when editing the same record
        qs = ProductCatalog.objects.filter(
            created_by=self.user,
            product_id=product_id,
            is_deleted=False,
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A product with this Product ID already exists."
            )

        return product_id
