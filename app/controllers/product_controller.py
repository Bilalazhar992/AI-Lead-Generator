from app.services.product_implementation import ProductImplementation
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = ProductImplementation()


class ProductController:
    """Thin HTTP layer — delegates all logic to ProductImplementation."""

    async def create_product(self, data: CreateProductRequest, ctx: dict) -> dict:
        try:
            return await _impl.create_product(data, ctx)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_all_products(self, ctx: dict) -> dict:
        try:
            return await _impl.get_all_products(ctx)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_product(self, product_id: str, ctx: dict) -> dict:
        try:
            return await _impl.get_product(product_id, ctx)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_product(self, product_id: str, data: UpdateProductRequest, ctx: dict) -> dict:
        try:
            return await _impl.update_product(product_id, data, ctx)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def delete_product(self, product_id: str, ctx: dict) -> dict:
        try:
            return await _impl.delete_product(product_id, ctx)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
