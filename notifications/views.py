# -*- coding: utf-8 -*-
''' Django Notifications example views '''
from distutils.version import \
    StrictVersion  # pylint: disable=no-name-in-module,import-error

from django import get_version
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from notifications import settings
from notifications.settings import get_config
from notifications.utils import id2slug, slug2id
from swapper import load_model

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

Notification = load_model('notifications', 'Notification')

def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

if StrictVersion(get_version()) >= StrictVersion('1.7.0'):
    from django.http import JsonResponse  # noqa
else:
    # Django 1.6 doesn't have a proper JsonResponse
    import json
    from django.http import HttpResponse  # noqa

    def date_handler(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    def JsonResponse(data):  # noqa
        return HttpResponse(
            json.dumps(data, default=date_handler),
            content_type="application/json")

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def mark_all_as_read(request):
    request.user.notifications.mark_all_as_read()

    return JsonResponse({"detail":"All marked as read."})

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def mark_as_read(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification, recipient=request.user, id=notification_id)
    notification.mark_as_read()

    return JsonResponse({"detail":"Mark as read."})

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def mark_as_unread(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification, recipient=request.user, id=notification_id)
    notification.mark_as_unread()

    return JsonResponse({"detail":"Mark as unread."})

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def delete(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification, recipient=request.user, id=notification_id)

    if settings.get_config()['SOFT_DELETE']:
        notification.deleted = True
        notification.save()
    else:
        notification.delete()

    return JsonResponse({"detail":"Mark as deleted."})

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def live_unread_notification_count(request):
    data = {
        'unread_count': request.user.notifications.unread().count(),
    }
    return JsonResponse(data)

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def live_unread_notification_list(request):
    ''' Return a json with a unread notification list '''

    default_num_to_fetch = get_config()['NUM_TO_FETCH']
    try:
        # If they don't specify, make it 5.
        num_to_fetch = request.GET.get('max', default_num_to_fetch)
        num_to_fetch = int(num_to_fetch)
        if not (1 <= num_to_fetch <= 100):
            num_to_fetch = default_num_to_fetch
    except ValueError:  # If casting to an int fails.
        num_to_fetch = default_num_to_fetch

    unread_list = []

    for notification in request.user.notifications.unread()[0:num_to_fetch]:
        unread_list.append(notification)
        if request.GET.get('mark_as_read'):
            notification.mark_as_read()
    
    CustomSerializer = my_import(settings.get_config()['NOTIFICATIONS_NOTIFICATION_SERIALIZER'])
    serializer = CustomSerializer(unread_list, many=True)
    return Response(serializer.data)

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def live_all_notification_list(request):
    ''' Return a json with a unread notification list '''

    default_num_to_fetch = get_config()['NUM_TO_FETCH']
    try:
        # If they don't specify, make it 5.
        num_to_fetch = request.GET.get('max', default_num_to_fetch)
        num_to_fetch = int(num_to_fetch)
        if not (1 <= num_to_fetch <= 100):
            num_to_fetch = default_num_to_fetch
    except ValueError:  # If casting to an int fails.
        num_to_fetch = default_num_to_fetch

    all_list = []

    for notification in request.user.notifications.all()[0:num_to_fetch]:
        all_list.append(notification)
        if request.GET.get('mark_as_read'):
            notification.mark_as_read()
    
    CustomSerializer = my_import(settings.get_config()['NOTIFICATIONS_NOTIFICATION_SERIALIZER'])
    serializer = CustomSerializer(all_list, many=True)
    return Response(serializer.data)

@permission_classes((IsAuthenticated, ))
@api_view(["GET"])
def live_all_notification_count(request):
    data = {
        'all_count': request.user.notifications.count(),
    }
    return JsonResponse(data)
