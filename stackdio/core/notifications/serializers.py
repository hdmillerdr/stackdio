# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

import json
import logging

from django.db import transaction
from rest_framework import serializers

from stackdio.core.serializers import EventField, StackdioHyperlinkedModelSerializer
from stackdio.core.utils import recursive_update
from . import models, utils

logger = logging.getLogger(__name__)


def validate_notifier(value):
    if value not in utils.get_notifier_list():
        raise serializers.ValidationError('No notifier named {}'.format(value))


class NotificationHandlerSerializer(serializers.HyperlinkedModelSerializer):

    options = serializers.JSONField()

    class Meta:
        model = models.NotificationHandler

        fields = (
            'notifier',
            'options',
        )

        extra_kwargs = {
            'notifier': {'validators': [validate_notifier]}
        }

    def validate(self, attrs):
        notifier_cls = utils.get_notifier_class(attrs['notifier'])
        required_options = notifier_cls.get_required_options()

        received_options = attrs.get('options', {})

        missing_options = []
        for option in required_options:
            if option not in received_options:
                missing_options.append(option)

        if missing_options:
            raise serializers.ValidationError({
                'options': ['Missing the following options: {}'.format(', '.join(missing_options))]
            })

        return attrs

    def create(self, validated_data):
        options = validated_data.pop('options', None)

        # Shove this into options_storage directly since it was already validated as JSON
        if options is not None:
            validated_data['options_storage'] = options

        return super(NotificationHandlerSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        options_storage = validated_data.pop('options', '{}')

        if self.partial:
            # This is a PATCH request - so merge the new options into the old ones
            options = json.loads(options_storage)
            options_storage = json.dumps(recursive_update(instance.options, options))

        # Shove the options into the validated data
        validated_data['options_storage'] = options_storage

        return super(NotificationHandlerSerializer, self).update(instance, validated_data)


class NotificationChannelSerializer(StackdioHyperlinkedModelSerializer):

    events = EventField(many=True, required=True)

    handlers = NotificationHandlerSerializer(many=True, required=True)

    class Meta:
        model = models.NotificationChannel
        lookup_field = 'name'

        fields = (
            'url',
            'name',
            'events',
            'handlers',
        )

    def create(self, validated_data):
        # Grab the handlers
        handlers = validated_data.pop('handlers')

        with transaction.atomic(using=models.NotificationChannel.objects.db):
            # Create the channel
            channel = super(NotificationChannelSerializer, self).create(validated_data)

            # Create the handlers
            for handler in handlers:
                handler['channel'] = channel
            self.fields['handlers'].create(handlers)

        return channel

    def update(self, instance, validated_data):
        # Grab the handlers
        handlers = validated_data.pop('handlers', [])

        with transaction.atomic(using=models.NotificationChannel.objects.db):
            # Update the channel
            channel = super(NotificationChannelSerializer, self).update(instance, validated_data)

            # Update the handlers
            if self.partial:
                # This is a PATCH request
                pass
            else:
                # This is a PUT request

                # delete all the handlers first
                for handler in channel.handlers.all():
                    handler.delete()

                # Then recreate them
                for handler in handlers:
                    handler['channel'] = channel
                self.fields['handlers'].create(handlers)

        return channel
