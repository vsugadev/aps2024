
#from flask_caching import Cache

# Instantiate the cache
#cache = Cache()
cache = {}
#config_dict = {}

def cache_config(app) :
    keys = app.config.keys()
    for key in keys :
    ## Do not cache db credetials.
        if not key.lower().startswith("sqlalchemy") :
            value =  app.config.get(key)
            cache.set(key, value)

def set_value(key, value) :
    return cache.set(key, value)

def get_value(key) :
    print(cache.keys())
    return cache[key]  #  cache.get(key)


def init(app) :
    config_dict = {}
    config_keys = [ 'USER_PROD_MODE', 'NEW_ENROLL', 'PASSING_SCORE', 'LOCKOUT_DAYS_ATTENDANCE', "PAYPAL_MODE", "PAYPAL_CLIENT_ID" , "PAYPAL_CLIENT_SECRET" , "ACADEMIC_YEAR"  ]
    for key in app.config.keys() :
    ## Do not cache db credetials.
        if key in config_keys :
            config_dict.update({key : app.config.get( key ) } )
    cache = config_dict
#    cache.init_app(app=app, config = config_dict )
    print( config_dict )
    print( cache )
    print(get_value("PAYPAL_MODE"))

