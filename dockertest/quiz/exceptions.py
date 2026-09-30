from rest_framework.exceptions import APIException
from rest_framework import status 
from rest_framework.views import exception_handler
from rest_framework.response import Response

class AlreadyAplliedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'You hva already apply for this job'
    default_code = 'already_applied'

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        custom_data ={
            'success':False,
            "error":{
                "status_code":response.status_code,
                "message":getattr(exc, "default_detail", 'an error occured'),
                "details":response.data
            }
        }
        response.data = custom_data
    return response