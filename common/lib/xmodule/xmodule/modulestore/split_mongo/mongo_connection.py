"""
Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
"""


import datetime
import logging
import math
import re
import zlib
from contextlib import contextmanager
from time import time

import pymongo
import pytz
import six
from six.moves import cPickle as pickle
from contracts import check, new_contract
from mongodb_proxy import autoretry_read
# Import this just to export it
from pymongo.errors import DuplicateKeyError  # pylint: disable=unused-import

from xmodule.exceptions import HeartbeatFailure
from xmodule.modulestore import BlockData
from xmodule.modulestore.split_mongo import BlockKey
from xmodule.mongo_utils import connect_to_mongodb, create_collection_index

try:
    from django.core.cache import caches, InvalidCacheBackendError
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

new_contract('BlockData', BlockData)
log = logging.getLogger(__name__)

DEBUG = False


# mcdaniel apr-2020
# Memcached object splitter: a workaround to the 1mb object limit in Memcached.

# DEPRECATED:
# -----------
# reduce default max value of 1024*1024 by the length of our hash
# less another 3 characters to allow for the pattern: ###  (ie where 001 means "chunk one")
MEMCACHED_MAX_VALUE_LENGTH = ((1024*1024)-3)


def get_cache(alias):
    """
    Return cache for an `alias`

    Note: The primary purpose of this is to mock the cache in test_split_modulestore.py
    """
    return caches[alias]


def round_power_2(value):
    """
    Return value rounded up to the nearest power of 2.
    """
    if value == 0:
        return 0

    return math.pow(2, math.ceil(math.log(value, 2)))


class Tagger(object):
    """
    An object used by :class:`QueryTimer` to allow timed code blocks
    to add measurements and tags to the timer.
    """
    def __init__(self, default_sample_rate):
        self.added_tags = []
        self.measures = []
        self.sample_rate = default_sample_rate

    def measure(self, name, size):
        """
        Record a measurement of the timed data. This would be something to
        indicate the size of the value being timed.

        Arguments:
            name: The name of the measurement.
            size (float): The size of the measurement.
        """
        self.measures.append((name, size))

    def tag(self, **kwargs):
        """
        Add tags to the timer.

        Arguments:
            **kwargs: Each keyword is treated as a tag name, and the
                value of the argument is the tag value.
        """
        self.added_tags.extend(list(kwargs.items()))

    @property
    def tags(self):
        """
        Return all tags for this (this includes any tags added with :meth:`tag`,
        and also all of the added measurements, bucketed into powers of 2).
        """
        return [
            '{}:{}'.format(name, round_power_2(size))
            for name, size in self.measures
        ] + [
            '{}:{}'.format(name, value)
            for name, value in self.added_tags
        ]


class QueryTimer(object):
    """
    An object that allows timing a block of code while also recording measurements
    about that code.
    """
    def __init__(self, metric_base, sample_rate=1):
        """
        Arguments:
            metric_base: The prefix to be used for all queries captured
            with this :class:`QueryTimer`.
        """
        self._metric_base = metric_base
        self._sample_rate = sample_rate

    @contextmanager
    def timer(self, metric_name, course_context):
        """
        Contextmanager which acts as a timer for the metric ``metric_name``,
        but which also yields a :class:`Tagger` object that allows the timed block
        of code to add tags and quantity measurements. Tags are added verbatim to the
        timer output. Measurements are recorded as histogram measurements in their own,
        and also as bucketed tags on the timer measurement.

        Arguments:
            metric_name: The name used to aggregate all of these metrics.
            course_context: The course which the query is being made for.
        """
        tagger = Tagger(self._sample_rate)
        metric_name = "{}.{}".format(self._metric_base, metric_name)

        start = time()
        try:
            yield tagger
        finally:
            end = time()
            tags = tagger.tags
            tags.append('course:{}'.format(course_context))


TIMER = QueryTimer(__name__, 0.01)


