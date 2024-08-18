import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

import base64


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=f"{id}.{ext}")
        return super().to_internal_value(data)


def generate_shopping_cart(ingredients):
    shopping_cart = []
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        measurement_unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['ingredient_amount']
        shopping_cart.append(f'{name}: {amount}, {measurement_unit}\n')
    return shopping_cart
