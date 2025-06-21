from typing import Any
from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, CoreSchema

class PyObjectId(ObjectId):
    """ Custom Pydantic type for MongoDB's ObjectId """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """
        Pydantic V2 compatible schema for ObjectId.
        It handles validation from a string and serialization to a string.
        """
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(
                                cls.validate
                            ),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance)
            ),
        )

    @classmethod
    def validate(cls, value: str) -> "PyObjectId":
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return cls(value)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetCoreSchemaHandler
    ):
        json_schema = handler(schema)
        json_schema.update(
            type="string",
            format="ObjectId",
            pattern="^[0-9a-f]{24}$",
            examples=["507f1f77bcf86cd799439011"],
        )
        return json_schema 