import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Импортирование тегов из tags.json'

    def handle(self, *args, **options):
        file_path = f'{settings.IMPORT_FOLDER}/tags.json'

        with open(file_path, 'r', encoding='utf-8') as file:
            tags = json.load(file)

            Tag.objects.bulk_create(
                (Tag(**tag) for tag in tags),
            )

        self.stdout.write(self.style.SUCCESS(
            'Теги успешно импортированы'
        ))
