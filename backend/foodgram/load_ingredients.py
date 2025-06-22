import csv

from recipes.models import Ingredient

with open('ingredients.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        Ingredient.objects.get_or_create(
            name=row['name'],
            measurement_unit=row['measurement_unit']
        )