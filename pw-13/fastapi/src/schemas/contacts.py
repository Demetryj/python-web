from datetime import date, datetime

from pydantic import BaseModel, Field, EmailStr, field_validator, field_serializer
from pydantic_extra_types.phone_numbers import PhoneNumber


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=25)
    last_name: str = Field(min_length=3, max_length=25)
    email: EmailStr = Field(max_length=150)
    phone_number: PhoneNumber = Field(
        description="Telephone in international format E.164",
        examples=["+380671234567", "+14155552671"],
    )
    birth_date: date = Field(
        description="Date in DD-MM-YYYY format",
        examples=["20-04-2026"],
    )
    additional_data: str | None = None

    @field_validator("birth_date", mode="before")
    @classmethod
    def parse_birth_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%d-%m-%Y").date()
        return v


class ContactUpdateSchema(BaseModel):
    first_name: str | None = Field(default=None, min_length=3, max_length=25)
    last_name: str | None = Field(default=None, min_length=3, max_length=25)
    email: EmailStr | None = Field(default=None, max_length=150)
    phone_number: PhoneNumber | None = Field(
        default=None,
        description="Telephone in international format E.164",
        examples=["+380671234567", "+14155552671"],
    )
    birth_date: date | None = Field(
        default=None,
        description="Date in DD-MM-YYYY format",
        examples=["20-04-2026"],
    )
    additional_data: str | None = None
   

    @field_validator("birth_date", mode="before")
    @classmethod
    def parse_birth_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%d-%m-%Y").date()
        return v


class ContactPutSchema(ContactSchema):
    pass


class ContactResponse(ContactSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    
    @field_serializer("birth_date")
    def serialize_birth_date(self, value: date) -> str:
        return value.strftime("%d-%m-%Y")

    class Config:
        from_attributes = True
