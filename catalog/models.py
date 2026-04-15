from django.db import models


class MasterCatalog(models.Model):
    """Global catalog of medicines managed by Super Admin"""
    MEDICINE_TYPES = [
        ('allopathic', 'Allopathic'),
        ('herbal', 'Herbal'),
        ('homeopathic', 'Homeopathic'),
    ]

    DOSAGE_FORMS = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('powder', 'Powder'),
        ('ointment', 'Ointment'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ]

    brand_id = models.IntegerField(unique=True)
    brand_name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=MEDICINE_TYPES)
    slug = models.SlugField(max_length=255, unique=True)
    dosage_form = models.CharField(max_length=50, choices=DOSAGE_FORMS)
    generic = models.CharField(max_length=200)
    strength = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=200)
    package_container = models.TextField()
    package_size = models.TextField()
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Suggested master price for reference")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'master_catalog'
        verbose_name = 'Master Catalog'
        verbose_name_plural = 'Master Catalog'
        ordering = ['brand_name']
        indexes = [
            models.Index(fields=['brand_name']),
            models.Index(fields=['generic']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.brand_name} - {self.strength}"
