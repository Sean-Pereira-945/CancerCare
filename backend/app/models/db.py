from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    cancer_type = Column(String(255))
    role = Column(String(50), default="patient")
    created_at = Column(DateTime, default=datetime.utcnow)

class DietPlan(Base):
    __tablename__ = "diet_plans"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    plan_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    date = Column(DateTime, nullable=False)
    meal_type = Column(String(50))
    adhered_to_plan = Column(Boolean, default=True)

class Medication(Base):
    __tablename__ = "medications"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    dosage = Column(String(255))
    frequency = Column(String(255))
    times = Column(JSON) # Stored as JSON for SQLite compatibility
    notes = Column(Text)
    active = Column(Boolean, default=True)

class MedicationLog(Base):
    __tablename__ = "medication_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    medication_id = Column(String(36), ForeignKey("medications.id"))
    status = Column(String(50), default="taken")
    taken_at = Column(DateTime, default=datetime.utcnow)

class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    symptoms = Column(JSON)
    mood = Column(String(255))
    notes = Column(Text)
    logged_at = Column(DateTime, default=datetime.utcnow)

class CaregiverPatient(Base):
    __tablename__ = "caregiver_patients"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    caregiver_id = Column(String(36), ForeignKey("users.id"))
    patient_id = Column(String(36), ForeignKey("users.id"))
    linked_at = Column(DateTime, default=datetime.utcnow)
