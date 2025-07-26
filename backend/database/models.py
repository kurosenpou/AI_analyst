"""SQLAlchemy database models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
import uuid

class FileUpload(Base):
    """File upload records"""
    __tablename__ = "file_uploads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    parsed_data_preview = Column(JSON, nullable=True)
    validation_status = Column(String(20), default="pending")  # pending, valid, invalid
    validation_errors = Column(JSON, nullable=True)
    file_metadata = Column(JSON, nullable=True)  # Additional file metadata
    
    # Relationships
    reports = relationship("Report", back_populates="file_upload", cascade="all, delete-orphan")
    data_quality_assessments = relationship("DataQualityAssessment", back_populates="file_upload", cascade="all, delete-orphan")

class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_upload_id = Column(String, ForeignKey("file_uploads.id"), nullable=False)
    report_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    financial_highlights = Column(JSON, nullable=True)
    insights = Column(JSON, nullable=True)  # List of BusinessInsight objects
    report_metadata = Column(JSON, nullable=True)  # Additional report metadata  # Additional file metadata
    
    # Analysis settings
    analysis_depth = Column(String(20), default="standard")  # quick, standard, comprehensive
    focus_areas = Column(JSON, nullable=True)  # List of focus areas
    additional_context = Column(Text, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    data_quality_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    confidence_metrics = Column(JSON, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    status = Column(String(20), default="generating")  # generating, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="reports")

class DataQualityAssessment(Base):
    """Data quality assessment records"""
    __tablename__ = "data_quality_assessments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_upload_id = Column(String, ForeignKey("file_uploads.id"), nullable=False)
    
    # Quality scores (0.0 to 1.0)
    completeness_score = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)
    timeliness_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    
    # Issues and recommendations
    issues_found = Column(JSON, nullable=True)  # List of issues
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    
    # Assessment metadata
    assessment_method = Column(String(50), default="automated")
    assessed_at = Column(DateTime(timezone=True), server_default=func.now())
    assessment_duration = Column(Float, nullable=True)  # seconds
    assessment_metadata = Column(JSON, nullable=True)  # Additional assessment metadata
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="data_quality_assessments")

class SystemMetric(Base):
    """System monitoring metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(20), default="counter")  # counter, gauge, histogram
    tags = Column(JSON, nullable=True)  # Key-value pairs for metric tags
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metric_metadata = Column(JSON, nullable=True)  # Additional metric metadata
    
    # Indexes for efficient querying
    __table_args__ = (
        {"sqlite_autoincrement": True}
    )

class SystemAlert(Base):
    """System alerts and notifications"""
    __tablename__ = "system_alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), nullable=False)  # info, warning, error, critical
    source = Column(String(100), nullable=False)
    alert_type = Column(String(50), default="system")
    
    # Alert status
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # Metadata
    alert_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserSession(Base):
    """Simple user session management"""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_token = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(100), nullable=False, default="anonymous")
    user_type = Column(String(20), default="user")  # admin, user
    
    # Session data
    session_data = Column(JSON, nullable=True)
    session_metadata = Column(JSON, nullable=True)  # Additional session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)