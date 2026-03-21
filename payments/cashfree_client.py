from cashfree_pg.api_client import Cashfree
from django.conf import settings

Cashfree.XClientId = settings.CASHFREE_CLIENT_ID
Cashfree.XClientSecret = settings.CASHFREE_CLIENT_SECRET
Cashfree.XEnvironment = settings.CASHFREE_ENVIRONMENT
Cashfree.XApiVersion = "2023-08-01"
