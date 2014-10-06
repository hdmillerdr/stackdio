from django.conf.urls import patterns, url

from . import api

urlpatterns = patterns(
    'cloud.api',

    url(r'^provider_types/$',
        api.CloudProviderTypeListAPIView.as_view(),
        name='cloudprovidertype-list'),

    url(r'^provider_types/(?P<pk>[0-9]+)/$',
        api.CloudProviderTypeDetailAPIView.as_view(),
        name='cloudprovidertype-detail'),

    url(r'^providers/$',
        api.CloudProviderListAPIView.as_view(),
        name='cloudprovider-list'),

    url(r'^providers/(?P<pk>[0-9]+)/$',
        api.CloudProviderDetailAPIView.as_view(),
        name='cloudprovider-detail'),

    url(r'^providers/(?P<pk>[0-9]+)/security_groups/$',
        api.CloudProviderSecurityGroupListAPIView.as_view(),
        name='cloudprovider-securitygroup-list'),

    url(r'^providers/(?P<pk>[0-9]+)/vpc_subnets/$',
        api.CloudProviderVPCSubnetListAPIView.as_view(),
        name='cloudprovider-vpcsubnet-list'),

    url(r'^providers/(?P<pk>[0-9]+)/global_orchestration_components/$',
        api.GlobalOrchestrationComponentListAPIView.as_view(),
        name='cloudprovider-global-orchestration-list'),

    url(r'^providers/(?P<pk>[0-9]+)/global_orchestration_properties/$',
        api.GlobalOrchestrationPropertiesAPIView.as_view(),
        name='cloudprovider-global-orchestration-properties'),

    url(r'^global_orchestration_components/(?P<pk>[0-9]+)/$',
        api.GlobalOrchestrationComponentDetailAPIView.as_view(),
        name='globalorchestrationformulacomponent-detail'),

    url(r'^instance_sizes/$',
        api.CloudInstanceSizeListAPIView.as_view(),
        name='cloudinstancesize-list'),

    url(r'^instance_sizes/(?P<pk>[0-9]+)/$',
        api.CloudInstanceSizeDetailAPIView.as_view(),
        name='cloudinstancesize-detail'),

    url(r'^profiles/$',
        api.CloudProfileListAPIView.as_view(),
        name='cloudprofile-list'),

    url(r'^profiles/(?P<pk>[0-9]+)/$',
        api.CloudProfileDetailAPIView.as_view(),
        name='cloudprofile-detail'),

    url(r'^snapshots/$',
        api.SnapshotListAPIView.as_view(),
        name='snapshot-list'),

    url(r'^snapshots/(?P<pk>[0-9]+)/$',
        api.SnapshotDetailAPIView.as_view(),
        name='snapshot-detail'),

    url(r'admin/snapshots/$',
        api.SnapshotAdminListAPIView.as_view(),
        name='snapshot-admin-list'),

    url(r'^regions/$',
        api.CloudRegionListAPIView.as_view(),
        name='cloudregion-list'),

    url(r'^regions/(?P<pk>[0-9]+)/$',
        api.CloudRegionDetailAPIView.as_view(),
        name='cloudregion-detail'),

    url(r'^regions/(?P<pk>[0-9]+)/zones/$',
        api.CloudZoneListAPIView.as_view(),
        name='cloudregion-zones'),

    url(r'^zones/(?P<pk>[0-9]+)/$',
        api.CloudZoneDetailAPIView.as_view(),
        name='cloudzone-detail'),

    url(r'^security_groups/$',
        api.SecurityGroupListAPIView.as_view(),
        name='securitygroup-list'),

    url(r'^security_groups/(?P<pk>[0-9]+)/$',
        api.SecurityGroupDetailAPIView.as_view(),
        name='securitygroup-detail'),

    url(r'^security_groups/(?P<pk>[0-9]+)/rules/$',
        api.SecurityGroupRulesAPIView.as_view(),
        name='securitygroup-rules'),
)