from pydantic import BaseModel
from typing import List, Optional, Any

class QualificationSchema(BaseModel):
    name: str
    issuer: str
    valid_until: str

class ProjectCaseSchema(BaseModel):
    name: str
    amount: str
    tags: List[str]

class EnterpriseProfileBase(BaseModel):
    company_name: str
    unified_social_credit_code: str
    legal_representative: str
    registered_capital: str
    establishment_date: str
    qualifications: List[QualificationSchema] = []
    project_cases: List[ProjectCaseSchema] = []

class EnterpriseProfileCreate(EnterpriseProfileBase):
    pass

class EnterpriseProfileResp(EnterpriseProfileBase):
    id: int
    class Config:
        from_attributes = True

class TrustScoreResp(BaseModel):
    score: float
    identity_verified: bool
    compliance_status: str
    financial_health: str
    ai_insights: List[dict]
