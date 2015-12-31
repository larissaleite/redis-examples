import redis

from random import randint
import time

def create_user(conn, login):
	llogin = login.lower()
	id = conn.incr('user:id:')

	pipeline = conn.pipeline(True)
	pipeline.hset('users:', llogin, id)     
	pipeline.hmset('user:%s'%id, {          
		'login': login,                     
		'id': id,                           
		'followers': 0,                     
		'following': 0,                     
		'posts': 0,                         
		'signup': time.time(),              
	})
	pipeline.execute()
	return id

def post_status(conn, uid, message, **data):
	id = create_status(conn, uid, message, **data)  
	
	posted = conn.hget('status:%s'%id, 'posted')    

	post = {str(id): float(posted)}
	conn.zadd('profile:%s'%uid, **post)             

	followers = conn.zrange('followers:%s'%uid, 0, -1)   

	pipeline = conn.pipeline(False)

	for follower in followers:                    
		pipeline.zadd('home:%s'%follower, **post)        
		pipeline.zrange('home:%s'%follower, 0, -1)

	pipeline.execute()
	return id

def create_status(conn, uid, message, **data):
	pipeline = conn.pipeline(True)
	pipeline.hget('user:%s'%uid, 'login')   
	pipeline.incr('status:id:')             
	login, id = pipeline.execute()

	data.update({
		'message': message,                 
		'posted': time.time(),              
		'id': id,                           
		'uid': uid,                         
		'login': login,                     
	})
	pipeline.hmset('status:%s'%id, data)    
	pipeline.hincrby('user:%s'%uid, 'posts')
	pipeline.execute()
	return id

def follow_user(conn, uid, other_uid):
	fkey1 = 'following:%s'%uid          
	fkey2 = 'followers:%s'%other_uid    

	if conn.zscore(fkey1, other_uid):   
		return None                     

	now = time.time()

	pipeline = conn.pipeline(True)
	pipeline.zadd(fkey1, other_uid, now)    
	pipeline.zadd(fkey2, uid, now)          
	pipeline.zrange('profile:%s'%other_uid, 0, -1)   
	following, followers, status_and_score = pipeline.execute()[-3:]

	pipeline.hincrby('user:%s'%uid, 'following', int(following))        
	pipeline.hincrby('user:%s'%other_uid, 'followers', int(followers))  

	pipeline.execute()
	return True

def retrieve_timeline(conn, uid):
	pipeline = conn.pipeline(True)

	statuses = conn.zrange('%s%s'%('home:', uid), 0, -1)   

	pipeline = conn.pipeline(True)
	for id in statuses:                                         
		pipeline.hgetall('status:%s'%id)  

		for results in pipeline.execute():
			print results                        

	return pipeline.execute()                    

def retrieve_followers(conn, uid):
	followers = conn.zrange('followers:%s'%uid, 0, -1)   

	pipeline = conn.pipeline(False)

	for follower in followers:
		pipeline.hgetall('user:%s'%follower)
		print pipeline.execute()

def retrieve_following(conn, uid):
	following = conn.zrange('following:%s'%uid, 0, -1)   

	pipeline = conn.pipeline(False)

	for followed in following:
		pipeline.hgetall('user:%s'%followed)
		print pipeline.execute()

def main():
	conn = redis.Redis(db=10)
	conn.flushdb() #cleans the database

	for user in range(0,10000):
		print "creating user %s" %user
		create_user(conn, 'user%s'%user)

	for user in range(0,10000):
		following = []
		for r in range(0,200):
			random = randint(0,10000)
			if random != user and random not in following:
				follow_user(conn, user, random)
				following.append(random)

	for user in range(0,10000):
		for status in range(0,100):
			post_status(conn, user, "Status %s for user %s"%(status,user))

	time_timeline = 0
	time_followers = 0
	time_following = 0

	sts = time.time()
	retrieve_timeline(conn, 102)
	ste = time.time()
	time_timeline = ste-sts

	sts = time.time()
	retrieve_followers(conn, 102)
	ste = time.time()
	time_followers = ste-sts

	sts = time.time()
	retrieve_following(conn, 102)
	ste = time.time()
	time_following = ste-sts

	print "[---Testing TIMELINE---] %s"%time_timeline
	print "[---Testing FOLLOWERS---] %s"%time_followers
	print "[---Testing FOLLOWING---] %s"%time_following

if __name__ == '__main__':
	main()