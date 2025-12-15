from django.contrib import admin
from .models import Post, Category, Product
from PIL import Image

# Register your models here.
admin.site.register(Post)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["name", "description"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.image:
            img = Image.open(obj.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(obj.image.path)
