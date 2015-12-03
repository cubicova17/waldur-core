from rest_framework import serializers

from nodeconductor.core.fields import JsonField
from nodeconductor.structure import SupportedServices, models as structure_models
from nodeconductor.template import models


class TemplateSerializer(serializers.ModelSerializer):
    resource_type = serializers.SerializerMethodField()
    options = JsonField()
    tags = serializers.SerializerMethodField()

    class Meta(object):
        model = models.Template
        fields = ('uuid', 'options', 'tags', 'resource_type', 'order_number')

    def get_resource_type(self, obj):
        try:
            return SupportedServices.get_name_for_model(obj.resource_content_type.model_class())
        except AttributeError:
            return '.'.join(obj.resource_content_type.natural_key())

    def get_tags(self, template):
        return [t.name for t in template.tags.all()]


class TemplateGroupSerializer(serializers.HyperlinkedModelSerializer):
    templates = TemplateSerializer(many=True)
    tags = serializers.SerializerMethodField()

    class Meta(object):
        model = models.TemplateGroup
        view_name = 'template-group-detail'
        fields = ('url', 'uuid', 'name', 'templates', 'is_active', 'tags')
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }

    def get_tags(self, template_group):
        return [t.name for t in template_group.tags.all()]


class TemplateGroupResultSerializer(serializers.HyperlinkedModelSerializer):
    provisioned_resources = JsonField()

    class Meta(object):
        model = models.TemplateGroupResult
        fields = ('url', 'uuid', 'is_finished', 'is_erred', 'provisioned_resources', 'state_message', 'error_message',
                  'error_details',)
        view_name = 'template-result-detail'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
        }


class BaseTemplateSerializer(serializers.Serializer):
    project = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        queryset=structure_models.Project.objects.all(),
        lookup_field='uuid',
        required=False,
    )
