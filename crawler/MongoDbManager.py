import pymongo
from pymongo.errors import PyMongoError
from pymongo import errors
from flask import current_app

import threading

from crawler.constants import lessor_sex_dict, lesser_role_dict

lock = threading.Lock()


class MongoDbManager:
    __instance = None
    __client = None
    __db = None
    __collection = None

    def __init__(self):
        raise SyntaxError('can not instance, please use get_instance')

    @classmethod
    def get_instance(cls, app):
        """
        thread function for get MongoDbManager instance
        :return: singleton
        """
        if cls.__instance is None:
            with lock:
                if cls.__instance is None:
                    cls.__client = pymongo.MongoClient(
                        app.config.get('MONGODB_SERVER'),
                        app.config.get('MONGODB_PORT'),
                        serverSelectionTimeoutMS=2000
                    )
                    try:
                        app.logger.info(cls.__client.server_info())
                    except errors.ServerSelectionTimeoutError as err:
                        app.logger.error("Connection to MongoDB Error", stack_info=err)
                        cls.__client = None
                        return None
                    cls.db_name = app.config.get('MONGODB_DATABASE')
                    cls.collection_name = app.config.get('MONGODB_COLLECTION')
                    cls.__instance = object.__new__(cls)
                    cls.__instance._check_target_db(app)
                    cls.__instance._check_target_collection(app)
                    cls.__instance._create_index()

        return cls.__instance

    def _check_target_db(self, app):
        """
        thread function for check database existence, create if not exist
        """
        if self.__client is None:
            app.logger.error('get mongodb client error: ')
            return None
        db_names = self.__client.list_database_names()
        if self.db_name not in db_names:
            app.logger.info('create db {} success: '.format(self.db_name))
        else:
            app.logger.info('db {} already exists: '.format(self.db_name))
        self.__db = self.__client[app.config.get('MONGODB_DATABASE')]

    def _check_target_collection(self, app):
        """
        thread function for check collection existence, create if not exist
        """
        if self.__db is None:
            app.logger.error('mongodb db {} not exist: '.format(self.db_name))
            return None
        collections = self.__db.list_collection_names()
        if self.collection_name not in collections:
            app.logger.info('create collection {} success: '.format(self.collection_name))
        else:
            app.logger.info('collection {} already exists: '.format(self.collection_name))
        self.__collection = self.__db[self.collection_name]

    def update(self, houses, app):
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
                    response = self.__collection.update_one({'_id': house_in_db['_id']}, {'$set': modified_fields})
                    res.append('update-' + house['id'] + '-' + existed_id)
                else:
                    res.append('duplicate-' + house['id'] + '-' + existed_id)
            else:
                response = self.__collection.update_one({'id': house['id']}, {'$set': house}, upsert=True)
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
            'price': {'$lte': pattern.get('price_upper', 2 ** 31 - 1), '$gte': pattern.get('price_lower', 0)},
            'area': {'$lte': pattern.get('area_upper', 2 ** 31 - 1), '$gte': pattern.get('area_lower', 0)}}

        if pattern.get('linkman', ''):  # if specify lessor name already, you just can't choose lessor's gender again
            parsed_patterns['linkman.name'] = {'$regex': '.*' + ''.join(pattern['linkman']) + '.*'}
        else:
            if pattern['lessor_sex'] != '2':
                parsed_patterns['linkman.sex'] = pattern['lessor_sex']

        if pattern['role_type'] != '3':
            parsed_patterns['linkman.role'] = pattern['role_type']

        if pattern['tel'] != '':
            parsed_patterns['tel'] = {'$regex': '.*' + ''.join(pattern['tel']) + '.*'}

        if pattern['sex'] != '2':  # match patterns in constants.py
            parsed_patterns['sex_requirement'] = pattern['sex']

        parsed_patterns['regionid'] = pattern['regionid']

        current_app.logger.info('Attempt searching with patterns: {}'.format(str(parsed_patterns)))
        cursor = self.__collection.find(parsed_patterns)

        return cursor

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

    def get_client(self):
        return self.__client

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
        todo: find modified pattern for compound fields
        """
        pattern = {}
        for key, value in house.items():
            if house[key] != house_in_db[key]:
                pattern[key] = house[key]

        return pattern
