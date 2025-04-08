#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sqlite3
import json


class DataBase(object):
    def __init__(self):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.create_user_post_table()
        self.create_user_like_table()
        self.create_mix_table()
        self.create_music_table()
        self.create_user_collection_table()

    def create_user_post_table(self):
        sql = """CREATE TABLE if not exists t_user_post (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        aweme_id integer unique, 
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            pass

    def create_user_collection_table(self):
        sql = """CREATE TABLE if not exists t_user_collection (
                    id integer primary key autoincrement,
                    sec_uid varchar(200),
                    user_link varchar(500),
                    custom_name varchar(200),
                    add_time timestamp default CURRENT_TIMESTAMP
                );"""
        
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            pass
            
    def get_all_users(self):
        sql = """select id, sec_uid, user_link, custom_name, add_time from t_user_collection order by add_time desc;"""
        
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return self.cursor.fetchall()
        except Exception as e:
            return []
            
    def add_user_to_collection(self, sec_uid, user_link, custom_name):
        check_sql = """select id from t_user_collection where sec_uid=?;"""
        
        try:
            self.cursor.execute(check_sql, (sec_uid,))
            existing = self.cursor.fetchone()
            
            if existing:
                update_sql = """update t_user_collection set user_link=?, custom_name=?, add_time=CURRENT_TIMESTAMP where sec_uid=?;"""
                self.cursor.execute(update_sql, (user_link, custom_name, sec_uid))
            else:
                insert_sql = """insert into t_user_collection (sec_uid, user_link, custom_name) values(?,?,?);"""
                self.cursor.execute(insert_sql, (sec_uid, user_link, custom_name))
                
            self.conn.commit()
            return True
        except Exception as e:
            return False
            
    def delete_user_from_collection(self, user_id):
        sql = """delete from t_user_collection where id=?;"""
        
        try:
            self.cursor.execute(sql, (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            return False

    def get_user_post(self, sec_uid: str, aweme_id: int):
        sql = """select id, sec_uid, aweme_id, rawdata from t_user_post where sec_uid=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            pass

    def insert_user_post(self, sec_uid: str, aweme_id: int, data: dict):
        insertsql = """insert into t_user_post (sec_uid, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            pass

    def create_user_like_table(self):
        sql = """CREATE TABLE if not exists t_user_like (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        aweme_id integer unique,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            pass

    def get_user_like(self, sec_uid: str, aweme_id: int):
        sql = """select id, sec_uid, aweme_id, rawdata from t_user_like where sec_uid=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            pass

    def insert_user_like(self, sec_uid: str, aweme_id: int, data: dict):
        insertsql = """insert into t_user_like (sec_uid, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            pass

    def create_mix_table(self):
        sql = """CREATE TABLE if not exists t_mix (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        mix_id varchar(200),
                        aweme_id integer,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            pass

    def get_mix(self, sec_uid: str, mix_id: str, aweme_id: int):
        sql = """select id, sec_uid, mix_id, aweme_id, rawdata from t_mix where sec_uid=? and  mix_id=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, mix_id, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            pass

    def insert_mix(self, sec_uid: str, mix_id: str, aweme_id: int, data: dict):
        insertsql = """insert into t_mix (sec_uid, mix_id, aweme_id, rawdata) values(?,?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, mix_id, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            pass

    def create_music_table(self):
        sql = """CREATE TABLE if not exists t_music (
                        id integer primary key autoincrement,
                        music_id varchar(200),
                        aweme_id integer unique,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            pass

    def get_music(self, music_id: str, aweme_id: int):
        sql = """select id, music_id, aweme_id, rawdata from t_music where music_id=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (music_id, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            pass

    def insert_music(self, music_id: str, aweme_id: int, data: dict):
        insertsql = """insert into t_music (music_id, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (music_id, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            pass


if __name__ == '__main__':
    pass
