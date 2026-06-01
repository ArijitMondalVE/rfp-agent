from pydantic import BaseModel
from typing import List, Optional


class Deadline(BaseModel):
    title: str
    date: str
    page: Optional[int] = None


class StaffingRequirement(BaseModel):
    role: str
    experience: Optional[str] = None
    quantity: Optional[int] = None
    page: Optional[int] = None


class PricingTerm(BaseModel):
    pricing_model: Optional[str] = None
    budget: Optional[str] = None
    payment_terms: Optional[str] = None


class ComplianceItem(BaseModel):
    clause: str
    status: str
    risk_level: str
    page: Optional[int] = None


class RFPExtraction(BaseModel):

    client_name: Optional[str] = None

    project_title: Optional[str] = None

    scope_of_work: List[str] = []

    deadlines: List[Deadline] = []

    staffing_requirements: List[StaffingRequirement] = []

    pricing_terms: Optional[PricingTerm] = None

    compliance_items: List[ComplianceItem] = []

    executive_summary: Optional[str] = None

    bid_recommendation: Optional[str] = None