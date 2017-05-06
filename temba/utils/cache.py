from __future__ import unicode_literals

import json

from datetime import timedelta
from django.utils import timezone
from django_redis import get_redis_connection


def get_cacheable(cache_key, cache_ttl, callable, r=None, force_dirty=False):
    """
    Gets the result of a method call, using the given key and TTL as a cache
    """
    if not r:
        r = get_redis_connection()

    if not force_dirty:
        cached = r.get(cache_key)
        if cached is not None:
            return json.loads(cached)

    calculated = callable()
    r.set(cache_key, json.dumps(calculated), cache_ttl)

    return calculated


def get_cacheable_result(cache_key, cache_ttl, callable, r=None, force_dirty=False):
    """
    Gets a cache-able integer calculation result
    """
    return int(get_cacheable(cache_key, cache_ttl, callable, r=r, force_dirty=force_dirty))


def get_cacheable_attr(obj, attr_name, calculate):
    """
    Gets the result of a method call, using the given object and attribute name
    as a cache
    """
    if hasattr(obj, attr_name):
        return getattr(obj, attr_name)

    calculated = calculate()
    setattr(obj, attr_name, calculated)

    return calculated


def incrby_existing(key, delta, r=None):
    """
    Update a existing integer value in the cache. If value doesn't exist, nothing happens. If value has a TTL, then that
    is preserved.
    """
    if not r:
        r = get_redis_connection()

    lua = "local ttl = redis.call('pttl', KEYS[1])\n" \
          "local val = redis.call('get', KEYS[1])\n" \
          "if val ~= false then\n" \
          "  val = tonumber(val) + ARGV[1]\n" \
          "  redis.call('set', KEYS[1], val)\n" \
          "  if ttl > 0 then\n" \
          "    redis.call('pexpire', KEYS[1], ttl)\n" \
          "  end\n" \
          "end"
    r.eval(lua, 1, key, delta)


def filter_with_lock(items, lock_prefix, lock_on=None):
    """
    Takes a set of objects and returns only those we are able to get a lock for
    """
    r = get_redis_connection()

    key_format = lock_prefix + '_%y_%m_%d'
    today_set_key = timezone.now().strftime(key_format)
    yesterday_set_key = (timezone.now() - timedelta(days=1)).strftime(key_format)

    locked_items = []

    for item in items:
        item_value = str(lock_on(item)) if lock_on else str(item)

        # check whether we locked this item today or yesterday
        pipe = r.pipeline()
        pipe.sismember(today_set_key, item_value)
        pipe.sismember(yesterday_set_key, item_value)
        (queued_today, queued_yesterday) = pipe.execute()

        # if not then we have access to this item
        if not queued_today and not queued_yesterday:
            locked_items.append(item)

            # add this item to today's set to show it's locked
            pipe = r.pipeline()
            pipe.sadd(today_set_key, item_value)
            pipe.expire(today_set_key, 86400)  # 24 hours
            pipe.execute()

    return locked_items
