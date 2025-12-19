"""
家族数据模型
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Person(BaseModel):
    """人物模型"""
    id: str
    name: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: Optional[str] = None
    description: Optional[str] = None

class Relationship(BaseModel):
    """关系模型"""
    from_person_id: str
    to_person_id: str
    relationship_type: str  # e.g., "parent", "spouse", "sibling"

class FamilyTree(BaseModel):
    """家族树模型"""
    root_person: Person
    persons: List[Person]
    relationships: List[Relationship]

