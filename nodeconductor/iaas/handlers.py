from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db.models.aggregates import Sum
from django.utils.lru_cache import lru_cache
from django.contrib.contenttypes.models import ContentType
from django.db import models

from nodeconductor.core import models as core_models
from nodeconductor.core.serializers import UnboundSerializerMethodField
from nodeconductor.structure.filters import filter_queryset_for_user
from nodeconductor.iaas.models import ResourceQuota, ResourceQuotaUsage


logger = logging.getLogger('nodeconductor.iaas')


def get_related_clouds(obj, request):
    related_clouds = obj.clouds.all()

    try:
        user = request.user
        related_clouds = filter_queryset_for_user(related_clouds, user)
    except AttributeError:
        pass

    from nodeconductor.iaas.serializers import BasicCloudSerializer

    serializer_instance = BasicCloudSerializer(related_clouds, many=True, context={'request': request})

    return serializer_instance.data


def add_clouds_to_related_model(sender, fields, **kwargs):
    fields['clouds'] = UnboundSerializerMethodField(get_related_clouds)


def calculate_resource_quota(obj, request, cls):
    return cls.objects.filter(
        cloud_project_membership__project=obj,
    ).aggregate(
        vcpu=Sum('vcpu'),
        ram=Sum('ram'),
        storage=Sum('storage'),
        max_instances=Sum('max_instances'),
    )


def add_quota_stats_to_project(sender, fields, **kwargs):
    fields['resource_quota'] = UnboundSerializerMethodField(
        lambda obj, request: calculate_resource_quota(obj, request, ResourceQuota))
    fields['resource_quota_usage'] = UnboundSerializerMethodField(
        lambda obj, request: calculate_resource_quota(obj, request, ResourceQuotaUsage))


def propagate_new_users_key_to_his_projects_clouds(sender, instance=None, created=False, **kwargs):
    if not created:
        return

    public_key = instance

    from nodeconductor.iaas.models import CloudProjectMembership

    membership_queryset = filter_queryset_for_user(
        CloudProjectMembership.objects.all(), public_key.user)

    membership_pks = membership_queryset.values_list('pk', flat=True)

    if membership_pks:
        # Note: importing here to avoid circular import hell
        from nodeconductor.iaas import tasks

        tasks.push_ssh_public_keys.delay([public_key.uuid.hex], list(membership_pks))


def propagate_users_keys_to_clouds_of_newly_granted_project(sender, structure, user, role, **kwargs):
    project = structure

    ssh_public_key_uuids = core_models.SshPublicKey.objects.filter(
        user=user).values_list('uuid', flat=True)

    from nodeconductor.iaas.models import CloudProjectMembership

    membership_pks = CloudProjectMembership.objects.filter(
        project=project).values_list('pk', flat=True)

    if ssh_public_key_uuids and membership_pks:
        # Note: importing here to avoid circular import hell
        from nodeconductor.iaas import tasks

        tasks.push_ssh_public_keys.delay(
            list(ssh_public_key_uuids), list(membership_pks))


@lru_cache(maxsize=1)
def _get_default_security_groups():
    nc_settings = getattr(settings, 'NODECONDUCTOR', {})
    config_groups = nc_settings.get('DEFAULT_SECURITY_GROUPS', [])
    groups = []

    def get_icmp(config_rule, key):
        result = config_rule[key]

        if not isinstance(result, (int, long)):
            raise TypeError('wrong type for "%s": expected int, found %s' %
                            (key, type(result).__name__))

        if not -1 <= result <= 255:
            raise ValueError('wrong value for "%s": '
                             'expected value in range [-1, 255], found %d' %
                             key, result)

        return result

    def get_port(config_rule, key):
        result = config_rule[key]

        if not isinstance(result, (int, long)):
            raise TypeError('wrong type for "%s": expected int, found %s' %
                            (key, type(result).__name__))

        if not 1 <= result <= 65535:
            raise ValueError('wrong value for "%s": '
                             'expected value in range [1, 65535], found %d' %
                             (key, result))

        return result

    for config_group in config_groups:
        try:
            name = config_group['name']
            description = config_group['description']
            config_rules = config_group['rules']
            if not isinstance(config_rules, (tuple, list)):
                raise TypeError('wrong type for "rules": expected list, found %s' %
                                type(config_rules).__name__)

            rules = []
            for config_rule in config_rules:
                protocol = config_rule['protocol']
                if protocol == 'icmp':
                    from_port = get_icmp(config_rule, 'icmp_type')
                    to_port = get_icmp(config_rule, 'icmp_code')
                elif protocol in ('tcp', 'udp'):
                    from_port = get_port(config_rule, 'from_port')
                    to_port = get_port(config_rule, 'to_port')

                    if to_port < from_port:
                        raise ValueError('wrong value for "to_port": '
                                         'expected value less that from_port (%d), found %d' %
                                         (from_port, to_port))
                else:
                    raise ValueError('wrong value for "protocol": '
                                     'expected one of (tcp, udp, icmp), found %s' %
                                     protocol)

                rules.append({
                    'protocol': protocol,
                    'cidr': config_rule['cidr'],
                    'from_port': from_port,
                    'to_port': to_port,
                })
        except KeyError as e:
            logger.error('Skipping misconfigured security group: parameter "%s" not found',
                         e.message)
        except (ValueError, TypeError) as e:
            logger.error('Skipping misconfigured security group: %s',
                         e.message)
        else:
            groups.append({
                'name': name,
                'description': description,
                'rules': rules,
            })

    return groups


def create_initial_security_groups(sender, instance=None, created=False, **kwargs):
    if not created:
        return

    from nodeconductor.iaas.models import SecurityGroup

    for group in _get_default_security_groups():
        g = SecurityGroup.objects.create(
            name=group['name'],
            description=group['description'],
            cloud_project_membership=instance,
        )

        for rule in group['rules']:
            g.rules.create(**rule)


def prevent_deletion_of_instances_with_connected_backups(sender, instance, **kwargs):
    from nodeconductor.backup.models import Backup
    ct = ContentType.objects.get_for_model(instance._meta.model)
    connected_backups = Backup.objects.filter(content_type=ct, object_id=instance.id)

    if connected_backups.exists():
        raise models.ProtectedError(
            "Cannot delete instance because it has connected backups.",
            connected_backups
        )


def set_cpm_default_availability_zone(sender, instance=None, **kwargs):
    if instance.availability_zone:
        return

    # TODO: Change after different clouds support
    nc_settings = getattr(settings, 'NODECONDUCTOR', {})
    openstacks = filter(lambda o: o.get('auth_url', '') == instance.cloud.auth_url,
                        nc_settings.get('OPENSTACK_CREDENTIALS', []))

    default_zones = [openstack['default_availability_zone'] for openstack in openstacks
                     if 'default_availability_zone' in openstack]

    if not default_zones:
        return
    elif len(default_zones) > 1:
        logger.warning('More than one default availability zone was found for cloud %s',
                       instance.cloud.name)
    else:
        instance.availability_zone = default_zones[0]
