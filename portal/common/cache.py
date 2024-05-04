
class Cache(object) :
    cache = {}

    @staticmethod
    def init(app) :
        config_dict = {}
        config_keys = [ 'USER_PROD_MODE', 'NEW_ENROLL', 'PASSING_SCORE', 'LOCKOUT_DAYS_ATTENDANCE', "PAYPAL_MODE", "PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET",
                        "ACADEMIC_YEAR", "ACADEMIC_YEAR_LABEL", "SCHOOL_NAME" , "ROLLOVER" ]
        for key in app.config.keys() :
            if key in config_keys :
                config_dict.update({key : app.config.get( key ) } )
        Cache.cache = config_dict

    @staticmethod
    def set_value(key, value) :
        return Cache.cache.update({key : value})

    @staticmethod
    def get_value(key) :
        return Cache.cache.get(key)
