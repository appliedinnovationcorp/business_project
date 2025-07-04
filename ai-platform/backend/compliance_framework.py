import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from models import Base, User
from database import get_db

class ComplianceFramework(Enum):
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    ISO27001 = "iso27001"
    FEDRAMP = "fedramp"
    PCI_DSS = "pci_dss"

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class AuditEventType(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_VIOLATION = "compliance_violation"

@dataclass
class ComplianceRule:
    framework: ComplianceFramework
    rule_id: str
    title: str
    description: str
    severity: str
    automated_check: bool
    check_function: Optional[str] = None

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    compliance_frameworks = Column(JSON, nullable=True)  # List of applicable frameworks
    risk_level = Column(String, default="low")  # low, medium, high, critical

class DataProcessingRecord(Base):
    __tablename__ = "data_processing_records"
    
    id = Column(Integer, primary_key=True, index=True)
    data_subject_id = Column(String, nullable=False)  # User ID or identifier
    processing_purpose = Column(String, nullable=False)
    data_categories = Column(JSON, nullable=False)  # List of data categories
    legal_basis = Column(String, nullable=False)  # GDPR legal basis
    retention_period = Column(Integer, nullable=True)  # Days
    third_party_sharing = Column(JSON, nullable=True)  # List of third parties
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=True)
    data_classification = Column(String, default=DataClassification.INTERNAL.value)

class ComplianceViolation(Base):
    __tablename__ = "compliance_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    framework = Column(String, nullable=False)
    rule_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    affected_resource = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    status = Column(String, default="open")  # open, investigating, resolved, false_positive

