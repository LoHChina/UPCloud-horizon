# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from openstack_dashboard.api.ceilometer import ceilometerclient
from openstack_dashboard.contrib.custom import settings

import datetime
import time

UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class ObjDict(dict):

    def __getattr__(self, name):
        if name in self:
            return self[name]
        n = ObjDict
        super(ObjDict, self).__setitem__(name, n)
        return n

    def __getitem__(self, name):
        if name not in self:
            super(ObjDict, self).__setitem__(name, ObjDict())
        return super(ObjDict, self).__getitem__(name)

    def __setattr__(self, name, value):
        super(ObjDict, self).__setitem__(name, value)

    # def __unicode__(self):
    #    return u""


def convert_traits_to_dict(event):
    _traits = ObjDict()
    for trait in event.traits:
        _traits[trait["name"]] = trait["value"]
    event.traits = _traits
    return event


def event_list_with_tenant(request, limit=None):
    query = []
    query += [{"field": "tenant_id",
               "op": "eq",
               "type": "string",
               "value": request.user.tenant_id}]
    return event_list(request, query, limit)


def event_list(request, query=None, limit=None):
    if limit:
        query += [{"field": "limit",
                   "op": "eq",
                   "type": "int",
                   "value": limit * 3}]
    _events = ceilometerclient(request).events.list(q=query)
    _events = filter(lambda x: not x.event_type.endswith("start") or
                     not x.event_type.endswith("exists") or
                     not x.event_type.endswith("update"),
                     _events)
    _events = sorted(_events, key=lambda x: x.generated, reverse=True)
    _events = map(convert_traits_to_dict, _events)
    if limit:
        events = ["compute.instance.create.end",
                  "volume.detach.end",
                  "volume.attach.end",
                  "compute.instance.delete.end",
                  "compute.instance.shutdown.end",
                  "volume.create.end",
                  "volume.delete.end",
                  "compute.instance.power_on.end",
                  "snapshot.create.end",
                  "snapshot.delete.end",
                  "compute.instance.snapshot.end",
                  "compute.instance.power_off.end",
                  "compute.instance.rebuild.end",
                  "compute.instance.reboot.end",
                  "compute.instance.resume",
                  "compute.instance.suspend",
                  "network.create.end",
                  "network.delete.end",
                  "router.create.end",
                  "router.delete.end",
                  "floatingip.create.end",
                  "floatingip.delete.end"]
        _events = filter(lambda x: x.event_type in events, _events)[:limit]
        _e = []
        for e in _events:
            if hasattr(e.traits, "display_name"):
                if e.traits.display_name:
                    _e.append(e)
            else:
                _e.append(e)
        return _e[:limit]
    else:
        return _events