def structure_from_mongo(structure, course_context=None):
    """
    Converts the 'blocks' key from a list [block_data] to a map
        {BlockKey: block_data}.
    Converts 'root' from [block_type, block_id] to BlockKey.
    Converts 'blocks.*.fields.children' from [[block_type, block_id]] to [BlockKey].
    N.B. Does not convert any other ReferenceFields (because we don't know which fields they are at this level).

    Arguments:
        structure: The document structure to convert
        course_context (CourseKey): For metrics gathering, the CourseKey
            for the course that this data is being processed for.
    """
    if DEBUG: log.info('mcdaniel apr-2020: mongo_connection.py structure_from_mongo() - begin')
    with TIMER.timer('structure_from_mongo', course_context) as tagger:
        tagger.measure('blocks', len(structure['blocks']))

        check('seq[2]', structure['root'])
        check('list(dict)', structure['blocks'])
        if DEBUG: log.info('mcdaniel apr-2020: mongo_connection.py structure_from_mongo() - 1')
        for block in structure['blocks']:
            if 'children' in block['fields']:
                check('list(list[2])', block['fields']['children'])

        if DEBUG: log.info('mcdaniel apr-2020: mongo_connection.py structure_from_mongo() - 2')
        structure['root'] = BlockKey(*structure['root'])
        new_blocks = {}
        if DEBUG: log.info('mcdaniel apr-2020: mongo_connection.py structure_from_mongo() - 3')
        for block in structure['blocks']:
            if 'children' in block['fields']:
                block['fields']['children'] = [BlockKey(*child) for child in block['fields']['children']]
            new_blocks[BlockKey(block['block_type'], block.pop('block_id'))] = BlockData(**block)
        structure['blocks'] = new_blocks

        if DEBUG: log.info('mcdaniel apr-2020: mongo_connection.py structure_from_mongo() - end')
        return structure


def structure_to_mongo(structure, course_context=None):
    """
    Converts the 'blocks' key from a map {BlockKey: block_data} to
        a list [block_data], inserting BlockKey.type as 'block_type'
        and BlockKey.id as 'block_id'.
    Doesn't convert 'root', since namedtuple's can be inserted
        directly into mongo.
    """
    with TIMER.timer('structure_to_mongo', course_context) as tagger:
        tagger.measure('blocks', len(structure['blocks']))

        check('BlockKey', structure['root'])
        check('dict(BlockKey: BlockData)', structure['blocks'])
        for block in six.itervalues(structure['blocks']):
            if 'children' in block.fields:
                check('list(BlockKey)', block.fields['children'])

        new_structure = dict(structure)
        new_structure['blocks'] = []

        for block_key, block in six.iteritems(structure['blocks']):
            new_block = dict(block.to_storable())
            new_block.setdefault('block_type', block_key.type)
            new_block['block_id'] = block_key.id
            new_structure['blocks'].append(new_block)

        return new_structure


