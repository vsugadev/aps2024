
# Flask settings
SECRET_KEY = '65a0bc61e8a2cea990f12811e3881cae12'
WTF_CSRF_ENABLED = False

# Flask-SQLAlchemy settings
# SQLALCHEMY_DATABASE_URI = 'mysql://APSManager:Vanakkam1330@APSManager.mysql.pythonanywhere-services.com/APSManager$portal'
SQLALCHEMY_DATABASE_URI = 'mysql://APSManagementSys:Vanakkam1330@APSManagementSystem.mysql.pythonanywhere-services.com/APSManagementSys$portal'

SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning
SQLALCHEMY_POOL_RECYCLE = 1 # 28800
SQLALCHEMY_POOL_PRE_PING=True

# Flask-User settings
USER_APP_NAME = "ஔவையார் பாடசாலை - உலகின் முதல் மெய்நிகர்த் தமிழ்ப்பள்ளி"  # Shown in and email templates and page footers
USER_ENABLE_EMAIL = True      # Disable email authentication
USER_ENABLE_USERNAME = False  # Enable username authentication
USER_REQUIRE_RETYPE_PASSWORD = True    # Simplify register form
USER_ENABLE_REGISTER = True  # Disable new enrollments into portal for time being

USER_AUTO_LOGIN = False  #: Automatic sign-in if the user session has not expired.
USER_AUTO_LOGIN_AFTER_CONFIRM = False  #: Automatic sign-in after a user confirms their email address.
USER_AUTO_LOGIN_AFTER_REGISTER = False #: Automatic sign-in after a user registers.
USER_AUTO_LOGIN_AFTER_RESET_PASSWORD = False #: Automatic sign-in after a user resets their password.
#USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL = False
USER_SHOW_EMAIL_DOES_NOT_EXIST = True

MAIL_SERVER = 'smtp.gmail.com'
MAIL_USERNAME = 'aps_techsupport2@avvaiyarpadasalai.org' #'myaps@avvaiyarpadasalai.org' # 'apsportal100@gmail.com' # 'myaps@avvaiyarpadasalai.org' # '122@gmail.com'
#MAIL_PASSWORD = 'MyAPS@2025' # 'MyAPS@2023' # 'Portal@2022' # 'odjr rkfk nawn idoz' # 'AvvaiyarPadasalai@2022' # 'Newuser@123' # 'Myaps@2021' # 'kmthnznf'
MAIL_PASSWORD = 'AP$ADMIN@2024' #'HJ59J7FKggS99qK%'
MAIL_DEFAULT_SENDER = 'aps_techsupport2@avvaiyarpadasalai.org' #'myaps@avvaiyarpadasalai.org' # 'apsportal100@gmail.com' # 'myaps@avvaiyarpadasalai.org' # 'contact@...''

SCHOOL_NAME = 'Avvaiyar Padasalai'
MAIL_SENDER_NAME = SCHOOL_NAME
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
TESTING = False
USER_PROD_MODE = True # change to true for prod. APP look and feel would change for production. False for dev mode
DEBUG = True
TEST_RECIPIENTS=[''] #['admin@avvaiyarpadasalai.org']

# Application specific config
USER_ACADEMIC_YEAR = 2024
ACADEMIC_YEAR = 2024
ACADEMIC_YEAR_NEW = 2025
ACADEMIC_YEAR_LABEL = '2024-25'
NEW_ENROLL = USER_ENABLE_REGISTER
PASSING_SCORE = 0
LOCKOUT_DAYS_ATTENDANCE = 180
ROLLOVER = True

# PayPal Config
# PAYPAL_MODE = "sandbox" # Developer mode # sandbox or live
# PAYPAL_CLIENT_ID = "AXQuOG8P0UV2kMC1bTPXCleLDhwxfWlWQtcTQIAMrWJQoj_31iSVkaGnIK0C9VoSTCyuc3BEe1IgOHFD"
# PAYPAL_CLIENT_SECRET = "EDyRngfmfmaN3yr3gWBPA2_vdBpt5rYtTvzA175pRHCpZakLDVPBCjQwFV7Q_Hjre0p-RQwsIQRNdFEj"

# amchats paypal
#PAYPAL_MODE = "live" # sandbox or live
#PAYPAL_CLIENT_ID = "AUjpXMJw7clPaJxJROcZgP-XWRVsGpF08f37WQsw08LVRH3hsSoo-jp-ygZUUc1gM3z_7TvA9UMN_uLe"
#PAYPAL_CLIENT_SECRET = "EBwSok8PPn9OHJdUX6DO91onZdMYC3Ea49gbQfNkHtTJH9oOW4EM4hKdOoCeQgdubG1MXvU37Mg3VrxO"

# aps paypal
PAYPAL_MODE = "live"
PAYPAL_CLIENT_ID = "AWQ5BulNCSj1yJXnCLKeIoDB4hJ6peqkoACev1ibtTIHyWYIoIiBLXqZuZ0BRloQsBSOpLoBVLvQTlVk"
PAYPAL_CLIENT_SECRET = "EBvphZgow4LlmkZXM8Q64KF2Yjg6K0YUqvx87_UZwyKtcYvj855ZoMYkqiSSpNjSenfLrC1ZHpXgZU6D"

