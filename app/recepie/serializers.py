from rest_framework import serializers

from core.models import Tag, Ingredient, Recepie

class TagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)
        

class IngredientSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)
    

class RecepieSerializer(serializers.ModelSerializer):
    
    ingredients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Ingredient.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    
    class Meta:
        model = Recepie
        fields = ('id', 'title', 'ingredients', 'tags', 'time_minutes',
                  'price', 'link'
        )
        read_only_fields = ('id',)
        

class RecepieDetailSerializer(RecepieSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)