class CourseStructureCache(object):
    """
    Wrapper around django cache object to cache course structure objects.
    The course structures are pickled and compressed when cached.

    If the 'course_structure_cache' doesn't exist, then don't do anything for
    for set and get.
    """
    def __init__(self):
        if DEBUG: log.info('mcdaniel apr-2020: CourseStructureCache.__init__() - begin')
        self.cache = None
        if DJANGO_AVAILABLE:
            try:
                self.cache = get_cache('course_structure_cache')
                if DEBUG: log.info('mcdaniel apr-2020: CourseStructureCache.__init__() - set Django cache object')
            except InvalidCacheBackendError:
                pass
        if DEBUG: log.info('mcdaniel apr-2020: CourseStructureCache.__init__() - end')


    def _memcached_num_chunks(self, object_size):
        """calculates the number of chunks which an object must be broken
        into so that the object accords with the Memcached MAX_VALUE_LENGTH
        constraint (which usually is 1MB).

        Arguments:
            object_size {int} -- raw size of object to be cached, in bytes.

        Returns:
            [int] -- [number of chunks required]
        """
        quotient = float(object_size) / float(MEMCACHED_MAX_VALUE_LENGTH)
        ceiling = math.ceil(quotient)
        chunks = int(ceiling)
        if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache._memcached_num_chunks() size: {size}, chunks: {chunks}'.format(
            size=object_size,
            chunks=chunks
        ))
        return chunks

    def _memcached_key_suffix(self, i):
        """generate a hash suffix of the form ###-### which will be
        appended to chunked objects for serialization.

        Arguments:
            i {int} -- identifies which chunk.
            n {int} -- total number of chunks.
        """
        retval = str(i).zfill(3)
        if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache._memcached_key_suffix() retval={retval}'.format(
            retval=retval
        ))
        return retval

    def _memcached_chunkify(self, i, val):
        """return the ith chunk of a cache-bound value.

        Arguments:
            i {int} -- indicates which i of n chunk to return
            val {string?} -- a zlib-compressed and pickled json object
        """
        start = (i - 1) * MEMCACHED_MAX_VALUE_LENGTH
        end = min((i * MEMCACHED_MAX_VALUE_LENGTH), len(val))
        return val[start:end]


    def get(self, key, course_context=None):
        """Pull the compressed, pickled struct data from cache and deserialize."""
        if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - begin')
        if self.cache is None:
            return None

        key = str(key)
        with TIMER.timer("CourseStructureCache.get", course_context) as tagger:
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 1')

            # retrieve the master cache object containing a string representation of
            # an integer representing the number of chunks for this object.
            n = self.cache.get(key)
            if not n:
                if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - cache miss.')
                return

            try:
                n = int(float(n))
            except ItemNotFoundError:
                if DEBUG: log.error('Invalid data encountered trying to retrieve the chunk count for key {key}. You might need to restart memcached.'.format(
                    key=key
                ))
                return


            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - chunks: {n}'.format(
                n=n
            ))

            compressed_pickled_data = None
            i = 1
            checksum = 0
            while i <= n:
                chunk_key = key + self._memcached_key_suffix(i)
                chunk = self.cache.get(chunk_key)
                if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - chunk: {i} key: {key}, size: {size}'.format(
                    i=i,
                    key=chunk_key,
                    size=len(chunk)
                ))
                if chunk is None:
                    return
                #    raise Exception('Internal error: cache miss: key={key}'.format(
                #        key=key+key_suffix
                #    ))

                if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - compressed_pickled_data: {t}'.format(
                    t=type(chunk)
                ))
                compressed_pickled_data = chunk if i == 1 else compressed_pickled_data + chunk
                i += 1
                checksum += len(chunk)


            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 2')
            tagger.tag(from_cache=str(compressed_pickled_data is not None).lower())

            if compressed_pickled_data is None:
                # Always log cache misses, because they are unexpected
                tagger.sample_rate = 1
                if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - end (cache miss)')
                return None

            tagger.measure('compressed_size', len(compressed_pickled_data))
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 3 compressed_pickled_data: {size}'.format(
                size=len(compressed_pickled_data)
            ))

            pickled_data = zlib.decompress(compressed_pickled_data)
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 4')
            tagger.measure('uncompressed_size', len(pickled_data))
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 5')

            tmp = pickle.loads(pickled_data)
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - 6')
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.get() - end')

            return tmp

    def set(self, key, structure, course_context=None):
        """Given a structure, will pickle, compress, and write to cache."""
        key = str(key)
        if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.set() - begin key: {key}'.format(
            key=key
        ))
        if self.cache is None:
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.set() - end (no cache!)')
            return None

        with TIMER.timer("CourseStructureCache.set", course_context) as tagger:
            pickled_data = pickle.dumps(structure, 4)  # Protocol can't be incremented until cache is cleared
            tagger.measure('uncompressed_size', len(pickled_data))

            # 1 = Fastest (slightly larger results)
            compressed_pickled_data = zlib.compress(pickled_data, 1)
            object_size = len(compressed_pickled_data)
            tagger.measure('compressed_size', object_size)

            # Stuctures are immutable, so we set a timeout of "never"
            #self.cache.set(key, compressed_pickled_data, None)

            # set the master cache entry containing only
            # an integer value representing the number of chunks
            # this structure requires.
            n = self._memcached_num_chunks(object_size)
            if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.set() - chunks: {n}'.format(
                n=n,
            ))
            self.cache.set(key, str(n), None)

            i = 1
            checksum = 0
            while i <= n:
                chunk = self._memcached_chunkify(i, compressed_pickled_data)
                chunk_key = key + self._memcached_key_suffix(i)
                if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.set() - chunk: {i}, key: {key}, size: {size}'.format(
                    i=i,
                    key=chunk_key,
                    size=len(chunk)
                ))
                self.cache.set(chunk_key, chunk, None)
                checksum += len(chunk)
                i += 1


        if DEBUG: log.info('mcdaniel apr-2020 CourseStructureCache.set() - end. key: {key}, compressed_pickled_data: {size}, checksum: {checksum}'.format(
            key=key,
            size=len(compressed_pickled_data),
            checksum=checksum
        ))

