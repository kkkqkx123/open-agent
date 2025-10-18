The function "validator" is deprecated
  Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more detailsPylance
(function) def validator(
    __field: str,
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool | None = None,
    allow_reuse: bool = False
) -> (_V1ValidatorType@validator) -> _V1ValidatorType@validator

src\config\models\agent_config.py