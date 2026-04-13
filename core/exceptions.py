from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the error response
        custom_response_data = {
            'error': {
                'message': str(exc),
                'status_code': response.status_code,
                'details': response.data
            }
        }
        response.data = custom_response_data
    
    return response


class InsufficientStockError(Exception):
    """Raised when trying to sell more than available stock"""
    pass


class ShopNotAssignedError(Exception):
    """Raised when user doesn't have a shop assigned"""
    pass


class MedicineNotFoundError(Exception):
    """Raised when medicine is not found in inventory"""
    pass
