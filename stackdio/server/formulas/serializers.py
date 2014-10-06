import logging

from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class FormulaPropertiesSerializer(serializers.Serializer):
    properties = serializers.Field('properties')

    class Meta:
        model = models.Formula
        fields = ('properties',)


class FormulaComponentSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.FormulaComponent
        fields = (
            'id',
            'title',
            'description',
            'formula',
            'sls_path',
        )


class FormulaSerializer(serializers.HyperlinkedModelSerializer):

    owner = serializers.Field()
    components = FormulaComponentSerializer(many=True)
    properties = serializers.HyperlinkedIdentityField(view_name='formula-properties')
    action = serializers.HyperlinkedIdentityField(view_name='formula-action')
    private_git_repo = serializers.Field()

    class Meta:
        model = models.Formula 
        fields = (
            'id',
            'url',
            'title',
            'description',
            'owner',
            'public',
            'private_git_repo',
            'uri',
            'root_path',
            'properties',
            'components',
            'created',
            'modified',
            'status',
            'status_detail',
            'action',
        )
