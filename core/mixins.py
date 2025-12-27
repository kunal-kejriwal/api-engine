from django.conf import settings
from django.db import models
import random
from django.utils.timezone import now


User = settings.AUTH_USER_MODEL

class OwnedModel(models.Model):
    created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="%(class)s_created",
    null=False,
    blank=False
    # null=True,
    # blank=True
)
    created_at = models.DateTimeField(auto_now_add=True)
    is_platform_owned = models.BooleanField(default=False)

    class Meta:
        abstract = True
        

class PublicIDMixin(models.Model):
    public_id = models.CharField(
        max_length=14,
        unique=True,
        editable=False,
        db_index=True,
        null=False,
        blank=False,
    )

    class Meta:
        abstract = True

    def _generate_public_id(self):
        return "".join(str(random.randint(0, 9)) for _ in range(14))

    def save(self, *args, **kwargs):
        if not self.public_id:
            for _ in range(5):  # retry protection
                candidate = self._generate_public_id()
                if not self.__class__.objects.filter(public_id=candidate).exists():
                    self.public_id = candidate
                    break
            else:
                raise RuntimeError("Failed to generate unique public_id")

        super().save(*args, **kwargs)
        
class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()      # default: only alive
    all_objects = AllObjectsManager()    # includes deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])