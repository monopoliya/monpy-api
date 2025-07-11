from pydantic import BaseModel, ConfigDict

__all__ = (
    'Model'
)


class Model(BaseModel):
    model_config = ConfigDict(
        extra='ignore', from_attributes=True
    )

    def __str__(self) -> str:
        return self.model_dump_json(indent=2)

    def to_dict(self, **kwargs) -> dict:
        return self.model_dump(mode='json' **kwargs)
