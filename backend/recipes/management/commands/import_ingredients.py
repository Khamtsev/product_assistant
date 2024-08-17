import json

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирование ингредиентов из ingredients.json'

    def handle(self, *args, **options):
        file_path = f'data/ingredients.json'

        with open(file_path, 'r', encoding='utf-8') as file:
            ingredients = json.load(file)

            Ingredient.objects.bulk_create(
                Ingredient(**ingredient) for ingredient in ingredients
            ),

        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно импортированы'
        ))
