# -*- coding: utf-8 -*-
import time
from sqlite3 import dbapi2 as sqlite3
from datetime import datetime
from random import randint
import time

def get_db():
	connection = sqlite3.connect('twitter-clone.db')
	return connection

def query_db(query, args=(), one=False):
	"""Queries the database and returns a list of dictionaries."""
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	return (rv[0] if rv else None) if one else rv


def init_db():
	get_db().cursor().executescript('''create table user (id int primary key, username text, signup datetime default current_timestamp);
		create table follows (user_id_1 int, user_id_2 int, primary key(user_id_1, user_id_2), foreign key (user_id_1) references user(id), foreign key (user_id_2) references user(id));
		create table status (id int primary key, user_id int, message text, time datetime default current_timestamp, foreign key (user_id) references user(id));''')
	get_db().commit()

def user_timeline(user_id):
	result = query_db('''select status.*, user.* from status, user
		where status.user_id = ? or
			status.user_id in (select user_id_2 from follows
									where user_id_1 = ?)
		order by status.time''', [user_id, user_id])

	print result

def follow_user(id1, id2):
	db = get_db()
	db.execute('insert into follows (user_id_1, user_id_2) values (?, ?)', [id1, id2])
	
	db.commit()

def create_status(id, message):
	db = get_db()
	db.execute('insert into status (user_id, message) values (?, ?)', [id, message])
	db.commit()

def create_user(username):
	db = get_db()
	db.execute('insert into user (username) values (?)', [username])
	db.commit()

def main():
	init_db()

	for user in range(0,10000):
		print "creating user %s" %user
		create_user('user%s'%user)

	for user in range(0,10000):
		following = []
		for r in range(0,200):
			random = randint(0,10000)
			if random != user and random not in following:
				follow_user(user, random)
				following.append(random)

	for user in range(0,10000):
		for status in range(0,100):
			message = "Status %s for user %s"%(status,user)
			print message
			create_status(user, message)

if __name__ == '__main__':
	main()