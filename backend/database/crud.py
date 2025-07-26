"""Database CRUD operations"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from database.models import (
    FileUpload, Report, DataQualityAssessment, 
    SystemMetric, SystemAlert, UserSession
)

logger = logging.getLogger(__name__)

class FileUploadCRUD:
    """CRUD operations for file uploads"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> FileUpload:
        """Create a new file upload record"""
        file_upload = FileUpload(**kwargs)
        db.add(file_upload)
        await db.commit()
        await db.refresh(file_upload)
        return file_upload
    
    @staticmethod
    async def get_by_id(db: AsyncSession, file_id: str) -> Optional[FileUpload]:
        """Get file upload by ID"""
        result = await db.execute(
            select(FileUpload)
            .options(selectinload(FileUpload.reports))
            .where(FileUpload.id == file_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 10) -> List[FileUpload]:
        """Get recent file uploads"""
        result = await db.execute(
            select(FileUpload)
            .order_by(desc(FileUpload.upload_time))
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_validation_status(db: AsyncSession, file_id: str, status: str, errors: List[str] = None):
        """Update file validation status"""
        await db.execute(
            update(FileUpload)
            .where(FileUpload.id == file_id)
            .values(
                validation_status=status,
                validation_errors=errors
            )
        )
        await db.commit()

class ReportCRUD:
    """CRUD operations for reports"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Report:
        """Create a new report"""
        report = Report(**kwargs)
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report
    
    @staticmethod
    async def get_by_id(db: AsyncSession, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        result = await db.execute(
            select(Report)
            .options(selectinload(Report.file_upload))
            .where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_file_id(db: AsyncSession, file_id: str) -> List[Report]:
        """Get all reports for a file"""
        result = await db.execute(
            select(Report)
            .where(Report.file_upload_id == file_id)
            .order_by(desc(Report.generated_at))
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 10) -> List[Report]:
        """Get recent reports"""
        result = await db.execute(
            select(Report)
            .options(selectinload(Report.file_upload))
            .where(Report.status == "completed")
            .order_by(desc(Report.generated_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_status(db: AsyncSession, report_id: str, status: str, error_message: str = None):
        """Update report status"""
        values = {"status": status, "updated_at": datetime.utcnow()}
        if error_message:
            values["error_message"] = error_message
        
        await db.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(**values)
        )
        await db.commit()
    
    @staticmethod
    async def update_content(db: AsyncSession, report_id: str, content: str, **kwargs):
        """Update report content and metadata"""
        values = {
            "content": content,
            "status": "completed",
            "updated_at": datetime.utcnow()
        }
        values.update(kwargs)
        
        await db.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(**values)
        )
        await db.commit()

class DataQualityAssessmentCRUD:
    """CRUD operations for data quality assessments"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> DataQualityAssessment:
        """Create a new data quality assessment"""
        assessment = DataQualityAssessment(**kwargs)
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment
    
    @staticmethod
    async def get_by_file_id(db: AsyncSession, file_id: str) -> Optional[DataQualityAssessment]:
        """Get latest data quality assessment for a file"""
        result = await db.execute(
            select(DataQualityAssessment)
            .where(DataQualityAssessment.file_upload_id == file_id)
            .order_by(desc(DataQualityAssessment.assessed_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

class SystemMetricCRUD:
    """CRUD operations for system metrics"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> SystemMetric:
        """Create a new metric record"""
        metric = SystemMetric(**kwargs)
        db.add(metric)
        await db.commit()
        return metric
    
    @staticmethod
    async def get_metrics(db: AsyncSession, metric_name: str = None, 
                         start_time: datetime = None, end_time: datetime = None,
                         limit: int = 1000) -> List[SystemMetric]:
        """Get metrics with optional filtering"""
        query = select(SystemMetric)
        
        conditions = []
        if metric_name:
            conditions.append(SystemMetric.metric_name == metric_name)
        if start_time:
            conditions.append(SystemMetric.timestamp >= start_time)
        if end_time:
            conditions.append(SystemMetric.timestamp <= end_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(SystemMetric.timestamp)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def cleanup_old_metrics(db: AsyncSession, days_to_keep: int = 30):
        """Clean up old metrics to prevent database bloat"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        await db.execute(
            delete(SystemMetric)
            .where(SystemMetric.timestamp < cutoff_date)
        )
        await db.commit()

class SystemAlertCRUD:
    """CRUD operations for system alerts"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> SystemAlert:
        """Create a new alert"""
        alert = SystemAlert(**kwargs)
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    @staticmethod
    async def get_active_alerts(db: AsyncSession, limit: int = 50) -> List[SystemAlert]:
        """Get active alerts"""
        result = await db.execute(
            select(SystemAlert)
            .where(SystemAlert.status == "active")
            .order_by(desc(SystemAlert.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def resolve_alert(db: AsyncSession, alert_id: str, resolved_by: str = "system"):
        """Resolve an alert"""
        await db.execute(
            update(SystemAlert)
            .where(SystemAlert.id == alert_id)
            .values(
                status="resolved",
                resolved_at=datetime.utcnow(),
                resolved_by=resolved_by,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()

class UserSessionCRUD:
    """CRUD operations for user sessions"""
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> UserSession:
        """Create a new user session"""
        session = UserSession(**kwargs)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def get_by_token(db: AsyncSession, session_token: str) -> Optional[UserSession]:
        """Get session by token"""
        result = await db.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_last_accessed(db: AsyncSession, session_token: str):
        """Update session last accessed time"""
        await db.execute(
            update(UserSession)
            .where(UserSession.session_token == session_token)
            .values(last_accessed=datetime.utcnow())
        )
        await db.commit()
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession):
        """Clean up expired sessions"""
        await db.execute(
            delete(UserSession)
            .where(
                or_(
                    UserSession.expires_at < datetime.utcnow(),
                    UserSession.is_active == False
                )
            )
        )
        await db.commit()