from django.db import models

# Create your models here.
class Author(models.Model):
    fullname = models.CharField(max_length=255, null=False, unique=True)
    born_date = models.CharField(max_length=50)
    born_location = models.CharField(max_length=300)
    description = models.TextField() 
    
    def __str__(self):
        return f"{self.fullname}"
    
    
class Tag(models.Model):
    name = models.CharField(max_length=35, unique=True)

    def __str__(self):
        return self.name


class Quote(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="quotes")
    tags = models.ManyToManyField(Tag, blank=True, related_name="quotes")
    quote = models.TextField(unique=True)

    def __str__(self):
        return self.quote[:60]


