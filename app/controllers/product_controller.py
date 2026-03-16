
from app.services.product_implementation import ProductImplementation
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = ProductImplementation()


class ProductController:
    

    async def create_product(
        self, data: CreateProductRequest, business_context: dict
    ) -> dict:
        try:
            return await _impl.create_product(data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_products(self, business_context: dict) -> dict:
        try:
            return await _impl.list_products(business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_product(self, product_id: str, business_context: dict) -> dict:
        try:
            return await _impl.get_product(product_id, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_product(
        self, product_id: str, data: UpdateProductRequest, business_context: dict
    ) -> dict:
        try:
            return await _impl.update_product(product_id, data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def delete_product(self, product_id: str, business_context: dict) -> dict:
        try:
            return await _impl.delete_product(product_id, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
