# backend/app/schemas/lookups.py
"""Pydantic schemas for lookup tables used in the Songs domain.
These are simple reference entities shared across the application.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional

# Base schema with common config
class LookupBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)

# Instrument
class InstrumentBase(LookupBase):
    id: int
    name: str

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentUpdate(BaseModel):
    name: Optional[str] = None

class InstrumentSummary(InstrumentBase):
    pass

class InstrumentDetail(InstrumentBase):
    description: Optional[str] = None

# Genre
class GenreBase(LookupBase):
    id: int
    name: str

class GenreCreate(GenreBase):
    pass

class GenreUpdate(BaseModel):
    name: Optional[str] = None

class GenreSummary(GenreBase):
    pass

class GenreDetail(GenreBase):
    description: Optional[str] = None

# Language
class LanguageBase(LookupBase):
    id: int
    name: str

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(BaseModel):
    name: Optional[str] = None

class LanguageSummary(LanguageBase):
    pass

class LanguageDetail(LanguageBase):
    iso_code: Optional[str] = None

# Technique
class TechniqueBase(LookupBase):
    id: int
    name: str

class TechniqueCreate(TechniqueBase):
    pass

class TechniqueUpdate(BaseModel):
    name: Optional[str] = None

class TechniqueSummary(TechniqueBase):
    pass

class TechniqueDetail(TechniqueBase):
    description: Optional[str] = None

# Articulation
class ArticulationBase(LookupBase):
    id: int
    name: str

class ArticulationCreate(ArticulationBase):
    pass

class ArticulationUpdate(BaseModel):
    name: Optional[str] = None

class ArticulationSummary(ArticulationBase):
    pass

class ArticulationDetail(ArticulationBase):
    description: Optional[str] = None

# DynamicMarking
class DynamicMarkingBase(LookupBase):
    id: int
    name: str

class DynamicMarkingCreate(DynamicMarkingBase):
    pass

class DynamicMarkingUpdate(BaseModel):
    name: Optional[str] = None

class DynamicMarkingSummary(DynamicMarkingBase):
    pass

class DynamicMarkingDetail(DynamicMarkingBase):
    description: Optional[str] = None

# ErrorType
class ErrorTypeBase(LookupBase):
    id: int
    name: str

class ErrorTypeCreate(ErrorTypeBase):
    pass

class ErrorTypeUpdate(BaseModel):
    name: Optional[str] = None

class ErrorTypeSummary(ErrorTypeBase):
    pass

class ErrorTypeDetail(ErrorTypeBase):
    description: Optional[str] = None

# Skill
class SkillBase(LookupBase):
    id: int
    name: str

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None

class SkillSummary(SkillBase):
    pass

class SkillDetail(SkillBase):
    description: Optional[str] = None
