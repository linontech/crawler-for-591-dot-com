import pymongo
from pymongo.errors import PyMongoError
from pymongo import errors
from flask import current_app

import threading

lock = threading.Lock()


class MongoDbManager:
    __instance = None
    __client = None
    __db = None
    __collection = None

    def __init__(self):
        raise SyntaxError('can not instance, please use get_instance')

    @classmethod
    def get_instance(cls):
        """
        thread function for get MongoDbManager instance
        :return: singleton
        """
        if cls.__instance is None:
            with lock:
                if cls.__instance is None:
                    cls.__instance = object.__new__(cls)
                    cls.__client = cls.__instance.get_client()
                    try:
                        current_app.logger.info(cls.__client.server_info())
                    except errors.ServerSelectionTimeoutError as err:
                        current_app.logger.error(
                            "Connection to MongoDB Error", stack_info=err)
                        cls.__client = None
                        return None
                    cls.db_name = current_app.config.get('MONGODB_DATABASE')
                    cls.collection_name = current_app.config.get('MONGODB_COLLECTION')
                    cls.__instance._check_target_db()
                    cls.__instance._check_target_collection()
                    cls.__instance._create_index()

        return cls.__instance

    def get_client(self):
        if not self.__client:
            return pymongo.MongoClient(
                current_app.config.get('MONGODB_SERVER'),
                current_app.config.get('MONGODB_PORT'),
                serverSelectionTimeoutMS=2000
            )
        else:
            return self.__client

    def _check_target_db(self):
        """
        thread function for check database existence, create if not exist
        """
        if self.__client is None:
            current_app.logger.error('get mongodb client error: ')
            return None
        db_names = self.__client.list_database_names()
        if self.db_name not in db_names:
            current_app.logger.info('create db {} success: '.format(self.db_name))
        else:
            current_app.logger.info('db {} already exists: '.format(self.db_name))
        self.__db = self.__client.get_database(
            current_app.config.get('MONGODB_DATABASE'))

    def _check_target_collection(self):
        """
        thread function for check collection existence, create if not exist
        """
        if self.__db is None:
            current_app.logger.error('mongodb db {} not exist: '.format(self.db_name))
            return None
        collections = self.__db.list_collection_names()
        if self.collection_name not in collections:
            self.__collection = self.__db.create_collection(self.collection_name)
            current_app.logger.info(
                'create collection {} success: '.format(
                    self.collection_name))
        else:
            self.__collection = self.__db.get_collection(self.collection_name)
            current_app.logger.info(
                'collection {} already exists: '.format(
                    self.collection_name))

    def update(self, houses):
        """
        thread function for inserting houses
        :param houses: houses records
        :param app: app context
        :return:
        """
        res = []
        for house in houses:
            house_in_db = self._query_by_id(house['id'])
            if house_in_db:
                # app.logger.info('Found duplicate id {}, replace old data.'.format(house['id']))
                existed_id = str(house_in_db['_id'])
                modified_fields = self._find_modified_pattern(house, house_in_db)
                if modified_fields:
                    response = self.__collection.update_one(
                        {'_id': house_in_db['_id']}, {'$set': modified_fields})
                    res.append('update-' + house['id'] + '-' + existed_id)
                else:
                    res.append('duplicate-' + house['id'] + '-' + existed_id)
            else:
                response = self.__collection.update_one(
                    {'id': house['id']}, {'$set': house}, upsert=True)
                if response.matched_count > 0:
                    res.append('new-' + house['id'] + '-conflict')
                else:
                    res.append('new-' + house['id'] + '-' + str(response.upserted_id))

        return res

    def query_by_pattern(self, pattern):
        """
        should put frequently used fields in the front
        pattern['sex'], pattern['role_type'] should be passed in already
        :param pattern: a dict with patterns
        :return:
        """
        parsed_patterns = {
            'price': {
                '$lte': pattern.get('price_upper', 2 ** 31 - 1),
                '$gte': pattern.get('price_lower', 0)},
            'area': {
                '$lte': pattern.get('area_upper', 2 ** 31 - 1),
                '$gte': pattern.get('area_lower', 0)}
        }
        # TODO: handle KeyError Exception
        pattern['lessor_sex'] = pattern.get('lessor_sex', '')
        pattern['role_type'] = pattern.get('role_type', '')
        pattern['tel'] = pattern.get('tel', '')
        pattern['sex'] = pattern.get('sex', '')
        pattern['regionid'] = pattern.get('regionid', '')

        # if specify lessor name already, you just can't choose lessor's gender again
        if pattern.get('linkman', ''):
            # parsed_patterns['linkman.name'] = {'$regex': '.*' + ''.join(pattern['linkman']) + '.*'}
            pass
        else:
            if pattern['lessor_sex'] != '2' and pattern['lessor_sex']:
                parsed_patterns['linkman.sex'] = pattern['lessor_sex']
        if pattern['role_type'] != '3' and pattern['role_type']:
            parsed_patterns['linkman.role'] = pattern['role_type']

        if pattern['tel'] != '':
            parsed_patterns['tel'] = {'$regex': '.*' + ''.join(pattern['tel']) + '.*'}

        if pattern['sex'] != '2' and pattern['sex']:  # match patterns in constants.py
            parsed_patterns['sex_requirement'] = pattern['sex']

        parsed_patterns['regionid'] = pattern['regionid']

        current_app.logger.info('Attempt searching with patterns: {}'.format(str(parsed_patterns)))

        return self.__collection.find(parsed_patterns)

    def insert(self, houses):
        """
        preserved method
        :param houses:
        :return: inserted_id
        """
        try:
            response = self.__collection.insert_many(houses)
            return response.inserted_ids
        except PyMongoError as e:
            current_app.logger.error('insert_many() error', e)
        return []

    def _query_by_id(self, house_id):
        cursor = self.__collection.find_one({'id': house_id})
        return cursor

    def _create_index(self):
        """
        Handle duplicate insertions.
        """
        self.__collection.create_index('id', unique=True)

    def _close(self):
        self.__client.close()

    @staticmethod
    def _find_modified_pattern(house, house_in_db):
        """
        TODO: find modified pattern for compound fields
        """
        pattern = {}
        for key, value in house.items():
            if house[key] != house_in_db[key]:
                pattern[key] = house[key]

        return pattern
