import django_filters

from nodeconductor.structure.views import BaseResourceFilter
from nodeconductor.openstack import models


class InstanceFilter(BaseResourceFilter):
    project = django_filters.CharFilter(
        name='service_project_link__project__uuid',
        lookup_type='icontains',
        distinct=True)

    project_name = django_filters.CharFilter(
        name='service_project_link__project__name',
        lookup_type='icontains',
        distinct=True)

    project_group_name = django_filters.CharFilter(
        name='service_project_link__project__project_groups__name',
        lookup_type='icontains',
        distinct=True)

    project_group = django_filters.CharFilter(
        name='service_project_link__project__project_groups__uuid',
        distinct=True)

    customer = django_filters.CharFilter(
        name='service_project_link__project__customer__uuid',
        distinct=True)

    customer_name = django_filters.CharFilter(
        name='service_project_link__project__customer__name',
        lookup_type='icontains',
        distinct=True)

    customer_native_name = django_filters.CharFilter(
        name='service_project_link__project__customer__native_name',
        lookup_type='icontains',
        distinct=True)

    customer_abbreviation = django_filters.CharFilter(
        name='service_project_link__project__customer__abbreviation',
        lookup_type='icontains',
        distinct=True)

    description = django_filters.CharFilter(lookup_type='icontains')
    state = django_filters.NumberFilter()

    # In order to return results when an invalid value is specified
    strict = False

    class Meta(object):
        model = models.Instance
        fields = BaseResourceFilter.Meta.fields + (
            'description',
            'customer',
            'customer_name',
            'customer_native_name',
            'customer_abbreviation',
            'project',
            'project_name',
            'project_group_name',
            'project_group',
            'state',
            'start_time',
            'created',
            'ram',
            'cores',
            'system_volume_size',
            'data_volume_size',
        )
        order_by = [
            'name',
            '-name',
            'state',
            '-state',
            'service_project_link__project__customer__name',
            '-service_project_link__project__customer__name',
            'service_project_link__project__customer__native_name',
            '-service_project_link__project__customer__native_name',
            'service_project_link__project__customer__abbreviation',
            '-service_project_link__project__customer__abbreviation',
            'service_project_link__project__name',
            '-service_project_link__project__name',
            'service_project_link__project__project_groups__name',
            '-service_project_link__project__project_groups__name',
            'created',
            '-created',
            'ram',
            '-ram',
            'cores',
            '-cores',
            'system_volume_size',
            '-system_volume_size',
            'data_volume_size',
            '-data_volume_size',
        ]
        order_by_mapping = {
            # Proper field naming
            'customer_name': 'service_project_link__project__customer__name',
            'customer_native_name': 'service_project_link__project__customer__native_name',
            'customer_abbreviation': 'service_project_link__project__customer__abbreviation',
            'project_name': 'service_project_link__project__name',
            'project_group_name': 'service_project_link__project__project_groups__name',

            # Backwards compatibility
            'project__customer__name': 'service_project_link__project__customer__name',
            'project__name': 'service_project_link__project__name',
            'project__project_groups__name': 'service_project_link__project__project_groups__name',
        }


class SecurityGroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        name='name',
        lookup_type='icontains',
    )
    description = django_filters.CharFilter(
        name='description',
        lookup_type='icontains',
    )
    service = django_filters.CharFilter(
        name='service_project_link__service__uuid',
    )
    project = django_filters.CharFilter(
        name='service_project_link__project__uuid',
    )

    class Meta(object):
        model = models.SecurityGroup
        fields = [
            'name',
            'description',
            'service',
            'project'
        ]


class FloatingIPFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(
        name='service_project_link__project__uuid',
    )
    service = django_filters.CharFilter(
        name='service_project_link__service__uuid',
    )

    class Meta(object):
        model = models.FloatingIP
        fields = [
            'project',
            'service',
            'status',
        ]