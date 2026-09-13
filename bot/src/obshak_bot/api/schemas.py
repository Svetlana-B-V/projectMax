from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Базовая модель ответов бэкенда: поля в JSON — camelCase, в Python — snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


class UserDto(ApiModel):
    id: str
    name: str
    email: str | None = None
    telegram_id: int | None = None


class AuthResult(ApiModel):
    user: UserDto
    access_token: str


class GroupDto(ApiModel):
    id: str
    name: str
    currency: str = "RUB"
    invite_code: str
    owner_id: str


class MemberUserDto(ApiModel):
    id: str
    name: str


class GroupMemberDto(ApiModel):
    user_id: str
    role: str
    user: MemberUserDto = Field(alias="User")


class CategoryDto(ApiModel):
    id: str
    name: str
    icon: str | None = None
    group_id: str | None = None


class SavingsGoalDto(ApiModel):
    id: str
    name: str
    type: str
    target_amount: Decimal
    current_amount: Decimal
    status: str


class SplitInput(ApiModel):
    user_id: str
    amount_owed: float


class ExpenseCreate(ApiModel):
    """Тело POST /api/expenses. Суммы — числа, как требует zod-схема бэкенда."""

    group_id: str
    payer_id: str
    amount: float
    splits: list[SplitInput]
    category_id: str | None = None
    description: str | None = None


class DebtUserDto(ApiModel):
    id: str
    name: str
    telegram_id: int | None = None


class DebtDto(ApiModel):
    """Долг fromUser → toUser. Вложенные пользователи есть только в списках, не в ответе pay."""

    id: str
    group_id: str
    from_user_id: str
    to_user_id: str
    amount: Decimal
    status: str
    from_user: DebtUserDto | None = None
    to_user: DebtUserDto | None = None


class AchievementDto(ApiModel):
    code: str
    name: str
    description: str
    icon: str | None = None
    earned_at: str | None = None


class ReminderSettingsDto(ApiModel):
    style: str  # soft | neutral | playful
    enabled: bool
    last_reminded_at: str | None = None


class RecognizedReceiptDto(ApiModel):
    """Ответ POST /api/expenses/receipt. Для расхода берём только amount."""

    amount: Decimal
    date: str | None = None
    category: str | None = None
    description: str | None = None


class ExpenseDto(ApiModel):
    id: str
    group_id: str
    payer_id: str
    amount: Decimal
    category_id: str | None = None
    description: str | None = None
