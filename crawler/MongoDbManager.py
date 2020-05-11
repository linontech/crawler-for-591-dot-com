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
                    cls.db_name = app.config.get('MONGODB_DATABASE')
                    cls.collection_name = app.config.get('MONGODB_COLLECTION')
                    cls.__instance = object.__new__(cls)

        return cls.__instance

    def check_target_db(self, app):
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

    def check_target_collection(self, app):
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
        :return:
        """
        res = []
        for house in houses:
            house_in_db = self._query_by_id(house['id'])
            if house_in_db.count() != 0:
                app.logger.info('Found duplicate id {}'.format(house['id']))
            response = self.__collection.replace_one({'id': house['id']}, house, upsert=True)
            res.append(response.upserted_id)

        return res

    def query_by_pattern(self, pattern):
        """
        pattern['sex'], pattern['role'] should be passed in already
        :param pattern: a dict with patterns
        :return:
        """
        parsed_pattern = [{'regionid': pattern['regionid']}]

        if pattern['sex'] != '0':  # match patterns in constants.py
            parsed_pattern.append({'sex_requirement': pattern['sex']})
        if pattern['role_type'] == '1':
            parsed_pattern.append({'linkman_role': '0'})
        if pattern['role_type'] == '0':
            role_pattern = []
            for key, value in lesser_role_dict.items():
                if value != '0' and key != 'unknown':
                    role_pattern.append(value)
            parsed_pattern.append({'linkman_role': {'$regex': '|'.join(role_pattern)}})
        if pattern['tel'] != '':
            parsed_pattern.append({'tel': {'$regex': '.*' + ''.join(pattern['tel']) + '.*'}})

        if pattern.get('linkman', ''):  # if specify lessor name already, you just can't choose lessor's gendar again
            parsed_pattern.append({'linkman': {'$regex': '.*' + ''.join(pattern['linkman']) + '.*'}})
        else:
            sex_pattern = []
            for key, value in lessor_sex_dict.items():
                if value == pattern['lessor_sex'] and key != '不限':  # lessor_sex is a Required Field
                    sex_pattern.append('.*' + key + '.*')
            parsed_pattern.append({'linkman': {'$regex': '|'.join(sex_pattern)}})
        parsed_patterns = {'$and': parsed_pattern}
        current_app.logger.info('Attempt searching with patterns: {}'.format(str(parsed_patterns)))
        cursor = self.__collection.find(parsed_patterns)

        return cursor

    def insert(self, houses):
        """
        preserved method, using replace_one() with upsert=True instead
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

    def _query_by_id(self, _id):
        cursor = self.__collection.find({'id': _id})
        return cursor

    def _close(self):
        self.__client.close()