class MongoConnection(object):
    """
    Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
    """
    def __init__(
        self, db, collection, host, port=27017, tz_aware=True, user=None, password=None,
        asset_collection=None, retry_wait_time=0.1, **kwargs
    ):
        """
        Create & open the connection, authenticate, and provide pointers to the collections
        """
        # Set a write concern of 1, which makes writes complete successfully to the primary
        # only before returning. Also makes pymongo report write errors.
        kwargs['w'] = 1

        self.database = connect_to_mongodb(
            db, host,
            port=port, tz_aware=tz_aware, user=user, password=password,
            retry_wait_time=retry_wait_time, **kwargs
        )

        self.course_index = self.database[collection + '.active_versions']
        self.structures = self.database[collection + '.structures']
        self.definitions = self.database[collection + '.definitions']

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        try:
            # The ismaster command is cheap and does not require auth.
            self.database.client.admin.command('ismaster')
            return True
        except pymongo.errors.ConnectionFailure:
            raise HeartbeatFailure("Can't connect to {}".format(self.database.name), 'mongo')

    def get_structure(self, key, course_context=None):
        """
        Get the structure from the persistence mechanism whose id is the given key.

        This method will use a cached version of the structure if it is available.
        """
        if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() key: {key}, course_context: {course_context}'.format(
            key=key,
            course_context=course_context
        ))
        with TIMER.timer("get_structure", course_context) as tagger_get_structure:
            if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 1')
            cache = CourseStructureCache()
            if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 2')

            structure = cache.get(key, course_context)
            if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 3')
            tagger_get_structure.tag(from_cache=str(bool(structure)).lower())
            if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 4')

            if not structure:
                # Always log cache misses, because they are unexpected
                tagger_get_structure.sample_rate = 1

                with TIMER.timer("get_structure.find_one", course_context) as tagger_find_one:
                    if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 5')
                    doc = self.structures.find_one({'_id': key})
                    if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 6')
                    if doc is None:
                        log.warning(
                            "doc was None when attempting to retrieve structure for item with key %s",
                            six.text_type(key)
                        )
                        return None
                    tagger_find_one.measure("blocks", len(doc['blocks']))
                    if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 7')
                    structure = structure_from_mongo(doc, course_context)
                    if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 8')
                    tagger_find_one.sample_rate = 1

                cache.set(key, structure, course_context)
                if DEBUG: log.info('mcdaniel apr-2020: MongoConnection.get_structure() - 9 key: {key}, course_context: {course_context}'.format(
                    key=key,
                    course_context=course_context
                ))

            return structure

    @autoretry_read()
    def find_structures_by_id(self, ids, course_context=None):
        """
        Return all structures that specified in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        with TIMER.timer("find_structures_by_id", course_context) as tagger:
            tagger.measure("requested_ids", len(ids))
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({'_id': {'$in': ids}})
            ]
            tagger.measure("structures", len(docs))
            return docs

    @autoretry_read()
    def find_courselike_blocks_by_id(self, ids, block_type, course_context=None):
        """
        Find all structures that specified in `ids`. Among the blocks only return block whose type is `block_type`.

        Arguments:
            ids (list): A list of structure ids
            block_type: type of block to return
        """
        with TIMER.timer("find_courselike_blocks_by_id", course_context) as tagger:
            tagger.measure("requested_ids", len(ids))
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find(
                    {'_id': {'$in': ids}},
                    {'blocks': {'$elemMatch': {'block_type': block_type}}, 'root': 1}
                )
            ]
            tagger.measure("structures", len(docs))
            return docs

    @autoretry_read()
    def find_structures_derived_from(self, ids, course_context=None):
        """
        Return all structures that were immediately derived from a structure listed in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        with TIMER.timer("find_structures_derived_from", course_context) as tagger:
            tagger.measure("base_ids", len(ids))
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({'previous_version': {'$in': ids}})
            ]
            tagger.measure("structures", len(docs))
            return docs

    @autoretry_read()
    def find_ancestor_structures(self, original_version, block_key, course_context=None):
        """
        Find all structures that originated from ``original_version`` that contain ``block_key``.

        Arguments:
            original_version (str or ObjectID): The id of a structure
            block_key (BlockKey): The id of the block in question
        """
        with TIMER.timer("find_ancestor_structures", course_context) as tagger:
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({
                    'original_version': original_version,
                    'blocks': {
                        '$elemMatch': {
                            'block_id': block_key.id,
                            'block_type': block_key.type,
                            'edit_info.update_version': {
                                '$exists': True,
                            },
                        },
                    },
                })
            ]
            tagger.measure("structures", len(docs))
            return docs

    def insert_structure(self, structure, course_context=None):
        """
        Insert a new structure into the database.
        """
        with TIMER.timer("insert_structure", course_context) as tagger:
            tagger.measure("blocks", len(structure["blocks"]))
            self.structures.insert_one(structure_to_mongo(structure, course_context))

    def get_course_index(self, key, ignore_case=False):
        """
        Get the course_index from the persistence mechanism whose id is the given key
        """
        with TIMER.timer("get_course_index", key):
            if ignore_case:
                query = {
                    key_attr: re.compile(u'^{}$'.format(re.escape(getattr(key, key_attr))), re.IGNORECASE)
                    for key_attr in ('org', 'course', 'run')
                }
            else:
                query = {
                    key_attr: getattr(key, key_attr)
                    for key_attr in ('org', 'course', 'run')
                }
            return self.course_index.find_one(query)

    def find_matching_course_indexes(
            self,
            branch=None,
            search_targets=None,
            org_target=None,
            course_context=None,
            course_keys=None

    ):
        """
        Find the course_index matching particular conditions.

        Arguments:
            branch: If specified, this branch must exist in the returned courses
            search_targets: If specified, this must be a dictionary specifying field values
                that must exist in the search_targets of the returned courses
            org_target: If specified, this is an ORG filter so that only course_indexs are
                returned for the specified ORG
        """
        with TIMER.timer("find_matching_course_indexes", course_context):
            query = {}
            if course_keys:
                courses_queries = self._generate_query_from_course_keys(branch, course_keys)
                query['$or'] = courses_queries
            else:
                if branch is not None:
                    query['versions.{}'.format(branch)] = {'$exists': True}

                if search_targets:
                    for key, value in six.iteritems(search_targets):
                        query['search_targets.{}'.format(key)] = value

                if org_target:
                    query['org'] = org_target

            return self.course_index.find(query)

    def _generate_query_from_course_keys(self, branch, course_keys):
        """
        Generate query for courses using course keys
        """
        courses_queries = []
        query = {}
        if branch:
            query = {'versions.{}'.format(branch): {'$exists': True}}

        for course_key in course_keys:
            course_query = {
                key_attr: getattr(course_key, key_attr)
                for key_attr in ('org', 'course', 'run')
            }
            course_query.update(query)
            courses_queries.append(course_query)

        return courses_queries

    def insert_course_index(self, course_index, course_context=None):
        """
        Create the course_index in the db
        """
        with TIMER.timer("insert_course_index", course_context):
            course_index['last_update'] = datetime.datetime.now(pytz.utc)
            self.course_index.insert_one(course_index)

    def update_course_index(self, course_index, from_index=None, course_context=None):
        """
        Update the db record for course_index.

        Arguments:
            from_index: If set, only update an index if it matches the one specified in `from_index`.
        """
        with TIMER.timer("update_course_index", course_context):
            if from_index:
                query = {"_id": from_index["_id"]}
                # last_update not only tells us when this course was last updated but also helps
                # prevent collisions
                if 'last_update' in from_index:
                    query['last_update'] = from_index['last_update']
            else:
                query = {
                    'org': course_index['org'],
                    'course': course_index['course'],
                    'run': course_index['run'],
                }
            course_index['last_update'] = datetime.datetime.now(pytz.utc)
            self.course_index.replace_one(query, course_index, upsert=False,)

    def delete_course_index(self, course_key):
        """
        Delete the course_index from the persistence mechanism whose id is the given course_index
        """
        with TIMER.timer("delete_course_index", course_key):
            query = {
                key_attr: getattr(course_key, key_attr)
                for key_attr in ('org', 'course', 'run')
            }
            return self.course_index.remove(query)

    def get_definition(self, key, course_context=None):
        """
        Get the definition from the persistence mechanism whose id is the given key
        """
        with TIMER.timer("get_definition", course_context) as tagger:
            definition = self.definitions.find_one({'_id': key})
            tagger.measure("fields", len(definition['fields']))
            tagger.tag(block_type=definition['block_type'])
            return definition

    def get_definitions(self, definitions, course_context=None):
        """
        Retrieve all definitions listed in `definitions`.
        """
        with TIMER.timer("get_definitions", course_context) as tagger:
            tagger.measure('definitions', len(definitions))
            definitions = self.definitions.find({'_id': {'$in': definitions}})
            return definitions

    def insert_definition(self, definition, course_context=None):
        """
        Create the definition in the db
        """
        with TIMER.timer("insert_definition", course_context) as tagger:
            tagger.measure('fields', len(definition['fields']))
            tagger.tag(block_type=definition['block_type'])
            self.definitions.insert_one(definition)

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """
        create_collection_index(
            self.course_index,
            [
                ('org', pymongo.ASCENDING),
                ('course', pymongo.ASCENDING),
                ('run', pymongo.ASCENDING)
            ],
            unique=True,
            background=True
        )

    def close_connections(self):
        """
        Closes any open connections to the underlying databases
        """
        self.database.client.close()

    def _drop_database(self, database=True, collections=True, connections=True):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.

        If database is True, then this should drop the entire database.
        Otherwise, if collections is True, then this should drop all of the collections used
        by this modulestore.
        Otherwise, the modulestore should remove all data from the collections.

        If connections is True, then close the connection to the database as well.
        """
        connection = self.database.client

        if database:
            connection.drop_database(self.database.name)
        elif collections:
            self.course_index.drop()
            self.structures.drop()
            self.definitions.drop()
        else:
            self.course_index.remove({})
            self.structures.remove({})
            self.definitions.remove({})

        if connections:
            connection.close()