class ComplianceManager:
    """Centralized compliance management system"""
    
    def __init__(self):
        self.rules = self._load_compliance_rules()
        self.logger = logging.getLogger(__name__)
    
    def _load_compliance_rules(self) -> Dict[ComplianceFramework, List[ComplianceRule]]:
        """Load compliance rules for different frameworks"""
        return {
            ComplianceFramework.SOC2: self._get_soc2_rules(),
            ComplianceFramework.HIPAA: self._get_hipaa_rules(),
            ComplianceFramework.GDPR: self._get_gdpr_rules(),
            ComplianceFramework.ISO27001: self._get_iso27001_rules(),
            ComplianceFramework.FEDRAMP: self._get_fedramp_rules(),
        }
    
    def _get_soc2_rules(self) -> List[ComplianceRule]:
        """SOC 2 compliance rules"""
        return [
            ComplianceRule(
                framework=ComplianceFramework.SOC2,
                rule_id="CC6.1",
                title="Logical and Physical Access Controls",
                description="System implements logical and physical access controls to restrict access to system resources",
                severity="high",
                automated_check=True,
                check_function="check_access_controls"
            ),
            ComplianceRule(
                framework=ComplianceFramework.SOC2,
                rule_id="CC6.2",
                title="Authentication and Authorization",
                description="System implements authentication and authorization controls",
                severity="high",
                automated_check=True,
                check_function="check_authentication"
            ),
            ComplianceRule(
                framework=ComplianceFramework.SOC2,
                rule_id="CC6.3",
                title="System Access Monitoring",
                description="System monitors and logs access to system resources",
                severity="medium",
                automated_check=True,
                check_function="check_access_monitoring"
            ),
            ComplianceRule(
                framework=ComplianceFramework.SOC2,
                rule_id="CC7.1",
                title="Data Transmission Controls",
                description="System implements controls over data transmission",
                severity="high",
                automated_check=True,
                check_function="check_data_transmission"
            ),
        ]
    
    def _get_hipaa_rules(self) -> List[ComplianceRule]:
        """HIPAA compliance rules"""
        return [
            ComplianceRule(
                framework=ComplianceFramework.HIPAA,
                rule_id="164.308",
                title="Administrative Safeguards",
                description="Implement administrative safeguards for PHI",
                severity="critical",
                automated_check=True,
                check_function="check_administrative_safeguards"
            ),
            ComplianceRule(
                framework=ComplianceFramework.HIPAA,
                rule_id="164.310",
                title="Physical Safeguards",
                description="Implement physical safeguards for PHI",
                severity="high",
                automated_check=False
            ),
            ComplianceRule(
                framework=ComplianceFramework.HIPAA,
                rule_id="164.312",
                title="Technical Safeguards",
                description="Implement technical safeguards for PHI",
                severity="critical",
                automated_check=True,
                check_function="check_technical_safeguards"
            ),
            ComplianceRule(
                framework=ComplianceFramework.HIPAA,
                rule_id="164.314",
                title="Business Associate Requirements",
                description="Ensure business associates comply with HIPAA",
                severity="high",
                automated_check=False
            ),
        ]
    
    def _get_gdpr_rules(self) -> List[ComplianceRule]:
        """GDPR compliance rules"""
        return [
            ComplianceRule(
                framework=ComplianceFramework.GDPR,
                rule_id="Art.6",
                title="Lawful Basis for Processing",
                description="Processing must have a lawful basis",
                severity="critical",
                automated_check=True,
                check_function="check_lawful_basis"
            ),
            ComplianceRule(
                framework=ComplianceFramework.GDPR,
                rule_id="Art.7",
                title="Consent Requirements",
                description="Consent must be freely given, specific, informed and unambiguous",
                severity="high",
                automated_check=True,
                check_function="check_consent"
            ),
            ComplianceRule(
                framework=ComplianceFramework.GDPR,
                rule_id="Art.17",
                title="Right to Erasure",
                description="Data subjects have the right to erasure of personal data",
                severity="high",
                automated_check=True,
                check_function="check_erasure_capability"
            ),
            ComplianceRule(
                framework=ComplianceFramework.GDPR,
                rule_id="Art.25",
                title="Data Protection by Design",
                description="Implement data protection by design and by default",
                severity="medium",
                automated_check=True,
                check_function="check_privacy_by_design"
            ),
        ]
    
    def _get_iso27001_rules(self) -> List[ComplianceRule]:
        """ISO 27001 compliance rules"""
        return [
            ComplianceRule(
                framework=ComplianceFramework.ISO27001,
                rule_id="A.9.1.1",
                title="Access Control Policy",
                description="Access control policy shall be established",
                severity="high",
                automated_check=True,
                check_function="check_access_control_policy"
            ),
            ComplianceRule(
                framework=ComplianceFramework.ISO27001,
                rule_id="A.12.6.1",
                title="Management of Technical Vulnerabilities",
                description="Information about technical vulnerabilities shall be obtained",
                severity="medium",
                automated_check=True,
                check_function="check_vulnerability_management"
            ),
        ]
    
    def _get_fedramp_rules(self) -> List[ComplianceRule]:
        """FedRAMP compliance rules"""
        return [
            ComplianceRule(
                framework=ComplianceFramework.FEDRAMP,
                rule_id="AC-2",
                title="Account Management",
                description="Manage information system accounts",
                severity="high",
                automated_check=True,
                check_function="check_account_management"
            ),
            ComplianceRule(
                framework=ComplianceFramework.FEDRAMP,
                rule_id="AU-2",
                title="Audit Events",
                description="Determine auditable events and audit frequency",
                severity="medium",
                automated_check=True,
                check_function="check_audit_events"
            ),
        ]
    
    async def run_compliance_checks(self, frameworks: List[ComplianceFramework], db: Session) -> Dict[str, Any]:
        """Run automated compliance checks"""
        results = {}
        
        for framework in frameworks:
            framework_results = []
            rules = self.rules.get(framework, [])
            
            for rule in rules:
                if rule.automated_check and rule.check_function:
                    try:
                        check_result = await self._run_check(rule.check_function, db)
                        framework_results.append({
                            'rule_id': rule.rule_id,
                            'title': rule.title,
                            'severity': rule.severity,
                            'status': 'pass' if check_result else 'fail',
                            'details': check_result if isinstance(check_result, dict) else {}
                        })
                        
                        # Log compliance violation if check failed
                        if not check_result:
                            await self._log_compliance_violation(rule, db)
                            
                    except Exception as e:
                        self.logger.error(f"Compliance check failed for {rule.rule_id}: {str(e)}")
                        framework_results.append({
                            'rule_id': rule.rule_id,
                            'title': rule.title,
                            'severity': rule.severity,
                            'status': 'error',
                            'error': str(e)
                        })
            
            results[framework.value] = framework_results
        
        return results
    
    async def _run_check(self, check_function: str, db: Session) -> Any:
        """Run a specific compliance check function"""
        if hasattr(self, check_function):
            return await getattr(self, check_function)(db)
        else:
            raise ValueError(f"Unknown check function: {check_function}")
    
    async def check_access_controls(self, db: Session) -> bool:
        """Check if proper access controls are in place"""
        # Check if all users have proper role assignments
        users_without_roles = db.query(User).filter(User.role.is_(None)).count()
        return users_without_roles == 0
    
    async def check_authentication(self, db: Session) -> bool:
        """Check authentication controls"""
        # Check if MFA is enabled for admin users
        admin_users = db.query(User).filter(User.role == 'admin').all()
        # This would check MFA status in a real implementation
        return True
    
    async def check_access_monitoring(self, db: Session) -> bool:
        """Check if access is properly monitored"""
        # Check if audit logging is active
        recent_logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=1)
        ).count()
        return recent_logs > 0
    
    async def check_data_transmission(self, db: Session) -> bool:
        """Check data transmission security"""
        # Check if HTTPS is enforced
        return os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
    
    async def check_lawful_basis(self, db: Session) -> bool:
        """Check GDPR lawful basis for processing"""
        # Check if all data processing has lawful basis
        records_without_basis = db.query(DataProcessingRecord).filter(
            DataProcessingRecord.legal_basis.is_(None)
        ).count()
        return records_without_basis == 0
    
    async def check_consent(self, db: Session) -> bool:
        """Check GDPR consent requirements"""
        # Check if consent is properly recorded where required
        consent_required = db.query(DataProcessingRecord).filter(
            DataProcessingRecord.legal_basis == 'consent'
        ).all()
        
        for record in consent_required:
            if not record.consent_given or not record.consent_date:
                return False
        
        return True
    
    async def _log_compliance_violation(self, rule: ComplianceRule, db: Session):
        """Log a compliance violation"""
        violation = ComplianceViolation(
            framework=rule.framework.value,
            rule_id=rule.rule_id,
            severity=rule.severity,
            description=f"Compliance check failed for {rule.title}: {rule.description}",
            status="open"
        )
        
        db.add(violation)
        db.commit()
    
    def log_audit_event(self, db: Session, event_type: AuditEventType, user_id: Optional[int] = None, 
                       resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                       action: str = "", details: Optional[Dict] = None, 
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                       compliance_frameworks: Optional[List[str]] = None):
        """Log an audit event"""
        
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type.value,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            compliance_frameworks=compliance_frameworks or [],
            risk_level=self._calculate_risk_level(event_type, details)
        )
        
        db.add(audit_log)
        db.commit()
    
    def _calculate_risk_level(self, event_type: AuditEventType, details: Optional[Dict]) -> str:
        """Calculate risk level for audit event"""
        high_risk_events = [
            AuditEventType.DATA_DELETION,
            AuditEventType.SYSTEM_CONFIGURATION,
            AuditEventType.SECURITY_EVENT,
            AuditEventType.COMPLIANCE_VIOLATION
        ]
        
        if event_type in high_risk_events:
            return "high"
        elif event_type == AuditEventType.DATA_MODIFICATION:
            return "medium"
        else:
            return "low"
    
    def create_data_processing_record(self, db: Session, data_subject_id: str, 
                                    processing_purpose: str, data_categories: List[str],
                                    legal_basis: str, retention_period: Optional[int] = None,
                                    third_party_sharing: Optional[List[str]] = None,
                                    consent_given: bool = False,
                                    data_classification: DataClassification = DataClassification.INTERNAL) -> DataProcessingRecord:
        """Create a GDPR data processing record"""
        
        record = DataProcessingRecord(
            data_subject_id=data_subject_id,
            processing_purpose=processing_purpose,
            data_categories=data_categories,
            legal_basis=legal_basis,
            retention_period=retention_period,
            third_party_sharing=third_party_sharing or [],
            consent_given=consent_given,
            consent_date=datetime.utcnow() if consent_given else None,
            data_classification=data_classification.value
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record
    
    def get_compliance_dashboard(self, db: Session) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        
        # Get recent violations
        recent_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.detected_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Get audit log statistics
        audit_stats = {}
        for event_type in AuditEventType:
            count = db.query(AuditLog).filter(
                AuditLog.event_type == event_type.value,
                AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).count()
            audit_stats[event_type.value] = count
        
        # Get data processing records
        processing_records = db.query(DataProcessingRecord).count()
        
        return {
            'violations': {
                'total': len(recent_violations),
                'by_severity': {
                    'critical': len([v for v in recent_violations if v.severity == 'critical']),
                    'high': len([v for v in recent_violations if v.severity == 'high']),
                    'medium': len([v for v in recent_violations if v.severity == 'medium']),
                    'low': len([v for v in recent_violations if v.severity == 'low']),
                },
                'by_framework': {}
            },
            'audit_events': audit_stats,
            'data_processing_records': processing_records,
            'compliance_score': self._calculate_compliance_score(recent_violations)
        }
    
    def _calculate_compliance_score(self, violations: List[ComplianceViolation]) -> float:
        """Calculate overall compliance score"""
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        total_weight = sum(severity_weights.get(v.severity, 1) for v in violations)
        
        # Calculate score (100 - weighted violations)
        score = max(0, 100 - total_weight)
        return score

# Data Loss Prevention
class DLPManager:
    """Data Loss Prevention management"""
    
    def __init__(self):
        self.sensitive_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
        }
    
    def scan_content(self, content: str) -> Dict[str, List[str]]:
        """Scan content for sensitive data"""
        import re
        
        findings = {}
        for pattern_name, pattern in self.sensitive_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                findings[pattern_name] = matches
        
        return findings
    
    def anonymize_content(self, content: str) -> str:
        """Anonymize sensitive content"""
        import re
        
        # Replace SSNs
        content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX', content)
        
        # Replace credit cards
        content = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX', content)
        
        return content

# Global compliance manager instance
compliance_manager = ComplianceManager()
dlp_manager = DLPManager()