class Instance(object):
    def __init__(self, tenant_id=None, user_id=None, instance_id=None,
                 display_name=None, flavor=None, charging_start=None,
                 charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = instance_id
        self.display_name = display_name
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.status = None
        self.charging_status = True
        self.cost = None
        self.flavor = flavor

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Instance(event.traits.tenant_id,
                        event.traits.user_id,
                        event.traits.instance_id,
                        event.traits.display_name,
                        event.traits.instance_type,
                        kwargs.get("start_time", None),
                        kwargs.get("end_time", None))


class Router(object):
    def __init__(self, tenant_id=None, user_id=None, router_id=None,
                 charging_start=None, charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = router_id
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.display_name = "unknown"

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Router(event.traits.tenant_id,
                      event.traits.user_id,
                      event.traits.router_id,
                      kwargs.get("start_time", None),
                      kwargs.get("end_time", None))


class Floatingip(object):
    def __init__(self, tenant_id=None, user_id=None, floatingip_id=None,
                 charging_start=None, charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = floatingip_id
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.display_name = "unknown"

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Floatingip(event.traits.tenant_id,
                          event.traits.user_id,
                          event.traits.floatingip_id,
                          kwargs.get("start_time", None),
                          kwargs.get("end_time", None))


class Network(object):
    def __init__(self, tenant_id=None, user_id=None, network_id=None,
                 charging_start=None, charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = network_id
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.display_name = "unknown"

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Network(event.traits.tenant_id,
                       event.traits.user_id,
                       event.traits.network_id,
                       kwargs.get("start_time", None),
                       kwargs.get("end_time", None))


class Image(object):
    def __init__(self, tenant_id=None, user_id=None,
                 image_id=None, display_name=None,
                 size=None, charging_start=None,
                 charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = image_id
        self.display_name = display_name
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.cost = None
        try:
            self.size = int(size) / 1024.0 / 1024.0 / 1024.0
        except Exception:
            self.size = 0.01

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Image(event.traits.tenant_id,
                     event.traits.user_id,
                     event.traits.image_id,
                     event.traits.display_name,
                     event.traits.size,
                     kwargs.get("start_time", None),
                     kwargs.get("end_time", None))


class Volume(object):
    def __init__(self, tenant_id=None, user_id=None, volume_id=None,
                 display_name=None, charging_start=None, charging_end=None,
                 size=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = volume_id
        self.display_name = display_name
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.size = size

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Volume(event.traits.tenant_id,
                      event.traits.user_id,
                      event.traits.volume_id,
                      event.traits.display_name,
                      kwargs.get("start_time", None),
                      kwargs.get("end_time", None),
                      event.traits.size)


class Snapshot(object):
    def __init__(self, tenant_id=None, user_id=None, snapshot_id=None,
                 display_name=None, size=None, charging_start=None,
                 charging_end=None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.id = snapshot_id
        self.display_name = display_name
        self.charging_start = charging_start
        self.charging_end = charging_end
        self.charging_status = True
        self.size = size

    @classmethod
    def build(cls, event, *args, **kwargs):
        return Snapshot(event.traits.tenant_id,
                        event.traits.user_id,
                        event.traits.snapshot_id,
                        event.traits.display_name,
                        event.traits.volume_size,
                        kwargs.get("start_time", None),
                        kwargs.get("end_time", None))


def find_available(event, instances, *args, **kwargs):
    type_name = {
        "volume": "volume",
        "compute": "instance",
        "snapshot": "snapshot",
        "floatingip": "floatingip",
        "network": "network",
        "router": "router",
        "image": "image",
    }[event.event_type.split(".")[0]]
    event_id = getattr(event.traits, type_name + "_id")
    _class = globals()[type_name.capitalize()]
    for i, instance in enumerate(instances):
        if instance.id == event_id and \
           instance.charging_status:
            return i
    instance = _class.build(event, **kwargs)
    instances.append(instance)
    return len(instances) - 1


def statistics_with_month(request, year, month):
    query = []
    query += [{"field": "tenant_id",
               "op": "eq",
               "type": "string",
               "value": request.user.tenant_id}]
    start_time = datetime.datetime(year, month, 1)
    month += 1
    if month > 12:
        year += 1
        month -= 12
    end_time = datetime.datetime(year, month, 1)
    return statistics(request, query, start_time, end_time)


def statistics_all(request):
    query = []
    query += [{"field": "tenant_id",
               "op": "eq",
               "type": "string",
               "value": request.user.tenant_id}]
    start_time = datetime.datetime(2015, 1, 1)
    end_time = datetime.datetime.now()
    return statistics(request, query, start_time, end_time)


def ftime(_event):
    try:
        return datetime.datetime.strptime(_event.generated, UTC_FORMAT)
    except Exception:
        return datetime.datetime.strptime(_event.generated, UTC_FORMAT[:-3])


def network_statistics_events(_event, data, **kwargs):
    _event = convert_traits_to_dict(_event)
    _event_type = _event.event_type.split(".")[0]
    start_type = _event_type + ".create.end"
    end_type = _event_type + ".delete.end"
    exists_type = _event_type + ".exists"
    _data = getattr(data, _event_type + "s")
    if _event.event_type == start_type:
        _id = find_available(_event, _data, **kwargs)
        _data[_id].display_name = _event.traits.display_name
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
    elif _event.event_type == end_type:
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == exists_type:
        pass


def volume_statistics_events(_event, data, **kwargs):
    _event = convert_traits_to_dict(_event)
    _data = getattr(data, "volumes")
    if _event.event_type == "volume.create.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
    elif _event.event_type == "volume.delete.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == "volume.resize.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
    elif _event.event_type == "volume.resize.start":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == "volume.exists":
        pass


def snapshot_statistics_events(_event, data, **kwargs):
    _event = convert_traits_to_dict(_event)
    _data = getattr(data, "snapshots")
    if _event.event_type == "snapshot.delete.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == "snapshot.create.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
    elif _event.event_type == "snapshot.exists":
        pass


def instance_statics_events(_event, data, **kwargs):
    _event = convert_traits_to_dict(_event)
    _data = getattr(data, "instances")
    if _event.event_type == "compute.instance.create.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
        _data[_id].status = "available"
    elif _event.event_type == "compute.instance.power_off.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].status = "power_off"
        _data[_id].charging_status = False
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
        _data[_id].status = "available"
    elif _event.event_type == "compute.instance.power_on.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
        _data[_id].status = "available"
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
        _data[_id].status = "power_off"
    elif _event.event_type == "compute.instance.delete.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == "compute.instance.finish_resize.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
        _data[_id].flavor = _event.traits.instance_type
        _data[_id].status = "available"
    elif _event.event_type == "compute.instance.resize.end":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
        _data[_id].flavor = _event.traits.instance_type
        if _event.traits['state'] == 'active':
            _data[_id].status = "available"
        else:
            _data[_id].status = 'power_off'
    elif _event.event_type == "compute.instance.exists":
        pass


def image_statistics_events(_event, data, **kwargs):
    _event = convert_traits_to_dict(_event)
    _data = getattr(data, "images")
    if not check_image(_event):
        return
    if _event.event_type == "image.upload":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_start = ftime(_event)
        _data[_id].charging_status = False
    elif _event.event_type == "image.delete":
        _id = find_available(_event, _data, **kwargs)
        _data[_id].charging_end = ftime(_event)
    elif _event.event_type == "image.exists":
        pass


def check_image(_event):
    return isinstance(_event.traits.size, int)


def patch_displayname(data):
    # patch for network does not have display name
    pass


def get_price(name):
    try:
        p = settings.ANIMBUS_PRICES
        for n in name.split("/"):
            p = p.get(n)
    except Exception:
        print("ERROR -------------------------" + name)
        p = 0.1
    if not isinstance(p, float):
        print("ERROR -------------------------" + name)
        p = 0.1
    return p


def statistics(request, query=None, start_time=None, end_time=None):
    spec_events = ["volume.resize.start"]
    data = ObjDict({
        "instances": [],
        "volumes": [],
        "images": [],
        "snapshots": [],
        "floatingips": [],
        "routers": [],
        "networks": []
    })
    if not end_time or end_time > datetime.datetime.now():
        end_time = datetime.datetime.now()
    if not query:
        query = []
    query += [{"field": "end_time",
               "value": end_time}]
    if start_time:
        query += [{"field": "start_time",
                   "value": start_time}]
    date_args = {"start_time": start_time, "end_time": end_time}
    _events = ceilometerclient(request).events.list(q=query)
    _events = filter(lambda x: (x.event_type in spec_events)
                     or (not x.event_type.endswith("start")), _events)
    _events = sorted(_events, key=lambda x: x.generated, reverse=True)
    for _event in _events:
        if _event.event_type.startswith("compute.instance"):
            instance_statics_events(_event, data, **date_args)
        elif (_event.event_type.startswith("router") or
              _event.event_type.startswith("floatingip") or
              _event.event_type.startswith("network")):
            network_statistics_events(_event, data, **date_args)
        elif _event.event_type.startswith("volume"):
            volume_statistics_events(_event, data, **date_args)
        elif _event.event_type.startswith("snapshot"):
            snapshot_statistics_events(_event, data, **date_args)
        elif _event.event_type.startswith("image"):
            image_statistics_events(_event, data, **date_args)

    for instance in data.instances:
        seconds = (instance.charging_end -
                   instance.charging_start).total_seconds()
        if instance.status == "available":
            status = "instance_available"
        else:
            status = "instance_power_off"
        instance.cost = (((seconds + 59) / 60) *
                         get_price("{0}/{1}".format(status, instance.flavor)))
        instance.cost = round(instance.cost, 2)

    for volume in data.volumes:
        seconds = (volume.charging_end - volume.charging_start).total_seconds()
        volume.cost = ((seconds + 59) / 60) \
            * get_price("volume") * int(volume.size)
        volume.cost = round(volume.cost, 2)

    for snapshot in data.snapshots:
        seconds = (snapshot.charging_end -
                   snapshot.charging_start).total_seconds()
        snapshot.cost = (((seconds + 59) / 60) *
                         get_price("volume_snapshot") * int(snapshot.size))
        snapshot.cost = round(snapshot.cost, 2)

    for router in data.routers:
        seconds = (router.charging_end -
                   router.charging_start).total_seconds()
        router.cost = ((seconds + 59) / 60) * get_price("router")
        router.cost = round(router.cost, 2)

    for network in data.networks:
        seconds = (network.charging_end -
                   network.charging_start).total_seconds()
        network.cost = ((seconds + 59) / 60) * get_price("network")
        network.cost = round(network.cost, 2)

    for floatingip in data.floatingips:
        seconds = (floatingip.charging_end -
                   floatingip.charging_start).total_seconds()
        floatingip.cost = (((seconds + 59) / 60) *
                           get_price("floatingip"))
        floatingip.cost = round(floatingip.cost, 2)

    for image in data.images:
        seconds = (image.charging_end -
                   image.charging_start).total_seconds()
        image.cost = (((seconds + 59) / 60) * image.size *
                      get_price("image"))
        image.cost = round(image.cost)
    patch_displayname(data)  # patch
    return data


import pymongo

GB = 1024.0 * 1024.0 * 1024.0


class BillingStatistics(object):
    def __init__(self):
        self.client = pymongo.MongoClient(getattr(settings, "MONGO_URI"))
        self.db = self.client.ceilometer
        self.billing = self.db.billing

    def summary_statics(self, tenant_id=None):
        if tenant_id:
            query = {"tenant_id": tenant_id}
        else:
            query = {}
        billings = {
            "instances": [],
            "volumes": [],
            "images": [],
            "snapshots": [],
            "floatingips": [],
            "routers": [],
            "networks": []
        }
        for b in self.billing.find(query):
            b = self._p(b)
            billings[self.get_name(b)].append(self.add_cost(b))
        return billings

    def get_name(self, billing):
        if billing["type"].startswith("volume"):
            return "volumes"
        if billing["type"].startswith("compute"):
            return "instances"
        if billing["type"].startswith("image"):
            return "images"
        if billing["type"].startswith("router"):
            return "routers"
        if billing["type"].startswith("network"):
            return "networks"
        if billing["type"].startswith("floatingip"):
            return "floatingips"
        if billing["type"].startswith("snapshot"):
            return "snapshots"

    def add_cost(self, billing):
        minutes = self.get_minutes(billing)
        if self.get_name(billing) == "volumes":
            billing["price"] = get_price("volume") * billing["meta"]["size"]
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "images":
            billing["price"] = (get_price("image") *
                                (int(billing["meta"]["size"]) / GB))
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "instances":
            if billing["meta"]["state"] == "active":
                billing["price"] = get_price("instance_available/%s" %
                                             (billing["meta"]["flavor"]))
            else:
                billing["price"] = get_price("instance_power_off/%s" %
                                             (billing["meta"]["flavor"]))
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "snapshots":
            billing["price"] = get_price("volume_snapshot")\
                * billing["meta"]["size"]
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "routers":
            billing["price"] = get_price("router")
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "networks":
            billing["price"] = get_price("network")
            billing["cost"] = billing["price"] * minutes
        if self.get_name(billing) == "floatingips":
            billing["price"] = get_price("floatingip")
            billing["cost"] = billing["price"] * minutes
        billing["cost"] = round(billing["cost"], 2)
        billing["price"] = round(billing["price"] * 60, 2)
        return billing

    def get_minutes(self, billing):
        return (int(billing['charge_end'] - billing['charge_start']) + 59) / 60

    def statistics_with_month(self, tenant_id, year, month):
        # TODO(xuanmingyi)(end_time < year, monoth)
        start_time = self.timestamp(year, month, 1)
        month += 1
        if month > 12:
            year += 1
            month -= 12
        end_time = self.timestamp(year, month, 1)
        billings = {
            "instances": [],
            "volumes": [],
            "images": [],
            "snapshots": [],
            "floatingips": [],
            "routers": [],
            "networks": []
        }
        now = int(time.time())
        if now <= start_time:
            return billings
        for b in self.billing.find({"tenant_id": tenant_id}):
            b = self._p(b)
            if b["charge_start"] > end_time or\
               b["charge_end"] < start_time:
                continue
            if b["charge_start"] < start_time:
                b["charge_start"] = start_time
            if b["charge_end"] > end_time:
                b["charge_end"] = end_time
            billings[self.get_name(b)].append(self.add_cost(b))
        return billings

    def timestamp(self, year, month, day):
        return time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))

    def _p(self, billing):
        billing["charge_start"] = billing["charge_start"] + 28800
        try:
            # type bug charge_end -> change_end
            billing["charge_end"] = billing["change_end"] + 28800
        except KeyError:
            billing["charge_end"] = int(time.time())
        return billing
