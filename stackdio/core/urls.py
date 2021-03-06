# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

from django.conf.urls import include, url
from stackdio.core import api

urlpatterns = (
    url(r'^api/version/$',
        api.VersionAPIView.as_view(),
        name='version'),

    url(r'^api/events/$',
        api.EventListAPIView.as_view(),
        name='event-list'),

    url(r'^api/notifications/',
        include('stackdio.core.notifications.urls', namespace='notifications')),
)
